const viewContainer = document.getElementById("viewContainer");
const viewTitle = document.getElementById("viewTitle");
const tokenStatus = document.getElementById("tokenStatus");

// ---- token helpers ----
function getToken() {
  return localStorage.getItem("socialhunt_token");
}
function setToken(token) {
  if (!token) localStorage.removeItem("socialhunt_token");
  else localStorage.setItem("socialhunt_token", token);
  renderTokenStatus();
}
function authHeaders(extra = {}) {
  const t = getToken();
  return t ? { ...extra, "X-Plugin-Token": t } : { ...extra };
}
function renderTokenStatus() {
  tokenStatus.textContent = getToken() ? "Token: set" : "Token: not set";
}

const viewTitles = {
  dashboard: "Dashboard",
  search: "Search",
  "breach-search": "Breach Search",
  reverse: "Reverse Image",
  history: "History",
  plugins: "Plugins",
  tokens: "Token",
  settings: "Settings",
};

async function loadView(name) {
  document.querySelectorAll(".menu-btn[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === name);
  });

  viewTitle.textContent = viewTitles[name] || name;

  const res = await fetch(`/static/views/${name}.html?v=layout3`, {
    cache: "no-store",
  });
  viewContainer.innerHTML = await res.text();

  if (name === "dashboard") initDashboardView();
  if (name === "search") initSearchView();
  if (name === "breach-search") initBreachSearchView();
  if (name === "reverse") initReverseView();
  if (name === "history") initHistoryView();
  if (name === "plugins") initPluginsView();
  if (name === "tokens") initTokensView();
  if (name === "settings") initSettingsView();
}

// ----------------------
// Local history (browser only)
// ----------------------
const HISTORY_MAX = 200;
const KEY_SEARCH_HISTORY = "socialhunt_search_history";
const KEY_REVERSE_HISTORY = "socialhunt_reverse_history";

function loadJsonArray(key) {
  try {
    const raw = localStorage.getItem(key);
    const v = JSON.parse(raw);
    return Array.isArray(v) ? v : [];
  } catch (_) {
    return [];
  }
}
function saveJsonArray(key, arr) {
  const limited = Array.isArray(arr) ? arr.slice(0, HISTORY_MAX) : [];
  localStorage.setItem(key, JSON.stringify(limited));
}

function addSearchHistoryEntry({ username, providers, job_id }) {
  const items = loadJsonArray(KEY_SEARCH_HISTORY);
  items.unshift({
    ts: Date.now(),
    username,
    providers_count: (providers || []).length,
    job_id,
    results_count: null,
    state: "running",
  });
  saveJsonArray(KEY_SEARCH_HISTORY, items);
}

function markSearchHistory(job_id, patch) {
  const items = loadJsonArray(KEY_SEARCH_HISTORY);
  const idx = items.findIndex((x) => x && x.job_id === job_id);
  if (idx >= 0) {
    items[idx] = { ...items[idx], ...patch };
    saveJsonArray(KEY_SEARCH_HISTORY, items);
  }
}

function addReverseHistoryEntry({ image_url, links }) {
  const items = loadJsonArray(KEY_REVERSE_HISTORY);
  items.unshift({
    ts: Date.now(),
    image_url,
    links: Array.isArray(links) ? links : [],
  });
  saveJsonArray(KEY_REVERSE_HISTORY, items);
}

// ----------------------
// Dashboard
// ----------------------
function initDashboardView() {
  const last = localStorage.getItem("socialhunt_last_job");
  const el = document.getElementById("lastJob");
  if (last && el) {
    el.innerHTML = `Last job: ${escapeHtml(
      last,
    )} <button id="loadLastJob" class="btn small">Load</button>`;
    const go = document.getElementById("loadLastJob");
    if (go) go.onclick = () => window.loadJob(last);
  }
}

// ----------------------
// Search
// ----------------------
function badge(status) {
  return `<span class="badge ${status}">${escapeHtml(status)}</span>`;
}
async function fetchProviders() {
  const res = await fetch("/api/providers");
  const data = await res.json();
  return data.providers || [];
}
async function fetchWhoami() {
  try {
    const res = await fetch("/api/whoami");
    const data = await res.json();
    return data;
  } catch (_) {
    return null;
  }
}
function renderProviders(providers) {
  const box = document.getElementById("providers");
  box.innerHTML = (providers || [])
    .map(
      (p) =>
        `<label class="provider"><input type="checkbox" data-name="${p}"><span>${p}</span></label>`,
    )
    .join("");
}
function selectedProviders() {
  return [
    ...document.querySelectorAll('input[type="checkbox"][data-name]:checked'),
  ].map((x) => x.dataset.name);
}

function renderResults(job, containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`renderResults: container #${containerId} not found.`);
    return;
  }

  const results = job.results || [];

  const rows = results
    .map((r) => {
      const prof = r.profile || {};
      const avatar =
        prof.avatar_url && prof.avatar_url !== "undefined"
          ? `<img src="${prof.avatar_url}" alt="" class="avatar"/>`
          : "";
      const name = escapeHtml(prof.display_name || "");
      const followers = escapeHtml(String(prof.followers ?? ""));
      const following = escapeHtml(String(prof.following ?? ""));
      const created = escapeHtml(prof.created_at || "");
      const link = r.url
        ? `<a href="${r.url}" target="_blank" rel="noreferrer">${r.url}</a>`
        : "";
      const err = r.error
        ? `<div class="danger" style="margin-top:6px">${escapeHtml(r.error)}</div>`
        : "";

      const notes = [];
      if (prof.bio) notes.push(prof.bio);
      if (prof.note) notes.push(prof.note);
      if (prof.result_count) notes.push(`Results: ${prof.result_count}`);
      if (prof.breach_sources)
        notes.push(`Sources: ${prof.breach_sources.join(", ")}`);

      if (r.face_match) {
        if (r.face_match.match) {
          notes.push("FACE MATCH");
        } else {
          notes.push(
            `NO FACE MATCH (reason: ${r.face_match.reason || "unknown"})`,
          );
        }
      }
      if (r.face_match_error) {
        notes.push(`FACE SEARCH ERROR: ${r.face_match_error}`);
      }
      const noteHtml = notes.length
        ? `<div class="muted" style="margin-top:6px">${escapeHtml(notes.join(" "))}</div>`
        : "";
      return `
      <tr>
        <td>${r.provider}</td>
        <td>${badge(r.status)}</td>
        <td>${avatar}</td>
        <td>${name}</td>
        <td>${followers}</td>
        <td>${following}</td>
        <td>${created}</td>
        <td>${link}${noteHtml}${err}</td>
        <td>${r.http_status ?? ""}</td>
        <td>${r.elapsed_ms ?? ""}</td>
      </tr>
    `;
    })
    .join("");

  container.innerHTML = `
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Status</th>
            <th>Avatar</th>
            <th>Name</th>
            <th>Followers</th>
            <th>Following</th>
            <th>Created</th>
            <th>URL / Notes</th>
            <th>HTTP</th>
            <th>ms</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ----------------------
// Breach Search
// ----------------------
async function initBreachSearchView() {
  const termEl = document.getElementById("breachTerm");
  const startBtn = document.getElementById("startBreachScan");
  const statusEl = document.getElementById("breachStatus");

  startBtn.onclick = async () => {
    const term = termEl.value.trim();
    if (!term) {
      statusEl.textContent = "Enter a search term.";
      return;
    }

    statusEl.textContent = "Starting scan...";
    document.getElementById("breachResults").innerHTML = "";

    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: term,
        providers: ["breachvip"],
      }),
    });

    const data = await res.json().catch(() => ({}));
    const jobId = data.job_id;
    if (!jobId) {
      statusEl.textContent = "Failed to start.";
      return;
    }

    statusEl.textContent = `Job ${jobId} running...`;

    for (;;) {
      await new Promise((r) => setTimeout(r, 1000));
      const jr = await fetch(`/api/jobs/${jobId}`);
      const job = await jr.json();

      if (job.state === "done") {
        statusEl.textContent = "Done.";
        renderResults(job, "breachResults");
        return;
      }
      if (job.state === "failed") {
        statusEl.textContent = "Failed: " + (job.error || "unknown");
        return;
      }
      statusEl.textContent = `Running... (${
        (job.results || []).length
      } results so far)`;
      if (job.results && job.results.length > 0) {
        renderResults(job, "breachResults");
      }
    }
  };
}

async function monitorJob(jobId) {
  const statusEl = document.getElementById("status");
  for (;;) {
    await new Promise((r) => setTimeout(r, 1000));
    const jr = await fetch(`/api/jobs/${jobId}`);
    const job = await jr.json();

    if (job.state === "done") {
      if (statusEl) statusEl.textContent = "Done.";
      markSearchHistory(jobId, {
        state: "done",
        results_count: (job.results || []).length,
      });
      renderResults(job, "results");
      return;
    }
    if (job.state === "failed") {
      if (statusEl)
        statusEl.textContent = "Failed: " + (job.error || "unknown");
      markSearchHistory(jobId, {
        state: "failed",
        error: job.error || "unknown",
      });
      return;
    }
    if (statusEl)
      statusEl.textContent = `Running... (${
        (job.results || []).length
      } results so far)`;
    if (job.results && job.results.length > 0) {
      renderResults(job, "results");
    }
  }
}

async function startScan() {
  const usernameEl = document.getElementById("username");
  const statusEl = document.getElementById("status");
  const enableFaceSearchEl = document.getElementById("enableFaceSearch");
  const faceImagesEl = document.getElementById("faceImages");

  const username = (usernameEl?.value || "").trim();
  if (!username) {
    statusEl.textContent = "Enter a username.";
    return;
  }

  const useFaceSearch = enableFaceSearchEl?.checked;
  const faceImages = faceImagesEl?.files || [];

  let res;
  if (useFaceSearch) {
    if (faceImages.length === 0) {
      statusEl.textContent = "Select at least one image file for face search.";
      return;
    }
    statusEl.textContent = "Starting face scan...";
    const formData = new FormData();
    formData.append("username", username);
    for (const file of faceImages) {
      formData.append("files", file);
    }
    res = await fetch("/api/face-search", {
      method: "POST",
      body: formData,
    });
  } else {
    const providers = selectedProviders();
    statusEl.textContent = "Starting scan...";
    res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, providers }),
    });
  }

  const data = await res.json().catch(() => ({}));
  const jobId = data.job_id;
  if (!jobId) {
    statusEl.textContent = "Failed to start.";
    return;
  }

  localStorage.setItem("socialhunt_last_job", jobId);
  addSearchHistoryEntry({
    username,
    providers: useFaceSearch ? ["face-search"] : selectedProviders(),
    job_id: jobId,
  });

  statusEl.textContent = `Job ${jobId} running...`;

  await monitorJob(jobId);
}

window.loadJob = async function (jobId) {
  await loadView("search");
  const statusEl = document.getElementById("status");
  if (statusEl) statusEl.textContent = `Loading job ${jobId}...`;

  try {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Job not found");
    const job = await res.json();

    if (job.state === "running") {
      if (statusEl) statusEl.textContent = `Job ${jobId} running...`;
      renderResults(job, "results");
      await monitorJob(jobId);
    } else {
      renderResults(job, "results");
      if (statusEl)
        statusEl.textContent = `Loaded job ${jobId} (${job.state}).`;
    }
  } catch (e) {
    if (statusEl) statusEl.textContent = "Error loading job: " + e.message;
  }
};

async function initSearchView() {
  const loadBtn = document.getElementById("loadProviders");
  const allBtn = document.getElementById("selectAll");
  const noneBtn = document.getElementById("selectNone");
  const startBtn = document.getElementById("start");
  const statusEl = document.getElementById("status");
  const whoEl = document.getElementById("whoami");
  const enableFaceSearchEl = document.getElementById("enableFaceSearch");
  const faceSearchContainerEl = document.getElementById("faceSearchContainer");

  enableFaceSearchEl.onchange = () => {
    faceSearchContainerEl.style.display = enableFaceSearchEl.checked
      ? "block"
      : "none";
  };

  loadBtn.onclick = async () => {
    statusEl.textContent = "Loading providers...";
    const names = await fetchProviders();
    renderProviders(names);
    statusEl.textContent = `Loaded ${names.length} providers.`;
  };

  allBtn.onclick = () => {
    document
      .querySelectorAll('input[type="checkbox"][data-name]')
      .forEach((x) => (x.checked = true));
  };

  noneBtn.onclick = () => {
    document
      .querySelectorAll('input[type="checkbox"][data-name]')
      .forEach((x) => (x.checked = false));
  };

  startBtn.onclick = startScan;

  // auto-load
  const names = await fetchProviders();
  renderProviders(names);

  const who = await fetchWhoami();
  if (who && who.client_ip) {
    const via = who.via ? ` (${who.via})` : "";
    whoEl.textContent = `Your IP (as seen by the API): ${who.client_ip}${via}`;
  } else {
    whoEl.textContent = "";
  }
}

// ----------------------
// Reverse image
// ----------------------
function initReverseView() {
  const img = document.getElementById("imageUrl");
  const out = document.getElementById("reverseOut");
  const btn = document.getElementById("reverseGo");
  const uploadBtn = document.getElementById("reverseUploadGo");
  const uploadFile = document.getElementById("reverseUploadFile");

  function render(links, previewUrl, warning) {
    const linkHtml = (links || [])
      .map(
        (x) =>
          `<div class="linkrow"><a target="_blank" rel="noreferrer" href="${x.url}">${x.name}</a></div>`,
      )
      .join("");

    let previewHtml = "";
    if (previewUrl) {
      previewHtml = `
      <div style="margin-bottom:10px">
        <a href="${previewUrl}" target="_blank">
          <img src="${previewUrl}" style="max-height:100px;border-radius:4px;border:1px solid #444">
        </a>
        <div style="margin-top:8px; display:flex; gap:8px;">
            <input type="text" readonly value="${escapeHtml(
              previewUrl,
            )}" style="flex:1; padding:4px;" onclick="this.select()">
            <button class="btn small" onclick="navigator.clipboard.writeText(this.previousElementSibling.value).then(()=>alert('Copied!'))">Copy URL</button>
        </div>
        <p class="muted" style="font-size:0.8em; margin-top:4px">
            Use "Copy URL" for manual uploads (PimEyes, FaceCheck.ID).
        </p>
      </div>`;
    }

    const warningHtml = warning
      ? `<div class="warning" style="margin-bottom:10px; border:1px solid #c77; background:#411; padding:8px; border-radius:4px;">${escapeHtml(
          warning,
        )}</div>`
      : "";

    out.innerHTML = warningHtml + previewHtml + linkHtml;
  }

  if (btn) {
    btn.onclick = async () => {
      const image_url = img.value.trim();
      if (!image_url) return alert("Paste an image URL.");

      out.innerHTML = '<div class="muted">Searching...</div>';

      const r = await fetch("/api/reverse_image_links", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url }),
      });

      const j = await r.json().catch(() => ({}));
      if (!r.ok) return alert(j.detail || `Failed (${r.status})`);

      // Save local history
      addReverseHistoryEntry({ image_url, links: j.links || [] });

      render(j.links, image_url);
    };
  }

  if (uploadBtn) {
    uploadBtn.onclick = async () => {
      const file = uploadFile?.files[0];
      if (!file) return alert("Select an image file.");

      out.innerHTML = '<div class="muted">Uploading...</div>';

      const fd = new FormData();
      fd.append("file", file);

      const r = await fetch("/api/reverse_image_upload", {
        method: "POST",
        body: fd,
      });

      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        out.innerHTML = `<div class="danger">Error: ${escapeHtml(
          j.detail || "Upload failed",
        )}</div>`;
        return;
      }

      // Save local history
      addReverseHistoryEntry({ image_url: j.image_url, links: j.links || [] });

      const warn = j.is_private_ip
        ? "Warning: Your server appears to be on a private IP (localhost). External engines (Google Lens, etc.) cannot download this image. Use a public URL or a tunnel."
        : null;

      render(j.links, j.image_url, warn);
    };
  }
}

// ----------------------
// History
// ----------------------
function fmtWhen(ts) {
  try {
    return new Date(ts).toLocaleString();
  } catch (_) {
    return "";
  }
}

function initHistoryView() {
  const searchBody = document.getElementById("searchHistoryBody");
  const reverseBody = document.getElementById("reverseHistoryBody");
  const searchEmpty = document.getElementById("searchHistoryEmpty");
  const reverseEmpty = document.getElementById("reverseHistoryEmpty");
  const clearSearch = document.getElementById("searchHistoryClear");
  const clearReverse = document.getElementById("reverseHistoryClear");
  const refreshBtn = document.getElementById("historyRefresh");

  function render() {
    // Search
    const searches = loadJsonArray(KEY_SEARCH_HISTORY);
    if (searchEmpty)
      searchEmpty.style.display = searches.length ? "none" : "block";
    if (searchBody) {
      searchBody.innerHTML = searches
        .map((x) => {
          const providers = x.providers_count ?? "";
          const job = x.job_id ? escapeHtml(x.job_id) : "";
          const results =
            (x.results_count ?? "") +
            (x.state ? ` (${escapeHtml(x.state)})` : "");

          let action = escapeHtml(String(results));
          if (x.job_id) {
            action += ` <button class="btn small" style="margin-left:10px" onclick="loadJob('${escapeHtml(
              x.job_id,
            )}')">View</button>`;
          }

          return `<tr>
          <td>${escapeHtml(fmtWhen(x.ts))}</td>
          <td>${escapeHtml(x.username || "")}</td>
          <td>${escapeHtml(String(providers))}</td>
          <td>${job}</td>
          <td>${action}</td>
        </tr>`;
        })
        .join("");
    }

    // Reverse
    const reverses = loadJsonArray(KEY_REVERSE_HISTORY);
    if (reverseEmpty)
      reverseEmpty.style.display = reverses.length ? "none" : "block";
    if (reverseBody) {
      reverseBody.innerHTML = reverses
        .map((x) => {
          const img = x.image_url || "";
          const links = Array.isArray(x.links) ? x.links : [];
          const linkHtml = links
            .slice(0, 4)
            .map((l) => {
              const name = escapeHtml(l.name || "Link");
              const url = escapeHtml(l.url || "#");
              return `<a class="mini-link" target="_blank" rel="noreferrer" href="${url}">${name}</a>`;
            })
            .join(" ");
          const more =
            links.length > 4
              ? ` <span class="muted">+${links.length - 4} more</span>`
              : "";
          return `<tr>
          <td>${escapeHtml(fmtWhen(x.ts))}</td>
          <td>${escapeHtml(img)}</td>
          <td>${linkHtml}${more}</td>
        </tr>`;
        })
        .join("");
    }
  }

  if (clearSearch) {
    clearSearch.onclick = () => {
      localStorage.removeItem(KEY_SEARCH_HISTORY);
      render();
    };
  }

  if (clearReverse) {
    clearReverse.onclick = () => {
      localStorage.removeItem(KEY_REVERSE_HISTORY);
      render();
    };
  }

  if (refreshBtn) {
    refreshBtn.onclick = render;
  }

  render();
}

// ----------------------
// Tokens
// ----------------------
function initTokensView() {
  const input = document.getElementById("tokenInput");
  const save = document.getElementById("tokenSave");
  const clear = document.getElementById("tokenClear");

  const statusEl = document.getElementById("adminTokenStatus");
  const serverTokenInput = document.getElementById("serverToken");
  const bootstrapSecretInput = document.getElementById("bootstrapSecret");
  const serverTokenSet = document.getElementById("serverTokenSet");

  input.value = getToken() || "";
  clear.onclick = () => {
    input.value = "";
    setToken("");
  };

  async function loadStatus() {
    if (!statusEl) return;
    statusEl.textContent = "Loading...";
    const r = await fetch("/api/admin/status", { cache: "no-store" });
    const j = await r.json();
    statusEl.innerHTML = `
      Admin token is ${j.admin_token_set ? "SET" : "NOT SET"}<br>
      Source: ${j.admin_token_source}<br>
      Web plugin uploads: ${
        j.web_plugin_upload_enabled ? "ENABLED" : "DISABLED"
      }<br>
      Bootstrap (env): ${j.bootstrap_env_enabled ? "ENABLED" : "DISABLED"}<br>
      Bootstrap (secret): ${
        j.bootstrap_secret_required ? "REQUIRED" : "NOT SET"
      }
    `;
  }

  save.onclick = async () => {
    const newTok = input.value.trim();
    if (!newTok) return alert("Enter a token.");
    setToken(newTok);

    const headers = { "Content-Type": "application/json" };
    const boot = bootstrapSecretInput.value.trim();
    if (boot) headers["X-Bootstrap-Secret"] = boot;

    const r = await fetch("/api/admin/token", {
      method: "PUT",
      headers: authHeaders(headers),
      body: JSON.stringify({ token: newTok }),
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      alert("Token saved. This will be used for future API requests.");
      loadStatus();
    } else {
      alert("Failed: " + (j.detail || "Unknown error"));
    }
  };

  loadStatus();
}

// ----------------------
// Plugins
// ----------------------
function initPluginsView() {
  const fileEl = document.getElementById("pluginFile");
  const uploadBtn = document.getElementById("pluginUpload");
  const reloadBtn = document.getElementById("pluginReload");
  const outEl = document.getElementById("pluginOut");

  function setOut(txt, isErr) {
    outEl.textContent = txt;
    outEl.className = isErr ? "danger" : "";
  }

  uploadBtn.onclick = async () => {
    if (!fileEl.files.length) return setOut("Select a file.", true);
    const fd = new FormData();
    fd.append("file", fileEl.files[0]);

    const r = await fetch("/api/plugin/upload", {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      setOut(
        `Installed: ${j.installed.join(", ") || "none"}. Total providers: ${
          (j.providers || []).length
        }.`,
      );
    } else setOut(j.detail || `Upload failed (${r.status})`, true);
  };

  reloadBtn.onclick = async () => {
    const r = await fetch("/api/providers/reload", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok)
      setOut(`Reloaded. Total providers: ${(j.providers || []).length}.`);
    else setOut(j.detail || `Reload failed (${r.status})`, true);
  };
}

// ----------------------
// Settings
// ----------------------
function initSettingsView() {
  const tableBody = document.getElementById("settingsTable").tBodies[0];
  const addBtn = document.getElementById("settingsAdd");
  const saveBtn = document.getElementById("settingsSave");
  const reloadBtn = document.getElementById("settingsReload");
  const msgEl = document.getElementById("settingsMsg");
  const publicUrlInput = document.getElementById("public_url");
  const savePublicUrlBtn = document.getElementById("saveSettings");
  const updateBtn = document.getElementById("updateBtn");
  const updateLog = document.getElementById("updateLog");

  function showMsg(txt) {
    msgEl.style.display = "block";
    msgEl.textContent = txt;
  }
  function rowHtml(key = "", val = "", secret = false, isSet = false) {
    const displayVal = secret && isSet ? "•••••• (set)" : val;
    return `
      <tr>
        <td><input class="input s-key" placeholder="e.g. hibp_api_key" value="${escapeHtml(key)}"></td>
        <td><input class="input s-val" placeholder="value" value="${escapeHtml(displayVal)}"></td>
        <td style="text-align:center"><input type="checkbox" class="s-secret" ${secret ? "checked" : ""}></td>
        <td><button class="btn danger s-del" type="button">Remove</button></td>
      </tr>
    `;
  }
  function bindRowEvents() {
    tableBody.querySelectorAll(".s-del").forEach((btn) => {
      btn.onclick = () => btn.closest("tr").remove();
    });
  }
  async function load() {
    if (!getToken()) {
      tableBody.innerHTML = "";
      showMsg("Set token first (Token page).");
      return;
    }

    tableBody.innerHTML = "";
    const r = await fetch("/api/settings", { headers: authHeaders() });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      showMsg(j.detail || `Failed (${r.status})`);
      return;
    }

    const settings = j.settings || {};

    if (settings.public_url && publicUrlInput) {
      publicUrlInput.value = settings.public_url.value || "";
    }

    for (const [k, meta] of Object.entries(settings)) {
      if (k === "public_url") continue;
      tableBody.insertAdjacentHTML(
        "beforeend",
        rowHtml(k, meta.value, meta.secret, meta.is_set),
      );
    }

    bindRowEvents();
    showMsg("Loaded.");
  }
  addBtn.onclick = () => {
    tableBody.insertAdjacentHTML("beforeend", rowHtml());
    bindRowEvents();
  };
  saveBtn.onclick = async () => {
    if (!getToken()) return alert("Set token first (Token page).");

    const rows = [...tableBody.querySelectorAll("tr")];
    const out = {};

    for (const tr of rows) {
      const k = tr.querySelector(".s-key").value.trim();
      const v = tr.querySelector(".s-val").value;
      const secret = tr.querySelector(".s-secret").checked;
      if (!k) continue;

      if (secret && (v === "•••••• (set)" || v.trim() === "")) continue;
      out[k] = v;
    }

    const r = await fetch("/api/settings", {
      method: "PUT",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ settings: out }),
    });

    const j = await r.json().catch(() => ({}));
    if (!r.ok) return showMsg(j.detail || `Save failed (${r.status})`);

    showMsg("Saved. Reloading…");
    await load();
  };
  reloadBtn.onclick = load;

  if (savePublicUrlBtn) {
    savePublicUrlBtn.onclick = async () => {
      const val = publicUrlInput.value.trim();
      const r = await fetch("/api/settings", {
        method: "PUT",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ settings: { public_url: val } }),
      });

      if (r.ok) {
        alert("Public URL saved.");
        load();
      } else {
        alert("Failed to save.");
      }
    };
  }

  if (updateBtn) {
    updateBtn.onclick = async () => {
      if (!confirm("Are you sure you want to pull updates from GitHub?"))
        return;

      updateBtn.disabled = true;
      updateLog.style.display = "block";
      updateLog.textContent = "Updating...";

      try {
        const r = await fetch("/api/admin/update", {
          method: "POST",
          headers: authHeaders(),
        });
        const j = await r.json();

        if (j.ok) {
          updateLog.textContent =
            (j.stdout || "") + "\n" + (j.message || "Update finished.");
          alert(
            "Update successful. Please restart the server manually if necessary.",
          );
        } else {
          updateLog.textContent =
            (j.stderr || "") + "\n" + (j.error || "Update failed.");
          alert("Update failed.");
        }
      } catch (e) {
        updateLog.textContent = "Error: " + e.message;
      } finally {
        updateBtn.disabled = false;
      }
    };
  }

  load();
}

// ----------------------
// Init
// ----------------------
function escapeHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const logoutBtn = document.getElementById("logout");
if (logoutBtn) {
  logoutBtn.onclick = () => {
    if (confirm("Are you sure you want to log out?")) {
      setToken("");
      window.location = "/login";
    }
  };
}

(async () => {
  renderTokenStatus();
  // auto-verify token and redirect to login if needed
  try {
    const r = await fetch("/api/auth/verify", {
      method: "POST",
      headers: authHeaders(),
    });
    if (!r.ok) throw new Error("auth");
  } catch (_) {
    if (window.location.pathname !== "/login") {
      window.location = "/login";
      return;
    }
  }

  // view loader
  document.querySelectorAll(".menu-btn[data-view]").forEach((b) => {
    b.onclick = () => loadView(b.dataset.view);
  });
  loadView("dashboard");
})();
