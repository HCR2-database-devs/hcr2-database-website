import { spawn } from "node:child_process";
import { createHmac } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const backendBaseUrl = process.env.BACKEND_BASE_URL ?? "http://127.0.0.1:8000";
const frontendBaseUrl = process.env.FRONTEND_BASE_URL ?? "http://127.0.0.1:5173";
const authSecret = process.env.AUTH_SHARED_SECRET ?? "dev-only-hcr2-secret";
const chromePath =
  process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const apiChecks = [
  ["maps", "/api/v1/maps", (data) => Array.isArray(data) && data.some((row) => row.nameMap === "Countryside")],
  [
    "vehicles",
    "/api/v1/vehicles",
    (data) => Array.isArray(data) && data.some((row) => row.nameVehicle === "Hill Climber"),
  ],
  [
    "players",
    "/api/v1/players",
    (data) => Array.isArray(data) && data.some((row) => row.namePlayer === "Demo Driver"),
  ],
  [
    "tuning parts",
    "/api/v1/tuning-parts",
    (data) => Array.isArray(data) && data.some((row) => row.nameTuningPart === "Coin Boost"),
  ],
  [
    "tuning setups",
    "/api/v1/tuning-setups",
    (data) => Array.isArray(data) && data.some((row) => Array.isArray(row.parts) && row.parts.length > 0),
  ],
  [
    "records",
    "/api/v1/records",
    (data) => Array.isArray(data) && data.some((row) => row.map_name === "Countryside" && row.distance === 12345),
  ],
  [
    "news",
    "/api/v1/news?limit=10",
    (data) => Array.isArray(data.news) && data.news.length > 0,
  ],
  ["hcaptcha sitekey", "/api/v1/hcaptcha/sitekey", (data) => data.sitekey === "dev-hcaptcha-site-key"],
];

const uiChecks = [
  ["/", "About this website"],
  ["/maps", "Countryside"],
  ["/vehicles", "Hill Climber"],
  ["/players", "Demo Driver"],
  ["/tuning-parts", "Coin Boost"],
  ["/tuning-setups", "Wings"],
  ["/records", "Countryside"],
  ["/stats", "Records"],
  ["/privacy", "Privacy"],
  ["/maintenance", "We'll be back soon"],
];
const standaloneUiRoutes = new Set(["/privacy", "/maintenance"]);

function b64url(value) {
  return Buffer.from(value).toString("base64url");
}

function makeDevToken() {
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = b64url(
    JSON.stringify({
      sub: process.env.DEV_DISCORD_ID ?? "dev-admin",
      username: process.env.DEV_DISCORD_USERNAME ?? "Dev Admin",
      exp: Math.floor(Date.now() / 1000) + 86400,
    }),
  );
  const signature = createHmac("sha256", authSecret).update(`${header}.${payload}`).digest("base64url");
  return `${header}.${payload}.${signature}`;
}

function adminHeaders() {
  return {
    Cookie: `WC_TOKEN=${makeDevToken()}`,
    "Content-Type": "application/json",
  };
}

async function adminJson(route, init = {}) {
  const response = await fetch(`${backendBaseUrl}${route}`, {
    ...init,
    headers: {
      ...adminHeaders(),
      ...(init.headers ?? {}),
    },
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Admin route ${route} returned invalid JSON: ${text.slice(0, 300)}`);
  }
  if (!response.ok) {
    throw new Error(`Admin route ${route} returned HTTP ${response.status}: ${text}`);
  }
  return data;
}

async function adminFetch(route, init = {}) {
  return fetch(`${backendBaseUrl}${route}`, {
    ...init,
    headers: {
      ...adminHeaders(),
      ...(init.headers ?? {}),
    },
  });
}

async function adminFormJson(route, fields) {
  const body = new FormData();
  for (const [key, value] of fields) {
    body.append(key, value);
  }
  const response = await fetch(`${backendBaseUrl}${route}`, {
    method: "POST",
    headers: { Cookie: `WC_TOKEN=${makeDevToken()}` },
    body,
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Admin form route ${route} returned invalid JSON: ${text.slice(0, 300)}`);
  }
  if (!response.ok) {
    throw new Error(`Admin form route ${route} returned HTTP ${response.status}: ${text}`);
  }
  return data;
}

async function checkJson(name, baseUrl, route, validator, init) {
  const response = await fetch(`${baseUrl}${route}`, init);
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`${name} returned HTTP ${response.status}: ${text}`);
  }
  const data = JSON.parse(text);
  if (!validator(data)) {
    throw new Error(`${name} returned unexpected payload: ${text.slice(0, 300)}`);
  }
  console.log(`OK ${name}`);
}

async function checkApiSurface() {
  const health = await fetch(`${backendBaseUrl}/health`);
  if (!health.ok) {
    throw new Error(`FastAPI health returned HTTP ${health.status}`);
  }
  console.log("OK backend health");

  const cors = await fetch(`${backendBaseUrl}/api/v1/maps`, {
    method: "OPTIONS",
    headers: {
      Origin: frontendBaseUrl,
      "Access-Control-Request-Method": "GET",
    },
  });
  if (cors.headers.get("access-control-allow-origin") !== frontendBaseUrl) {
    throw new Error("FastAPI CORS did not allow the local frontend origin");
  }
  console.log("OK backend CORS");

  for (const [name, route, validator] of apiChecks) {
    await checkJson(`backend ${name}`, backendBaseUrl, route, validator);
    await checkJson(`frontend proxy ${name}`, frontendBaseUrl, route, validator);
  }

  await checkJson(
    "backend auth logged out",
    backendBaseUrl,
    "/api/v1/auth/status",
    (data) => data.logged === false && data.allowed === false,
  );
  await checkJson(
    "backend auth dev admin",
    backendBaseUrl,
    "/api/v1/auth/status",
    (data) => data.logged === true && data.allowed === true && data.id === "dev-admin",
    { headers: { Cookie: `WC_TOKEN=${makeDevToken()}` } },
  );

  const submitResponse = await fetch(`${backendBaseUrl}/api/v1/submissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const submitPayload = await submitResponse.json();
  if (
    submitResponse.status !== 400 ||
    submitPayload.error !== "hCaptcha verification failed. Please try again."
  ) {
    throw new Error("Public submission hCaptcha rejection did not match the API shape");
  }
  console.log("OK backend public submission hcaptcha rejection");
}

async function checkAdminApiSurface() {
  const suffix = Date.now();

  const pending = await adminJson("/api/v1/admin/pending");
  if (!Array.isArray(pending.pending)) {
    throw new Error("Admin pending list did not return an array");
  }
  const pendingTarget = pending.pending[0] ?? null;
  console.log("OK admin pending list");

  const map = await adminJson("/api/v1/admin/maps", {
    method: "POST",
    body: JSON.stringify({ mapName: `Admin Smoke Map ${suffix}` }),
  });
  const vehicle = await adminJson("/api/v1/admin/vehicles", {
    method: "POST",
    body: JSON.stringify({ vehicleName: `Admin Smoke Vehicle ${suffix}` }),
  });
  const part = await adminJson("/api/v1/admin/tuning-parts", {
    method: "POST",
    body: JSON.stringify({ partName: `Admin Smoke Part ${suffix}` }),
  });
  if (!map.success || !vehicle.success || !part.success) {
    throw new Error("Admin catalog additions did not return success");
  }
  console.log("OK admin catalog additions");

  const formMap = await adminFormJson("/api/v1/admin/maps/form", [["mapName", `Admin Smoke Form Map ${suffix}`]]);
  const formVehicle = await adminFormJson("/api/v1/admin/vehicles/form", [["vehicleName", `Admin Smoke Form Vehicle ${suffix}`]]);
  const formPart = await adminFormJson("/api/v1/admin/tuning-parts/form", [["partName", `Admin Smoke Form Part ${suffix}`]]);
  if (!formMap.success || !formVehicle.success || !formPart.success) {
    throw new Error("Admin multipart catalog additions did not return success");
  }
  console.log("OK admin multipart catalog additions");

  const setup = await adminJson("/api/v1/admin/tuning-setups", {
    method: "POST",
    body: JSON.stringify({ partIds: [1, 2, part.idTuningPart] }),
  });
  if (!setup.success || !setup.idTuningSetup) {
    throw new Error("Admin tuning setup creation did not return a setup id");
  }
  console.log("OK admin tuning setup creation");

  const record = await adminJson("/api/v1/admin/records", {
    method: "POST",
    body: JSON.stringify({
      mapId: map.idMap,
      vehicleId: vehicle.idVehicle,
      distance: 55555,
      playerId: 1,
      tuningSetupId: null,
      questionable: 0,
    }),
  });
  if (!record.success || !record.idRecord) {
    throw new Error("Admin record submit did not return a record id");
  }
  console.log("OK admin record submit");

  await adminJson("/api/v1/admin/records/questionable", {
    method: "PATCH",
    body: JSON.stringify({ recordId: record.idRecord, questionable: 1, note: "Smoke test note" }),
  });
  console.log("OK admin questionable status");

  await adminJson("/api/v1/admin/records/tuning-setup", {
    method: "PATCH",
    body: JSON.stringify({ recordId: record.idRecord, tuningSetupId: setup.idTuningSetup }),
  });
  console.log("OK admin tuning setup assignment");

  await adminJson("/api/v1/admin/records/delete", {
    method: "POST",
    body: JSON.stringify({ recordId: record.idRecord }),
  });
  console.log("OK admin record delete");

  if (pendingTarget) {
    await adminJson("/api/v1/admin/pending/approve", {
      method: "POST",
      body: JSON.stringify({ id: pendingTarget.id }),
    });
    const pendingAfterApprove = await adminJson("/api/v1/admin/pending");
    if (pendingAfterApprove.pending.some((item) => item.id === pendingTarget.id)) {
      throw new Error(`Admin pending approval did not remove item ${pendingTarget.id}`);
    }
    console.log("OK admin pending approval");
  } else {
    console.log("SKIP admin pending approval (no pending submissions)");
  }

  const title = `Admin smoke news ${suffix}`;
  await adminJson("/api/v1/admin/news", {
    method: "POST",
    body: JSON.stringify({ title, content: "Created by admin smoke test." }),
  });
  await checkJson(
    "backend admin news post visible publicly",
    backendBaseUrl,
    "/api/v1/news?limit=20",
    (data) => Array.isArray(data.news) && data.news.some((item) => item.title === title),
  );

  await adminJson("/api/v1/admin/maintenance", {
    method: "PATCH",
    body: JSON.stringify({ action: "enable" }),
  });
  const maintenanceOn = await adminJson("/api/v1/admin/maintenance", { method: "GET" });
  if (maintenanceOn.maintenance !== true) {
    throw new Error("Admin maintenance enable did not persist");
  }
  await adminJson("/api/v1/admin/maintenance", {
    method: "PATCH",
    body: JSON.stringify({ action: "disable" }),
  });
  console.log("OK admin maintenance controls");

  const integrity = await adminJson("/api/v1/admin/integrity", { method: "GET" });
  if (!integrity.ok || !integrity.counts || integrity.counts._worldrecord < 1) {
    throw new Error(`Admin integrity returned unexpected payload: ${JSON.stringify(integrity)}`);
  }
  console.log("OK admin integrity check");

  const createdBackup = await adminJson("/api/v1/admin/backups", { method: "POST" });
  if (!createdBackup.success || !createdBackup.filename || !createdBackup.filename.endsWith(".sql")) {
    throw new Error(`Admin backup creation returned unexpected payload: ${JSON.stringify(createdBackup)}`);
  }
  console.log("OK admin backup creation");

  const listedBackups = await adminJson("/api/v1/admin/backups", { method: "GET" });
  if (!Array.isArray(listedBackups.backups) || !listedBackups.backups.some((item) => item.name === createdBackup.filename)) {
    throw new Error(`Admin backup list did not include ${createdBackup.filename}`);
  }
  console.log("OK admin backup listing");

  const backupDownload = await adminFetch(`/api/v1/admin/backups/${encodeURIComponent(createdBackup.filename)}/download`);
  const backupText = await backupDownload.text();
  if (!backupDownload.ok || !backupText.includes("BEGIN;") || !backupText.includes("_worldrecord")) {
    throw new Error(`Admin backup download returned unexpected payload: ${backupDownload.status} ${backupText.slice(0, 200)}`);
  }
  console.log("OK admin backup download");

  await adminJson(`/api/v1/admin/backups/${encodeURIComponent(createdBackup.filename)}`, { method: "DELETE" });
  const listedAfterDelete = await adminJson("/api/v1/admin/backups", { method: "GET" });
  if (listedAfterDelete.backups.some((item) => item.name === createdBackup.filename)) {
    throw new Error(`Admin backup delete did not remove ${createdBackup.filename}`);
  }
  console.log("OK admin backup delete");
}

function sendCommand(ws, id, method, params = {}) {
  ws.send(JSON.stringify({ id, method, params }));
}

class CdpPage {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.problems = [];

    ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) {
          reject(new Error(`${message.error.message}: ${message.error.data ?? ""}`));
        } else {
          resolve(message.result);
        }
        return;
      }

      if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") {
        this.problems.push(`console error: ${message.params.args.map((arg) => arg.value ?? arg.description).join(" ")}`);
      }
      if (message.method === "Log.entryAdded" && message.params.entry.level === "error") {
        this.problems.push(`log error: ${message.params.entry.text}`);
      }
      if (message.method === "Network.responseReceived" && message.params.response.status >= 400) {
        this.problems.push(`HTTP ${message.params.response.status}: ${message.params.response.url}`);
      }
    });
  }

  command(method, params = {}) {
    const id = this.nextId++;
    sendCommand(this.ws, id, method, params);
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  async evaluate(expression) {
    const result = await this.command("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.text);
    }
    return result.result.value;
  }
}

function waitForWebSocketOpen(ws) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Timed out opening Chrome DevTools websocket")), 10000);
    ws.addEventListener("open", () => {
      clearTimeout(timeout);
      resolve();
    });
    ws.addEventListener("error", (event) => {
      clearTimeout(timeout);
      reject(new Error(`Chrome DevTools websocket error: ${event.message ?? "unknown error"}`));
    });
  });
}

async function waitForChrome(port) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (response.ok) {
        return;
      }
    } catch {
      // Chrome is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Timed out waiting for Chrome DevTools");
}

async function waitForText(page, text) {
  const expression = `Boolean(document.body && document.body.innerText.includes(${JSON.stringify(text)}))`;
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    if (await page.evaluate(expression)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  const body = await page.evaluate("document.body ? document.body.innerText.slice(0, 1000) : ''");
  throw new Error(`Timed out waiting for text ${JSON.stringify(text)}. Body was: ${body}`);
}

async function waitForExpression(page, expression, message) {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    if (await page.evaluate(expression)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(message);
}

async function checkUiSurface() {
  const port = Number(process.env.CHROME_DEBUG_PORT ?? "9322");
  const userDataDir = await mkdtemp(path.join(tmpdir(), "hcr2-chrome-"));
  const chrome = spawn(chromePath, [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--disable-background-networking",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    "about:blank",
  ]);

  try {
    await waitForChrome(port);
    const targetResponse = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {
      method: "PUT",
    });
    const target = await targetResponse.json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await waitForWebSocketOpen(ws);
    const page = new CdpPage(ws);
    await page.command("Runtime.enable");
    await page.command("Log.enable");
    await page.command("Network.enable");
    await page.command("Page.enable");

    for (const [route, text] of uiChecks) {
      const isStandalone = standaloneUiRoutes.has(route);
      page.problems = [];
      await page.command("Page.navigate", { url: `${frontendBaseUrl}${route}` });
      await waitForText(page, text);
      if (!isStandalone) {
        await waitForExpression(
          page,
          "Boolean(document.querySelector('img#logo') && document.querySelector('img#logo').complete && document.querySelector('img#logo').naturalWidth > 0)",
          `Logo did not load on ${route}`,
        );
      }
      const details = await page.evaluate(`(() => {
        return {
          hasDarkModeButton: Boolean(document.querySelector('#dark-mode-toggle')),
          rowCount: document.querySelectorAll('tbody tr').length,
          hasErrorText: document.body.innerText.includes('Database error') || document.body.innerText.includes('Request failed')
        };
      })()`);

      if (!isStandalone && !details.hasDarkModeButton) {
        throw new Error(`Dark mode button is missing on ${route}`);
      }
      if (["/maps", "/vehicles", "/players", "/tuning-parts", "/tuning-setups", "/records"].includes(route) && details.rowCount < 1) {
        throw new Error(`No data rows rendered on ${route}`);
      }
      if (details.hasErrorText) {
        throw new Error(`Error text rendered on ${route}`);
      }
      if (page.problems.length) {
        throw new Error(`Browser problems on ${route}: ${page.problems.join("; ")}`);
      }
      console.log(`OK UI ${route}`);
    }

    await page.command("Page.navigate", { url: `${frontendBaseUrl}/records` });
    await waitForText(page, "Countryside");
    await page.evaluate(`(() => {
      const input = document.querySelector('#search-bar');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, 'Forest');
      input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: 'Forest' }));
    })()`);
    await waitForText(page, "Sample Racer");
    await waitForExpression(
      page,
      "!document.body.innerText.includes('Demo Driver')",
      "Records search filter did not hide non-matching rows",
    );
    await page.evaluate(`(() => {
      const select = document.querySelector('#sort-select');
      select.value = 'dist-desc';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    })()`);
    console.log("OK UI records filters");

    await page.evaluate(`document.querySelector('#news-btn-container button').click()`);
    await waitForText(page, "Created by admin smoke test.");
    await page.evaluate(`document.querySelector('.close-news-btn').click()`);
    console.log("OK UI news modal");

    await page.evaluate(
      `Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Submit Record').click()`,
    );
    await waitForText(page, "Submit a Record (for admin review)");
    await waitForExpression(
      page,
      "document.querySelector('#hcaptcha-widget')?.getAttribute('data-sitekey') === 'dev-hcaptcha-site-key'",
      "Public submit modal did not load the hCaptcha site key",
    );
    console.log("OK UI public submit modal");

    const before = await page.evaluate("document.documentElement.getAttribute('data-theme')");
    await page.evaluate("document.querySelector('#dark-mode-toggle').click()");
    const after = await page.evaluate("document.documentElement.getAttribute('data-theme')");
    if (before === after || after !== "dark") {
      throw new Error("Dark mode toggle did not set data-theme=dark");
    }
    console.log("OK UI dark mode toggle");

    page.problems = [];
    await page.command("Network.setCookie", {
      name: "WC_TOKEN",
      value: makeDevToken(),
      url: frontendBaseUrl,
      path: "/",
    });
    await page.command("Page.navigate", { url: `${frontendBaseUrl}/admin` });
    await waitForText(page, "Submit a New Record");
    await waitForText(page, "Maintenance Mode");
    await waitForText(page, "Database & Backups");
    await page.evaluate(
      `Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Integrity Check').click()`,
    );
    await waitForText(page, "Integrity check completed.");
    await page.evaluate(
      `Array.from(document.querySelectorAll('button')).find((button) => button.textContent.trim() === 'Create Backup').click()`,
    );
    await waitForText(page, "Backup created.");
    await waitForExpression(
      page,
      "Boolean(Array.from(document.querySelectorAll('#backups-list td')).some((cell) => cell.textContent.includes('.sql')))",
      "Admin backup list did not render a SQL backup after creation",
    );
    const uiBackupName = await page.evaluate(
      "Array.from(document.querySelectorAll('#backups-list td')).map((cell) => cell.textContent.trim()).find((text) => text.endsWith('.sql')) || ''",
    );
    if (uiBackupName) {
      await adminJson(`/api/v1/admin/backups/${encodeURIComponent(uiBackupName)}`, { method: "DELETE" });
    }
    if (page.problems.length) {
      throw new Error(`Browser problems on /admin: ${page.problems.join("; ")}`);
    }
    console.log("OK UI admin page");
    ws.close();
  } finally {
    chrome.kill();
    await new Promise((resolve) => {
      if (chrome.exitCode !== null) {
        resolve();
        return;
      }
      const timeout = setTimeout(resolve, 1500);
      chrome.once("exit", () => {
        clearTimeout(timeout);
        resolve();
      });
    });
    try {
      await rm(userDataDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 250 });
    } catch (error) {
      console.warn(`WARN unable to remove temporary Chrome profile: ${error.message}`);
    }
  }
}

await checkApiSurface();
await checkAdminApiSurface();
await checkUiSurface();
