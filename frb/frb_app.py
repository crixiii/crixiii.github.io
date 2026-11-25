import json
import sys

import numpy as np

sys.path.insert(0, "/home/pyodide")

from frbbeaming import Config, IsotropicBeam, RelativisticBeam, Simulation
from frbbeaming.analysis import bimodality
from frbbeaming.numerics import LN10


XLIM = (33.0, 43.0) #need to update for flexible xlims? place under  graph
_beams = {}
_cache = {}

def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer, np.bool_)):
        return o.item()
    return o


def _out(o):
    return json.dumps(_clean(o))


def _cfg(p):
    return Config(theta_p=p["theta_p"], gamma_p=p["gamma_p"], sigma=p["sigma"], zeta=p["zeta"],
                  lognorm_shape=p["lognorm_shape"], pl_index=p["pl_index"],
                  bpl_alpha1=p["bpl_alpha1"], bpl_alpha2=p["bpl_alpha2"], bpl_break=10.0 ** p["bpl_break_log"])
def _key(label, p):
    return (label,) + {
        "Isotropic": (),
        "Gaussian": (p["sigma"],),
        "Gaussian & Plateau": (p["sigma"], p["theta_p"]),
        "Relativistic": (p["gamma_p"],),
        "R-PL": (p["gamma_p"], p["theta_p"], p["zeta"]),
        "R-G": (p["gamma_p"], p["theta_p"]),
    }[label]


def _setup(p):
    """Builds the simulation and reuses tabulated relativistic beams across calls."""
    cfg = _cfg(p)
    sim = Simulation(cfg)
    label = p["beam"]
    key = _key(label, p)
    if key not in _beams:
        if len(_beams) > 30:
            _beams.clear()
        _beams[key] = sim.beams[label]
    sim.beams[label] = _beams[key]
    return cfg, sim, _beams[key], sim.dists[p["dist"]]


def _cut(cfg, beam):
    return float(np.log10(cfg.e0 * max(beam.g_cut(cfg.r_max), 1e-300)))


def _thin(a, n=1000):
    return a[::int(np.ceil(len(a) / n))]


def _pdf(p):
    cfg, sim, beam, dist = _setup(p)
    e0 = cfg.e0
    base = dict(cut=_cut(cfg, beam), e0=float(np.log10(e0)), edge=beam.edge)
    if p["dist"] == "single":
        if isinstance(beam, IsotropicBeam):
            return dict(base, kind="delta")
        x, dens, mass = beam.single_energy_pdf(e0)
        x, y = _thin(x), _thin(dens * LN10)
        x = np.concatenate([x, [np.log10(e0), XLIM[1] + 1]])
        y = np.concatenate([y, [0.0, 0.0]])
        if x[0] > XLIM[0]:
            x = np.concatenate([[XLIM[0] - 1, x[0]], x])
            y = np.concatenate([[0.0, 0.0], y])
        return dict(base, kind="curve", x=x, y=y, mass=float(mass))
    if isinstance(beam, RelativisticBeam):
        grid = np.unique(np.concatenate([np.geomspace(1e31, 10.0**43.5, 350),
                                         e0 * np.geomspace(10.0**-1.5, 10.0**1.5, 250)]))
    else:
        grid = beam.default_grid(cfg)
    p_ln = beam.observed_pdf_ln(dist, grid)
    out = dict(base, kind="curve", x=np.log10(grid), y=p_ln * LN10)
    if isinstance(beam, RelativisticBeam):
        out["total"] = float(beam.total_probability(dist, grid, p_ln))
    return out


def compute_pdf(pjson):
    p = json.loads(pjson)
    key = ("pdf", pjson)
    if key not in _cache:
        _cache[key] = _out(_pdf(p))
    return _cache[key]


def compute_profile(pjson):
    p = json.loads(pjson)
    cfg, sim, beam, dist = _setup(p)
    theta = np.linspace(0, np.pi, 600)
    em = beam.emitted_profile(theta)
    return _out(dict(theta=theta, g=np.maximum(beam.g(theta), 1e-300),
                     emitted=None if em is None else np.maximum(em, 1e-300), edge=beam.edge))


def compute_hist(pjson):
    p = json.loads(pjson)
    cfg, sim, beam, dist = _setup(p)
    n = int(p["n_sim"])
    log_e = np.log10(np.maximum(beam.sample(dist, np.random.default_rng(int(p["seed"])), n), 1e-300))
    bins = np.linspace(XLIM[0], XLIM[1], 111)
    counts, _ = np.histogram(log_e, bins=bins)
    return _out(dict(edges=bins, density=counts / n / np.diff(bins), n=n, below=float(np.mean(log_e < XLIM[0])),
                     cut=_cut(cfg, beam), e0=float(np.log10(cfg.e0))))


def compute_bimodality(pjson):
    p = json.loads(pjson)
    cfg, sim, beam, dist = _setup(p)
    n = int(min(p["n_sim"], 30_000))
    rng = np.random.default_rng(int(p["seed"]))
    log_e = sim.observed_log_energies(beam, dist, n, rng)
    if len(log_e) < 100 or np.ptp(log_e) == 0:
        return _out(dict(degenerate=True))
    log_e = log_e + rng.normal(0, 0.01, len(log_e))
    r = bimodality(log_e, seed=int(p["seed"]), use_dip=False)
    lo, hi = float(log_e.min()), float(log_e.max())
    bins = np.linspace(lo, hi, 61)
    counts, _ = np.histogram(log_e, bins=bins)
    x = np.linspace(lo, hi, 300)
    comps = [dict(x=x, y=w / (s * np.sqrt(2 * np.pi)) * np.exp(-((x - m) ** 2) / (2 * s**2)))
             for m, s, w in zip(r["means"], r["stds"], r["weights"])]
    return _out(dict(degenerate=False, result=r, n=len(log_e), edges=bins, density=counts / len(log_e) / np.diff(bins),
                     components=comps))
