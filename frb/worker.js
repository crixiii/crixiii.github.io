const PYODIDE = new URL(self.location.href).searchParams.get("pyodide") || "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

importScripts(PYODIDE + "pyodide.js");

let py = null;
let app = null;
let sklearnLoaded = false;

// percent = share of start-up already finished (omit for messages after start-up)
const status = (text, percent) => postMessage({ type: "status", text, percent });

async function fetchText(path) {
  const response = await fetch(new URL(path, self.location.href));
  if (!response.ok) throw new Error(`could not fetch ${path} (${response.status})`);
  return response.text();
}

async function init() {
  status("loading python…", 0);
  py = await loadPyodide({ indexURL: PYODIDE });
  status("loading numpy…", 25);
  await py.loadPackage("numpy");
  status("loading scipy…", 40);
  await py.loadPackage("scipy");
  status("loading the frbbeaming package…", 75);
  py.FS.mkdirTree("/home/pyodide");
  const bundle = await fetch(new URL("frbbeaming.zip", self.location.href));
  if (!bundle.ok) throw new Error(`could not fetch frbbeaming.zip (${bundle.status})`);
  py.unpackArchive(await bundle.arrayBuffer(), "zip", { extractDir: "/home/pyodide" });
  py.FS.writeFile("/home/pyodide/frb_app.py", await fetchText("frb_app.py"));
  py.runPython("import sys\nsys.path.insert(0, '/home/pyodide')");
  app = py.pyimport("frb_app"); // imports numpy, scipy and frbbeaming
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
