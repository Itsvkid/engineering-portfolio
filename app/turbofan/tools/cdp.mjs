// Minimal CDP driver: headless Edge, collect console + exceptions, run steps, screenshot.
// usage: node cdp.mjs <url> <out.png> [steps...]   steps: wait:ms | click:x,y | key:Name | eval:js | shot:file.png | move:x,y
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";

const [url, out, ...steps] = process.argv.slice(2);
const port = 9333 + Math.floor(Math.random() * 500);
const edge = spawn("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", [
  "--headless=new", "--no-first-run", "--no-default-browser-check", `--user-data-dir=/tmp/edge-cdp-${port}`,
  "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--hide-scrollbars",
  `--window-size=${process.env.W||1600},${process.env.H||1000}`, `--remote-debugging-port=${port}`, "about:blank",
], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let wsUrl;
for (let i = 0; i < 50 && !wsUrl; i++) {
  await sleep(200);
  try { const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); wsUrl = list.find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
}
if (!wsUrl) { console.error("no target"); edge.kill(); process.exit(1); }
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
  if (m.method === "Runtime.consoleAPICalled") {
    const txt = m.params.args.map((a) => a.value ?? a.description ?? "").join(" ");
    if (!/React DevTools|Fast Refresh|HMR/.test(txt)) console.log(`[console.${m.params.type}]`, txt.slice(0, 400));
  }
  if (m.method === "Runtime.exceptionThrown") console.log("[exception]", (m.params.exceptionDetails.exception?.description ?? m.params.exceptionDetails.text).slice(0, 600));
};
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Runtime.enable"); await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: Number(process.env.W||1600), height: Number(process.env.H||1000), deviceScaleFactor: 1, mobile: !!process.env.MOBILE });
await send("Page.navigate", { url });
await sleep(9000);
for (const s of steps) {
  const [k, v] = s.split(/:(.*)/s);
  if (k === "wait") await sleep(Number(v));
  else if (k === "goto") { await send("Page.navigate", { url: v }); await sleep(9000); }
  else if (k === "click" || k === "move") {
    const [x, y] = v.split(",").map(Number);
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
    if (k === "click") {
      await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
      await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
    }
    await sleep(600);
  } else if (k === "key") { await send("Input.dispatchKeyEvent", { type: "keyDown", key: v }); await send("Input.dispatchKeyEvent", { type: "keyUp", key: v }); await sleep(400); }
  else if (k === "eval") { const r = await send("Runtime.evaluate", { expression: v, returnByValue: true }); console.log("[eval]", JSON.stringify(r.result?.result?.value ?? r.result?.exceptionDetails?.text)); }
  else if (k === "shot") { await sleep(800); const r = await send("Page.captureScreenshot", { format: "png" }); writeFileSync(v, Buffer.from(r.result.data, "base64")); console.log("[shot]", v); }
}
await sleep(500);
const r = await send("Page.captureScreenshot", { format: "png" });
writeFileSync(out, Buffer.from(r.result.data, "base64"));
console.log("[shot]", out);
ws.close(); edge.kill(); process.exit(0);
