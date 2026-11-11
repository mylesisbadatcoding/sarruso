const $ = (id) => document.getElementById(id);
const fmt = {
  num: (v, d = 2) => (v === null || v === undefined ? "–" : Number(v).toFixed(d)),
  pct: (v) => (v === null || v === undefined ? "–" : (v * 100).toFixed(1) + "%"),
  ms: (v) => (v === null || v === undefined ? "–" : Math.round(v) + " ms"),
  sec: (v) => (v === null || v === undefined ? "–" : Number(v).toFixed(2) + " s"),
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c]));

let rec = null;   // active recording session
let completed = []; // finalized segment texts in this session

// ---------- status & entries ----------

async function loadStatus() {
  const s = await (await fetch("/api/status")).json();
  const b = $("model-badge");
  b.textContent = s.stub ? `${s.model} (stub: no model loaded)` : s.model;
  b.className = "badge " + (s.stub ? "stub" : "ok");
}

async function loadEntries() {
  const { entries, summary } = await (await fetch("/api/entries")).json();
  renderSummary(summary);
  renderEntries(entries);
}

function renderSummary(s) {
  const card = (label, value, hint = "") =>
    `<div class="card"><div class="label">${label}</div><div class="value">${value}</div><div class="hint">${hint}</div></div>`;
  $("summary").innerHTML = [
    card("Entries", s.count, `${fmt.sec(s.total_audio_seconds)} of audio`),
    card("Mean RTF", fmt.num(s.mean_rtf, 3), "lower is faster; <1 is real-time"),
    card("Mean tok/s", fmt.num(s.mean_tokens_per_sec, 1), "generated tokens per second"),
    card("Mean inference", fmt.ms(s.mean_infer_ms), "final pass per entry"),
    card("Mean first text", fmt.ms(s.mean_first_text_ms), "live latency"),
    card("Mean WER", fmt.pct(s.mean_wer), `${s.with_reference} with reference`),
    card("Mean CER", fmt.pct(s.mean_cer), "character error rate"),
  ].join("");
}

function renderEntries(entries) {
  $("empty").hidden = entries.length > 0;
  $("entries-body").innerHTML = entries.map((e) => {
    const when = new Date(e.created_at).toLocaleTimeString();
    const werCls = e.wer === null ? "" : e.wer <= 0.1 ? "good" : e.wer > 0.3 ? "bad" : "";
    const rtfCls = e.rtf === null ? "" : e.rtf < 1 ? "good" : "bad";
    return `<tr>
      <td>${when}</td>
      <td>${esc(e.source)}</td>
      <td class="text">${esc(e.text) || "<em>(no speech)</em>"}</td>
      <td class="num">${fmt.sec(e.audio_seconds)}</td>
      <td class="num">${fmt.ms(e.infer_ms)}</td>
      <td class="num ${rtfCls}">${fmt.num(e.rtf, 3)}</td>
      <td class="num">${fmt.num(e.tokens_per_sec, 1)}</td>
      <td class="num ${werCls}">${fmt.pct(e.wer)}</td>
      <td class="num">${fmt.pct(e.cer)}</td>
      <td class="num">${fmt.ms(e.first_text_ms)}</td>
      <td class="num">${fmt.ms(e.avg_pass_ms)}</td>
      <td><input class="ref" type="text" value="${esc(e.reference)}" data-id="${e.id}" placeholder="add reference"></td>
      <td><button class="row-del" data-del="${e.id}" title="Delete entry">✕</button></td>
    </tr>`;
  }).join("");
}

$("entries-body").addEventListener("change", async (ev) => {
  const input = ev.target.closest("input.ref");
  if (!input) return;
  await fetch(`/api/entries/${input.dataset.id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reference: input.value.trim() || null }),
  });
  loadEntries();
});

$("entries-body").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button[data-del]");
  if (!btn) return;
  await fetch(`/api/entries/${btn.dataset.del}`, { method: "DELETE" });
  loadEntries();
});

$("clear-btn").addEventListener("click", async () => {
  if (!confirm("Delete all entries?")) return;
  await fetch("/api/entries", { method: "DELETE" });
  loadEntries();
});

// ---------- live recording ----------

function setStatus(text) { $("status").textContent = text; }

function showLive(partial = "") {
  const done = completed.join(" ");
  $("live").innerHTML =
    `${esc(done)}${done && partial ? " " : ""}<span class="partial">${esc(partial)}</span>`;
}

async function startRecording() {
  completed = [];
  showLive("");
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, noiseSuppression: true, echoCancellation: true },
  });
  const ctx = new AudioContext({ sampleRate: 16000 });
  await ctx.audioWorklet.addModule("/static/pcm-worklet.js");
  const source = ctx.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(ctx, "pcm-capture");
  source.connect(node);

  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/live`);
  ws.binaryType = "arraybuffer";
  rec = { stream, ctx, node, ws, stopping: false };

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: "start", reference: $("session-ref").value.trim() || null }));
    node.port.onmessage = (e) => { if (ws.readyState === 1) ws.send(e.data); };
    setStatus("Listening…");
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "partial") {
      showLive(msg.text);
      setStatus(`Listening · ${msg.audio_seconds.toFixed(1)} s buffered · last pass ${Math.round(msg.infer_ms)} ms`);
    } else if (msg.type === "entry") {
      if (msg.entry.text) completed.push(msg.entry.text);
      showLive("");
      loadEntries();
    } else if (msg.type === "done") {
      finishRecording("Saved.");
    }
  };
  ws.onerror = () => { setStatus("WebSocket error. Is the server running?"); finishRecording(); };
  ws.onclose = () => { if (rec && !rec.stopping) finishRecording(); };

  $("rec-btn").textContent = "■ Stop";
  $("rec-btn").classList.add("recording");
}

function stopRecording() {
  if (!rec || rec.stopping) return;
  rec.stopping = true;
  setStatus("Finishing last segment…");
  if (rec.ws.readyState === 1) rec.ws.send(JSON.stringify({ type: "stop" }));
  else finishRecording();
}

function finishRecording(message = "Idle") {
  if (!rec) return;
  const r = rec;
  rec = null;
  r.node.port.onmessage = null;
  r.stream.getTracks().forEach((t) => t.stop());
  r.ctx.close();
  if (r.ws.readyState <= 1) r.ws.close();
  $("rec-btn").textContent = "● Start recording";
  $("rec-btn").classList.remove("recording");
  setStatus(message);
  loadEntries();
}

$("rec-btn").addEventListener("click", () => {
  if (rec) stopRecording();
  else startRecording().catch((err) => setStatus("Microphone error: " + err.message));
});

// ---------- file upload ----------

$("file-input").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  if (!file) return;
  setStatus(`Transcribing ${file.name}…`);
  const form = new FormData();
  form.append("file", file);
  form.append("reference", $("upload-ref").value.trim());
  const res = await fetch("/api/upload", { method: "POST", body: form });
  if (!res.ok) {
    setStatus("Upload failed: " + (await res.json()).detail);
  } else {
    setStatus(`Saved entry for ${file.name}.`);
    loadEntries();
  }
  ev.target.value = "";
});

// ---------- boot ----------

loadStatus();
loadEntries();
