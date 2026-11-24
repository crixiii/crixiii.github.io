const PYODIDE = new URL(self.location.href).searchParams.get("pyodide") || "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

importScripts(PYODIDE + "pyodide.js");

let py = null;
let app = null;
let sklearnLoaded = false;

const status = (text) => postMessage({ type: "status", text });

async function fetchText(path) {
  const response = await fetch(new URL(path, self.location.href));
  if (!response.ok) throw new Error(`could not fetch ${path} (${response.status})`);
  return response.text();
}

async function init() {
  status("loading python…");
  py = await loadPyodide({ indexURL: PYODIDE });
  status("loading numpy and scipy…");
  await py.loadPackage(["numpy", "scipy"]);
  status("loading the frbbeaming package…");
  py.FS.mkdirTree("/home/pyodide");
  const bundle = await fetch(new URL("frbbeaming.zip", self.location.href));
  if (!bundle.ok) throw new Error(`could not fetch frbbeaming.zip (${bundle.status})`);
  py.unpackArchive(await bundle.arrayBuffer(), "zip", { extractDir: "/home/pyodide" });
  py.FS.writeFile("/home/pyodide/frb_app.py", await fetchText("frb_app.py"));
  py.runPython("import sys\nsys.path.insert(0, '/home/pyodide')");
  app = py.pyimport("frb_app");
  postMessage({ type: "ready" });
}

const ready = init().catch((err) => postMessage({ type: "fatal", error: String(err) }));

onmessage = async (event) => {
  const { id, fn, arg } = event.data;
  try {
    await ready;
    if (!app) throw new Error("python did not start");
    if (fn === "compute_bimodality" && !sklearnLoaded) {
      status("loading scikit-learn (first bimodality run only)…");
      await py.loadPackage("scikit-learn");
      sklearnLoaded = true;
    }
    const t0 = performance.now();
    const data = app[fn](arg);
    postMessage({ type: "result", id, ok: true, data, ms: performance.now() - t0 });
  } catch (err) {
    postMessage({ type: "result", id, ok: false, error: String(err) });
  }
};
