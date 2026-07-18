const state = {
  mode: "precision",
  output: "",
  candidates: [],
  selected: null,
  reviews: new Map(),
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function setMode(mode) {
  state.mode = mode;
  $("precisionMode").classList.toggle("active", mode === "precision");
  $("recallMode").classList.toggle("active", mode === "recall");
  $("minScore").value = mode === "precision" ? "0.8" : "0.012";
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "--:--";
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remainingSeconds = total % 60;
  const mm = String(minutes).padStart(2, "0");
  const ss = String(remainingSeconds).padStart(2, "0");
  if (hours > 0) return `${hours}:${mm}:${ss}`;
  return `${mm}:${ss}`;
}

function formatVideoTime(seconds) {
  return formatDuration(Number(seconds));
}

function formatClipWindow(startSeconds, endSeconds) {
  return `${formatVideoTime(startSeconds)}-${formatVideoTime(endSeconds)}`;
}

function suspicionCategory(score) {
  const value = Number(score);
  if (!Number.isFinite(value)) return { label: "待复核目标", className: "low" };
  if (value >= 5.0) return { label: "高度疑似目标", className: "high" };
  if (value >= 1.0) return { label: "中等疑似目标", className: "medium" };
  return { label: "低疑似目标", className: "low" };
}

function renderProgress(payload) {
  const rawPercent = Number(payload.progress_percent || 0);
  const percent = Math.max(0, Math.min(100, Number.isFinite(rawPercent) ? rawPercent : 0));
  const rounded = Math.round(percent);
  $("progressBar").style.width = `${percent}%`;
  $("progressPercent").textContent = `${rounded}%`;
  const track = document.querySelector(".progress-track");
  if (track) track.setAttribute("aria-valuenow", String(rounded));

  const videoName = payload.current_video || (payload.running ? "准备扫描" : "未开始");
  const index = Number(payload.video_index || 0);
  const total = Number(payload.total_videos || 0);
  $("currentVideo").textContent = index > 0 && total > 0 ? `${videoName}  ${index}/${total}` : videoName;
  $("elapsedTime").textContent = formatDuration(Number(payload.elapsed_seconds || 0));
  const eta = payload.eta_seconds === null || payload.eta_seconds === undefined ? NaN : Number(payload.eta_seconds);
  $("etaTime").textContent = formatDuration(eta);
  $("frameProgress").textContent = `${Number(payload.processed_frames || 0)} / ${Number(payload.total_frames || 0)} 帧`;
}

function renderHealth(payload) {
  $("runState").textContent = payload.running ? "扫描中" : "待机";
  $("outputSummary").textContent = payload.last_output || state.output || "未生成";
  $("logView").textContent = (payload.logs || []).join("\n");
  renderProgress(payload);
  if (payload.dependencies) {
    $("dependencyList").innerHTML = payload.dependencies
      .map((dep) => `<div class="dep ${dep.ok ? "ok" : "bad"}"><span>${dep.name}</span><strong>${dep.ok ? "OK" : dep.detail}</strong></div>`)
      .join("");
  }
}

function mediaUrl(relpath) {
  return `/media/${encodeURIComponent(relpath).replaceAll("%2F", "/")}`;
}

function renderCandidates() {
  $("candidateCount").textContent = String(state.candidates.length);
  $("candidateGrid").innerHTML = state.candidates
    .map((candidate, index) => {
      const selected = state.selected === index ? " selected" : "";
      const review = state.reviews.get(candidate.candidate_id) || candidate.state || "unreviewed";
      const category = suspicionCategory(candidate.score);
      return `<article class="candidate-card${selected}" data-index="${index}">
        <img src="${mediaUrl(candidate.image_relpath)}" alt="">
        <div class="meta">
          <strong>${formatVideoTime(candidate.timestamp_seconds)} · ${candidate.score.toFixed(2)}</strong>
          <span class="score-badge ${category.className}">${category.label}</span>
          <span>${review}</span>
        </div>
      </article>`;
    })
    .join("");
  document.querySelectorAll(".candidate-card").forEach((card) => {
    card.addEventListener("click", () => selectCandidate(Number(card.dataset.index)));
  });
  if (state.selected === null && state.candidates.length) selectCandidate(0);
}

function selectCandidate(index) {
  state.selected = index;
  const candidate = state.candidates[index];
  const category = suspicionCategory(candidate.score);
  $("detailImage").src = mediaUrl(candidate.image_relpath);
  $("detailVideo").src = mediaUrl(candidate.clip_relpath);
  $("detailMeta").innerHTML = `
    <strong>${candidate.video}</strong><br>
    <span class="score-badge ${category.className}">${category.label}</span><br>
    时间 ${formatVideoTime(candidate.timestamp_seconds)}<br>
    片段 ${formatClipWindow(candidate.clip_start_seconds, candidate.clip_end_seconds)}<br>
    评分 ${candidate.score.toFixed(2)}<br>
    红像素 ${candidate.red_pixels} · 强度 ${candidate.red_strength.toFixed(1)}
  `;
  renderCandidates();
}

async function refreshHealth() {
  renderHealth(await api("/health"));
}

async function refreshResults() {
  const payload = await api("/results");
  state.output = payload.output || payload.last_output || state.output;
  state.candidates = payload.candidates || [];
  for (const candidate of state.candidates) {
    state.reviews.set(candidate.candidate_id, candidate.state || "unreviewed");
  }
  renderHealth(payload);
  renderCandidates();
}

async function startScan() {
  const payload = {
    source: $("sourcePath").value.trim(),
    output: $("outputPath").value.trim(),
    mode: state.mode,
    max_candidates: Number($("maxCandidates").value),
    min_score: Number($("minScore").value),
    min_red_pixels: Number($("minRedPixels").value),
    pre_seconds: Number($("preSeconds").value),
    post_seconds: Number($("postSeconds").value),
  };
  if (!payload.source) {
    alert("请先填写视频或文件夹路径");
    return;
  }
  const result = await api("/scan", { method: "POST", body: JSON.stringify(payload) });
  state.output = result.output;
  $("outputPath").value = result.output;
  await refreshHealth();
}

async function choosePath(kind, targetId) {
  // Prefer the native webview dialog (Windows/macOS/Linux) when running inside
  // pywebview. Falls back to the HTTP endpoint for plain-browser / CLI use.
  if (window.pywebview && window.pywebview.api && window.pywebview.api.choose_path) {
    try {
      const result = await window.pywebview.api.choose_path(kind);
      if (result && result.ok && result.path) {
        $(targetId).value = result.path;
      }
      return;
    } catch (error) {
      // fall through to the HTTP endpoint
    }
  }
  const result = await api("/choose-path", { method: "POST", body: JSON.stringify({ kind }) });
  if (result.ok && result.path) {
    $(targetId).value = result.path;
  }
}

async function saveReview() {
  if (!state.output) return;
  const reviews = Array.from(state.reviews.entries()).map(([candidate_id, reviewState]) => ({ candidate_id, state: reviewState }));
  await api("/review-state", { method: "POST", body: JSON.stringify({ output: state.output, reviews }) });
  await refreshResults();
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  if (target.id === "precisionMode") setMode("precision");
  if (target.id === "recallMode") setMode("recall");
  if (target.id === "chooseVideo") choosePath("video", "sourcePath").catch((error) => alert(error.message));
  if (target.id === "chooseSourceFolder") choosePath("source-folder", "sourcePath").catch((error) => alert(error.message));
  if (target.id === "chooseOutputFolder") choosePath("output-folder", "outputPath").catch((error) => alert(error.message));
  if (target.id === "startScan") startScan().catch((error) => alert(error.message));
  if (target.id === "cancelScan") api("/cancel", { method: "POST", body: "{}" }).then(refreshHealth);
  if (target.id === "saveReview") saveReview().catch((error) => alert(error.message));
  if (target.id === "openOutput" && state.output) api("/open-path", { method: "POST", body: JSON.stringify({ path: state.output }) });
  if (target.id === "openReport" && state.output) api("/open-path", { method: "POST", body: JSON.stringify({ path: `${state.output}/report.html` }) });
  if (target.dataset.state && state.selected !== null) {
    const candidate = state.candidates[state.selected];
    state.reviews.set(candidate.candidate_id, target.dataset.state);
    renderCandidates();
  }
});

setMode("precision");
refreshHealth();
setInterval(refreshHealth, 1500);
setInterval(refreshResults, 3500);
