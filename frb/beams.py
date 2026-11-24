from dataclasses import dataclass
from functools import cached_property

import numpy as np
from scipy import integrate, interpolate, optimize

from .distributions import SingleEnergy
from .numerics import LN10, gauss_panels, integrate_theta, sample_theta, trapz


class Beam:
    """g(theta) = E_obs / E is the beam strength at observer angle theta."""

    label = "beam"
    edge = None

    def g(self, theta):
        raise NotImplementedError

    def observed_pdf_ln(self, dist, e_grid):
        raise NotImplementedError

    def single_energy_pdf(self, e0):
        """Returns (log10 E_obs, density per ln E, plateau point mass) for one intrinsic energy."""
        raise NotImplementedError

    def emitted_profile(self, theta):
        return None

    def default_grid(self, cfg):
        return np.geomspace(10.0 ** (cfg.xlim[0] - 1), 10.0 ** (cfg.xlim[1] + 0.5), 1500)

    def theta_nodes(self):
        return np.linspace(0, np.pi, 20001)

    def g_cut(self, r_max):
        return float(self.g(np.array([r_max]))[0])

    def sample(self, dist, rng, n):
        return dist.sample(rng, n) * self.g(sample_theta(rng, n))

    def tail_probability(self, dist, e_max):
        th = self.theta_nodes()
        with np.errstate(divide="ignore", over="ignore"):
            integrand = np.sin(th) / 2 * dist.sf(e_max / self.g(th))
        return trapz(integrand, th)

    def total_probability(self, dist, e_grid, p_ln):
        return trapz(p_ln, np.log(e_grid)) + self.tail_probability(dist, e_grid[-1])

    def grid_for(self, dist, n):
        lo, hi = dist.e_range()
        return np.geomspace(lo * float(self.g(np.pi)) * dist.scale, hi * dist.scale, n)


class IsotropicBeam(Beam):
    label = "Isotropic"

    def g(self, theta):
        return np.ones_like(np.asarray(theta, float))

    def observed_pdf_ln(self, dist, e_grid):
        return dist.pdf_ln(np.log(e_grid))

    def single_energy_pdf(self, e0):
        raise TypeError("isotropic + single energy is a delta function")


class GaussianBeam(Beam):
    """g = exp(-max(|theta| - theta_p, 0)**2 / (2 sigma**2)); theta_p > 0 adds a plateau."""

    def __init__(self, sigma, theta_p=0.0):
        self.sigma, self.theta_p = sigma, theta_p
        self.label = "Gaussian & Plateau" if theta_p > 0 else "Gaussian"
        self.edge = theta_p if theta_p > 0 else None

    def g(self, theta):
        d = np.clip(np.abs(theta) - self.theta_p, 0, None)
        return np.exp(-d**2 / (2 * self.sigma**2))

    def observed_pdf_ln(self, dist, e_grid, n_theta=8001, chunk=200):
        if isinstance(dist, SingleEnergy):
            raise TypeError("use single_energy_pdf for a single intrinsic energy")
        th = np.linspace(0, np.pi, n_theta)
        w = np.sin(th) / 2
        b = self.g(th)
        components = dist.powerlaw_components() if hasattr(dist, "powerlaw_components") else None
        if components:
            e0 = dist.scale
            th_low = np.where(e_grid < e0,
                              self.theta_p + self.sigma * np.sqrt(2 * np.maximum(np.log(e0 / e_grid), 0)), 0.0)
            out = np.zeros_like(e_grid, dtype=float)
            for weight, a in components:
                f = w * b**a
                c = np.concatenate([[0], np.cumsum(0.5 * (f[1:] + f[:-1]) * np.diff(th))])
                out += weight * a * (e_grid / e0) ** -a * (c[-1] - np.interp(th_low, th, c))
            return out
        ln_e, ln_b = np.log(e_grid), np.log(b)
        out = np.empty_like(ln_e)
        for i in range(0, len(ln_e), chunk):
            x = ln_e[i:i + chunk, None] - ln_b[None, :]
            out[i:i + chunk] = trapz(w[None, :] * dist.pdf_ln(x), th, axis=1)
        return out

    def single_energy_pdf(self, e0):
        x = np.linspace(-25.0, 0.0, 4000)[:-1]
        th = self.theta_p + self.sigma * np.sqrt(-2 * x)
        density = self.sigma * np.sin(np.minimum(th, np.pi)) / (2 * np.sqrt(-2 * x))
        mass = (1 - np.cos(self.theta_p)) / 2
        return np.log10(e0) + x / LN10, density, mass


@dataclass
class BeamTable:
    ln_g: object
    theta_of_lng: object
    dtheta_dlng: object
    theta_max: float
    lng_min: float
    lng_max: float
    theta: np.ndarray
    g: np.ndarray
    breaks: np.ndarray


class RelativisticBeam(Beam):
    """Jet beam integrated over its angular structure (Beniamini 2019).

    kind "Relativistic": point source with Lorentz factor gamma_p.
    kind "RPL": plateau of radius r_p with power-law wings (r/r_p)**-zeta.
    kind "RG": Gaussian structure exp(-(r/r_p)**2).
    """

    _LABELS = {"Relativistic": "Relativistic", "RPL": "R-PL", "RG": "R-G"}

    def __init__(self, kind="RPL", gamma_p=300.0, r_p=0.3, zeta=1.7, theta_b_max=np.pi / 2,
                 n_gauss=24, lng_step=0.1, label=None):
        if kind not in self._LABELS:
            raise ValueError(f"kind must be one of {list(self._LABELS)}")
        self.kind, self.gamma_p, self.r_p, self.zeta = kind, gamma_p, r_p, zeta
        self.theta_b_max, self.n_gauss, self.lng_step = theta_b_max, n_gauss, lng_step
        self.label = label or self._LABELS[kind]
        self.edge = r_p if kind in ("RPL", "RG") else None

    @classmethod
    def from_config(cls, kind, cfg, **kw):
        r_p = 1 / cfg.gamma_p if kind == "Relativistic" else cfg.theta_p
        return cls(kind, cfg.gamma_p, r_p, cfg.zeta, cfg.theta_b_max, cfg.n_gauss, cfg.lng_step, **kw)

    def profile(self, r):
        if self.kind == "RG":
            return np.exp(-(r / self.r_p) ** 2)
        return (np.maximum(r, self.r_p) / self.r_p) ** -self.zeta

    def lorentz(self, r):
        return 1 + (self.gamma_p - 1) * self.profile(r)

    def emitted_profile(self, theta):
        return self.profile(theta) if self.kind in ("RPL", "RG") else None

    @staticmethod
    def _one_minus_beta_cos(x, beta, gamma):
        return 1 / (gamma**2 * (1 + beta)) + 2 * beta * np.sin(x / 2) ** 2

    def _integrand(self, theta_b, theta):
        gamma = self.lorentz(theta_b)
        beta = np.sqrt(1 - 1 / gamma**2)
        a = 1 - beta * np.cos(theta) * np.cos(theta_b)
        c = beta * np.sin(theta) * np.sin(theta_b)
        omc = self._one_minus_beta_cos
        a2_minus_c2 = omc(theta - theta_b, beta, gamma) * omc(theta + theta_b, beta, gamma)
        phi_integral = np.pi * (2 * a**2 + c**2) / a2_minus_c2**2.5
        return np.sin(theta_b) * self.profile(theta_b) / gamma**4 * phi_integral

    def beam_function(self, theta):
        """g(theta) by direct integration over the jet structure; slow, used to build the table."""
        if self.kind == "Relativistic":
            gamma = self.gamma_p
            beta = np.sqrt(1 - 1 / gamma**2)
            return (1 / (gamma**2 * (1 + beta))) / self._one_minus_beta_cos(theta, beta, gamma)
        width = 1 / self.lorentz(min(theta, self.theta_b_max))
        hints = [theta, self.r_p, theta - width, theta + width, theta - 10 * width, theta + 10 * width]
        hints = sorted({h for h in hints if 1e-9 < h < self.theta_b_max - 1e-9})
        value, _ = integrate.quad(self._integrand, 0, self.theta_b_max, args=(theta,),
                                  points=hints or None, limit=500, epsabs=0, epsrel=1e-10)
        return value / (4 * np.pi)

    def beam_function_fast(self, theta, order=16):
        """Same integral as beam_function with vectorised Gauss-Legendre panels, much faster than quad.
        Panel edges cluster around theta, the plateau/core edge and the width 1/Gamma of the beaming cone."""
        if self.kind == "Relativistic":
            return self.beam_function(theta)
        width = 1 / self.lorentz(min(theta, self.theta_b_max))
        scales = np.array([0.1, 0.3, 1, 3, 10, 30, 100, 300])
        core = self.r_p * np.array([0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8])
        pts = np.concatenate([[0, self.theta_b_max, self.r_p, theta], theta - width * scales, theta + width * scales,
                              core, np.linspace(0, self.theta_b_max, 65)])
        edges = np.unique(np.clip(pts, 0, self.theta_b_max))
        x, w = gauss_panels(edges, order)
        return np.sum(w * self._integrand(x, theta)) / (4 * np.pi)

    def _theta_grid(self):
        uniform = np.linspace(0, np.pi, 1500)
        near_edge = self.r_p + np.concatenate([-np.logspace(-4, -0.7, 150)[::-1], [0], np.logspace(-4, -0.3, 400)])
        return np.unique(np.clip(np.concatenate([uniform, near_edge]), 1e-6, np.pi))

    def _plateau_breaks(self):
        offsets = np.array([-0.3, -0.1, -0.03, -0.01, -0.003, -0.001, 0, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0])
        return np.unique(np.clip(self.r_p + offsets, 0, np.pi))

    @cached_property
    def table(self):
        theta = self._theta_grid()
        g = np.array([self.beam_function_fast(t) for t in theta])
        i_max = np.argmax(g)
        ln_g_fall, theta_fall = np.log(g[i_max:]), theta[i_max:]
        falling = np.concatenate([[True], np.diff(ln_g_fall) < 0])
        ln_g_fall, theta_fall = ln_g_fall[falling], theta_fall[falling]
        theta_of_lng = interpolate.PchipInterpolator(ln_g_fall[::-1], theta_fall[::-1])
        ln_g = interpolate.PchipInterpolator(theta, np.log(g))
        return BeamTable(ln_g, theta_of_lng, theta_of_lng.derivative(), theta[i_max],
                         ln_g_fall[-1], ln_g_fall[0], theta, g, self._plateau_breaks())

    def g(self, theta):
        return np.exp(self.table.ln_g(np.clip(np.abs(theta), 0, np.pi)))

    def theta_nodes(self):
        return self.table.theta

    def default_grid(self, cfg):
        coarse = np.geomspace(10.0 ** (cfg.xlim[0] - 1), 10.0 ** (cfg.xlim[1] + 0.5), 700)
        return np.unique(np.concatenate([coarse, cfg.e0 * np.geomspace(10**-1.5, 10**1.5, 700)]))

    def _theta_star(self, g_value):
        ln_g = self.table.ln_g
        if g_value >= float(self.g(0.0)):
            return 0.0
        if g_value <= float(self.g(np.pi)):
            return np.pi
        return optimize.brentq(lambda t: float(ln_g(t)) - np.log(g_value), 0, np.pi, xtol=1e-14)

    def _theta_lower_limit(self, dist, e_obs):
        if dist.e_min is not None and e_obs < dist.e_min:
            return self._theta_star(e_obs / dist.e_min)
        return 0.0

    @staticmethod
    def _weight(dist, e_obs, theta, g):
        return np.sin(theta) / (2 * g) * dist.pdf(e_obs / g)

    def _observed_pdf(self, dist, e_obs):
        """PDF per unit E_obs. Integrates in theta up to the peak of g, then in ln g on the falling branch."""
        t = self.table
        theta_min = self._theta_lower_limit(dist, e_obs)
        total = 0.0
        if theta_min < t.theta_max:
            total += integrate_theta(lambda th: self._weight(dist, e_obs, th, np.exp(t.ln_g(th))),
                                     theta_min, t.theta_max, t.breaks, self.n_gauss)
        theta_start = max(theta_min, t.theta_max)
        x_top = min(float(t.ln_g(theta_start)), t.lng_max)
        if x_top > t.lng_min:
            n_panels = int(np.ceil((x_top - t.lng_min) / self.lng_step))
            x, w = gauss_panels(np.linspace(t.lng_min, x_top, n_panels + 1), self.n_gauss)
            total += np.sum(w * np.abs(t.dtheta_dlng(x)) * self._weight(dist, e_obs, t.theta_of_lng(x), np.exp(x)))
        return total

    def _naive_pdf(self, dist, e_obs):
        ln_g = self.table.ln_g
        return integrate.quad(lambda th: self._weight(dist, e_obs, th, np.exp(ln_g(th))),
                              self._theta_lower_limit(dist, e_obs), np.pi, limit=200)[0]

    def observed_pdf_ln(self, dist, e_grid, naive=False):
        if isinstance(dist, SingleEnergy):
            raise TypeError("use single_energy_pdf for a single intrinsic energy")
        pdf = self._naive_pdf if naive else self._observed_pdf
        return np.array([e * pdf(dist, e) for e in e_grid])

    def single_energy_pdf(self, e0):
        t = self.table
        x = np.linspace(t.lng_min, t.lng_max, 4000)[:-1]
        density = np.sin(t.theta_of_lng(x)) / 2 * np.abs(t.dtheta_dlng(x))
        mass = (1 - np.cos(t.theta_of_lng(t.lng_max))) / 2
        return np.log10(e0) + x / LN10, density, mass


def build_beams(cfg):
    beams = [IsotropicBeam(),
             GaussianBeam(cfg.sigma, 0.0),
             GaussianBeam(cfg.sigma, cfg.theta_p),
             RelativisticBeam.from_config("Relativistic", cfg),
             RelativisticBeam.from_config("RPL", cfg),
             RelativisticBeam.from_config("RG", cfg)]
    return {b.label: b for b in beams}
