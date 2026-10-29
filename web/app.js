// CapCut Keyframe Studio Pro - Interactive Frontend Application

let currentProjects = [];
let activeProject = null;
let selectedSegments = new Set(); // Stores composite keys: "trackIdx_segIdx"
let activePreset = "rhythmic_switch_entrance";
let currentBeats = [];
let audioFile = "";

// Preset definitions with default parameters
const PRESET_CONFIGS = {
  rhythmic_switch_entrance: {
    name: "Switch In (Vút Vào Đàn Hồi)",
    curveMode: "Cubic Ease-Out + Spring Overshoot",
    params: [
      { id: "direction", label: "Hướng bay vào (Direction)", type: "select", options: [
        { value: "up", text: "Dưới vút lên (như clip Halloween)" },
        { value: "down", text: "Trên vút xuống" },
        { value: "right", text: "Trái vút sang phải" },
        { value: "left", text: "Phải vút sang trái" }
      ], default: "up" },
      { id: "target_pos", label: "Vị trí dừng hiển thị (Target Pos)", type: "range", min: -1.0, max: 1.0, step: 0.05, default: -0.50, unit: "" },
      { id: "transition_duration_ms", label: "Thời gian vút vào (Duration)", type: "range", min: 100, max: 600, step: 25, default: 250, unit: " ms" },
      { id: "overshoot", label: "Độ nảy đàn hồi (Overshoot Bounce)", type: "range", min: 0.0, max: 0.25, step: 0.02, default: 0.08, unit: "" }
    ]
  },
  rhythmic_switch_exit: {
    name: "Switch Out (Vút Xuống Rời Khung)",
    curveMode: "Power-2.5 Accelerated Exit",
    params: [
      { id: "direction", label: "Hướng vút ra", type: "select", options: [
        { value: "down", text: "Vút xuống dưới (như clip Halloween)" },
        { value: "up", text: "Vút lên trên" },
        { value: "left", text: "Vút sang trái" },
        { value: "right", text: "Vút sang phải" }
      ], default: "down" },
      { id: "current_pos", label: "Vị trí đang đứng ban đầu", type: "range", min: -1.0, max: 1.0, step: 0.05, default: -0.50, unit: "" },
      { id: "transition_duration_ms", label: "Thời gian vút ra ở cuối clip", type: "range", min: 100, max: 500, step: 25, default: 200, unit: " ms" }
    ]
  },
  rhythmic_pulse_step: {
    name: "Rhythmic Step (Nhịp Đều 1s / 2s / Beat)",
    curveMode: "Periodic Step Pulse",
    params: [
      { id: "interval_seconds", label: "Chu kỳ nhịp (Interval)", type: "select", options: [
        { value: "0.5", text: "Mỗi 0.5 giây (Rất nhanh)" },
        { value: "0.8", text: "Mỗi 0.8 giây (Chuẩn clip Halloween)" },
        { value: "1.0", text: "Mỗi 1.0 giây (Nhịp 1s phổ biến)" },
        { value: "1.5", text: "Mỗi 1.5 giây" },
        { value: "2.0", text: "Mỗi 2.0 giây (Nhịp 2s)" },
        { value: "3.0", text: "Mỗi 3.0 giây" }
      ], default: "1.0" },
      { id: "motion_type", label: "Kiểu phản hồi nhịp", type: "select", options: [
        { value: "bounce", text: "Nảy phóng to (Scale Bounce)" },
        { value: "slide_up", text: "Nấc giật lên (Step Bump Up)" }
      ], default: "bounce" },
      { id: "bounce_scale", label: "Cường độ nảy (Scale Peak)", type: "range", min: 1.05, max: 1.40, step: 0.02, default: 1.15, unit: "x" },
      { id: "bounce_duration_ms", label: "Thời gian 1 lần nảy", type: "range", min: 80, max: 300, step: 10, default: 150, unit: " ms" }
    ]
  },
  smooth_zoom_in: {
    name: "Smooth Zoom In",
    curveMode: "FreeCurveInOut (Bezier)",
    params: [
      { id: "start_scale", label: "Tỷ lệ bắt đầu (Start Scale)", type: "range", min: 0.8, max: 2.0, step: 0.05, default: 1.0, unit: "x" },
      { id: "end_scale", label: "Tỷ lệ kết thúc (End Scale)", type: "range", min: 1.0, max: 3.0, step: 0.05, default: 1.25, unit: "x" },
      { id: "curve_mode", label: "Kiểu đường cong (Easing)", type: "select", options: [
        { value: "smooth", text: "Siêu mượt (Bezier Ease In-Out)" },
        { value: "linear", text: "Đường thẳng (Linear)" }
      ], default: "smooth" }
    ]
  },
  smooth_zoom_out: {
    name: "Smooth Zoom Out",
    curveMode: "FreeCurveInOut (Bezier)",
    params: [
      { id: "start_scale", label: "Tỷ lệ bắt đầu (Start Scale)", type: "range", min: 1.0, max: 3.0, step: 0.05, default: 1.25, unit: "x" },
      { id: "end_scale", label: "Tỷ lệ kết thúc (End Scale)", type: "range", min: 0.8, max: 2.0, step: 0.05, default: 1.0, unit: "x" },
      { id: "curve_mode", label: "Kiểu đường cong", type: "select", options: [
        { value: "smooth", text: "Siêu mượt (Bezier Ease In-Out)" },
        { value: "linear", text: "Đường thẳng (Linear)" }
      ], default: "smooth" }
    ]
  },
  camera_shake: {
    name: "Camera Shake (Rung Điện Ảnh)",
    curveMode: "Smooth Micro-Noise",
    params: [
      { id: "intensity", label: "Cường độ rung (Intensity)", type: "range", min: 0.01, max: 0.08, step: 0.005, default: 0.03, unit: "" },
      { id: "frequency_hz", label: "Tần số rung (Shakes/sec)", type: "range", min: 8, max: 24, step: 1, default: 14, unit: " Hz" },
      { id: "rotation_deg", label: "Biên độ xoay (Rotation)", type: "range", min: 0.0, max: 3.0, step: 0.2, default: 1.2, unit: "°" },
      { id: "decay", label: "Giảm dần về cuối clip (Decay)", type: "checkbox", default: false }
    ]
  },
  slow_pan: {
    name: "Slow Pan (Ken Burns)",
    curveMode: "FreeCurveInOut (Bezier)",
    params: [
      { id: "direction", label: "Hướng di chuyển (Direction)", type: "select", options: [
        { value: "right", text: "Trôi sang phải (Pan Right)" },
        { value: "left", text: "Trôi sang trái (Pan Left)" },
        { value: "up", text: "Trôi lên trên (Pan Up)" },
        { value: "down", text: "Trôi xuống dưới (Pan Down)" },
        { value: "diagonal_up_right", text: "Trôi chéo góc (Diagonal)" }
      ], default: "right" },
      { id: "pan_distance", label: "Khoảng cách trôi (Distance)", type: "range", min: 0.05, max: 0.35, step: 0.01, default: 0.15, unit: "" },
      { id: "zoom_scale", label: "Độ phóng to cơ bản (Base Zoom)", type: "range", min: 1.05, max: 1.35, step: 0.02, default: 1.15, unit: "x" }
    ]
  },
  elastic_bounce: {
    name: "Elastic Bounce (Nảy Đàn Hồi)",
    curveMode: "Multi-point Spring Easing",
    params: [
      { id: "peak_scale", label: "Độ nảy tối đa (Peak Scale)", type: "range", min: 1.1, max: 1.6, step: 0.02, default: 1.25, unit: "x" },
      { id: "bounce_duration_ms", label: "Thời gian nảy (Duration)", type: "range", min: 300, max: 1000, step: 50, default: 600, unit: " ms" },
      { id: "base_scale", label: "Tỷ lệ chuẩn (Base Scale)", type: "range", min: 0.8, max: 1.2, step: 0.05, default: 1.0, unit: "x" }
    ]
  },
  whip_pan: {
    name: "Whip Pan (Gạt Siêu Tốc)",
    curveMode: "Heavy Ease-In-Out Bezier",
    params: [
      { id: "direction", label: "Hướng gạt (Direction)", type: "select", options: [
        { value: "right", text: "Gạt sang phải (Right)" },
        { value: "left", text: "Gạt sang trái (Left)" },
        { value: "up", text: "Gạt lên trên (Up)" },
        { value: "down", text: "Gạt xuống dưới (Down)" }
      ], default: "right" },
      { id: "whip_duration_ms", label: "Thời gian vút (Duration)", type: "range", min: 200, max: 600, step: 25, default: 350, unit: " ms" },
      { id: "is_transition_out", label: "Thời điểm thực hiện", type: "select", options: [
        { value: "true", text: "Vút ra ở cuối clip (Transition Out)" },
        { value: "false", text: "Vút vào ở đầu clip (Transition In)" }
      ], default: "true" }
    ]
  },
  breathing_pulse: {
    name: "Breathing Pulse (Nhịp Thở)",
    curveMode: "Periodic Bezier Oscillation",
    params: [
      { id: "min_scale", label: "Tỷ lệ co nhỏ nhất (Min)", type: "range", min: 0.95, max: 1.05, step: 0.01, default: 1.0, unit: "x" },
      { id: "max_scale", label: "Tỷ lệ phồng lớn nhất (Max)", type: "range", min: 1.03, max: 1.20, step: 0.01, default: 1.08, unit: "x" },
      { id: "period_seconds", label: "Chu kỳ 1 nhịp thở (Period)", type: "range", min: 1.0, max: 4.0, step: 0.2, default: 2.0, unit: " s" }
    ]
  },
  fade_opacity: {
    name: "Fade Opacity (Hiện/Mờ Dần)",
    curveMode: "Alpha Bezier Easing",
    params: [
      { id: "fade_type", label: "Kiểu mờ (Mode)", type: "select", options: [
        { value: "in", text: "Hiện dần ở đầu clip (Fade In)" },
        { value: "out", text: "Mờ dần ở cuối clip (Fade Out)" },
        { value: "in_and_out", text: "Cả Hiện dần & Mờ dần (Both)" }
      ], default: "in" },
      { id: "fade_duration_ms", label: "Thời gian mờ (Duration)", type: "range", min: 200, max: 1500, step: 50, default: 500, unit: " ms" }
    ]
  }
};

// Initialize app when DOM loads
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadProjects();
  renderPresetParams();
  drawCurvePreview();
});

// Setup event listeners
function setupEventListeners() {
  // Navigation & Modals
  document.getElementById("btnRefresh").addEventListener("click", loadProjects);
  document.getElementById("btnSetDir").addEventListener("click", () => {
    document.getElementById("modalSetDir").classList.remove("hidden");
  });
  document.getElementById("btnCloseModalDir").addEventListener("click", () => {
    document.getElementById("modalSetDir").classList.add("hidden");
  });
  document.getElementById("btnConfirmSetDir").addEventListener("click", handleSetCustomDir);

  document.getElementById("btnHelp").addEventListener("click", () => {
    document.getElementById("modalHelp").classList.remove("hidden");
  });
  document.getElementById("btnCloseModalHelp").addEventListener("click", () => {
    document.getElementById("modalHelp").classList.add("hidden");
  });

  // Project search filter
  document.getElementById("projectSearch").addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    renderProjectList(currentProjects.filter(p => (p.display_name || p.folder_name).toLowerCase().includes(q)));
  });

  // Track clip selection helpers
  document.getElementById("btnSelectAllClips").addEventListener("click", () => {
    if (!activeProject) return;
    activeProject.tracks.forEach(track => {
      if (track.type === "video") {
        track.segments.forEach(seg => {
          selectedSegments.add(`${track.index}_${seg.index}`);
        });
      }
    });
    updateClipSelectionUI();
  });

  document.getElementById("btnDeselectAllClips").addEventListener("click", () => {
    selectedSegments.clear();
    updateClipSelectionUI();
  });

  // Studio tabs switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");

      // Auto-load audio beats when switching to BeatSync tab
      if (btn.dataset.tab === "tabBeatSync" && activeProject) {
        loadAudioBeats();
      }
      // Auto-load AI Frame Inspection when switching to AI Inspector tab
      if (btn.dataset.tab === "tabAIInspector" && activeProject) {
        loadAIFrameInspection();
      }
    });
  });

  // Preset Card Clicks
  document.querySelectorAll(".preset-card").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activePreset = card.dataset.preset;
      renderPresetParams();
      drawCurvePreview();
    });
  });

  // Apply Preset Button
  document.getElementById("btnApplyPreset").addEventListener("click", handleApplyPreset);

  // Beat Sync Mode Cards
  document.querySelectorAll(".effect-mode-card").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".effect-mode-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
    });
  });

  // Beat Sync Sliders
  document.getElementById("sliderBeatScale").addEventListener("input", (e) => {
    document.getElementById("beatScaleVal").textContent = `${e.target.value}x`;
  });
  document.getElementById("sliderBeatDur").addEventListener("input", (e) => {
    document.getElementById("beatDurVal").textContent = `${e.target.value} ms`;
  });

  // Beat source radio
  document.querySelectorAll("input[name='beatSource']").forEach(radio => {
    radio.addEventListener("change", (e) => {
      const bpmGroup = document.getElementById("bpmControlGroup");
      if (e.target.value === "bpm") {
        bpmGroup.classList.remove("hidden");
      } else {
        bpmGroup.classList.add("hidden");
      }
      loadAudioBeats();
    });
  });
  document.getElementById("inputBpm").addEventListener("input", loadAudioBeats);

  // Apply Beat Sync
  document.getElementById("btnApplyBeatSync").addEventListener("click", handleApplyBeatSync);

  // Batch source clip select
  document.getElementById("selectSourceClip").addEventListener("change", handleSourceClipSelect);
  document.getElementById("btnApplyBatch").addEventListener("click", handleApplyBatch);

  // Curve Tools
  document.getElementById("sliderSmoothFactor").addEventListener("input", (e) => {
    document.getElementById("smoothFactorVal").textContent = e.target.value;
  });
  document.getElementById("btnSmoothCurves").addEventListener("click", handleSmoothCurves);
  document.getElementById("btnShiftKeyframes").addEventListener("click", handleShiftKeyframes);

  // AI Frame Inspector controls
  document.getElementById("vpScrubber").addEventListener("input", (e) => {
    seekToFrame(parseInt(e.target.value));
  });
  document.getElementById("vpPrevFrame").addEventListener("click", () => {
    seekToFrame(currentFrameIndex - 1);
  });
  document.getElementById("vpNextFrame").addEventListener("click", () => {
    seekToFrame(currentFrameIndex + 1);
  });
  document.getElementById("vpPlayPause").addEventListener("click", togglePlayViewport);
  document.getElementById("btnReanalyzeFrames").addEventListener("click", loadAIFrameInspection);
  document.getElementById("btnAIFixAll").addEventListener("click", handleAIFixAll);
  document.getElementById("btnGenerateFilmstrip").addEventListener("click", handleGenerateFilmstrip);

  // Clear Keyframes
  document.getElementById("btnClearKeyframesPrompt").addEventListener("click", handleClearKeyframes);
  document.getElementById("btnOpenBackups").addEventListener("click", () => {
    document.querySelector("[data-tab='tabHistory']").click();
  });
}

// ==========================================
// API CALLS & DATA LOADING
// ==========================================

async function loadProjects() {
  const container = document.getElementById("projectList");
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Đang quét thư mục CapCut...</p>
    </div>
  `;

  try {
    const res = await fetch("/api/projects");
    const data = await res.json();
    if (data.status === "success") {
      currentProjects = data.projects || [];
      document.getElementById("projectCount").textContent = currentProjects.length;
      document.getElementById("statusIndicator").classList.remove("offline");
      document.getElementById("statusIndicator").classList.add("online");
      document.getElementById("statusText").textContent = `Đã kết nối CapCut (${currentProjects.length} dự án)`;

      renderProjectList(currentProjects);

      // Auto-select first project if none selected
      if (currentProjects.length > 0 && !activeProject) {
        selectProject(currentProjects[0].folder_name);
      }
    } else {
      showToast(data.message || "Lỗi khi quét thư mục", "error");
    }
  } catch (err) {
    document.getElementById("statusIndicator").classList.add("offline");
    document.getElementById("statusText").textContent = "Không tìm thấy thư mục CapCut";
    container.innerHTML = `<p class="p-3 text-muted text-sm">Không thể kết nối tới CapCut. Vui lòng bấm <strong>📁 Đổi thư mục</strong> để chọn đường dẫn dự án.</p>`;
  }
}

function renderProjectList(projects) {
  const container = document.getElementById("projectList");
  if (!projects || projects.length === 0) {
    container.innerHTML = `<p class="p-3 text-muted text-sm text-center">Không tìm thấy dự án nào.</p>`;
    return;
  }

  container.innerHTML = projects.map(p => {
    const isActive = activeProject && activeProject.folder_name === p.folder_name;
    const coverUrl = p.has_cover ? `/cover?name=${encodeURIComponent(p.folder_name)}` : '';
    const coverHtml = p.has_cover
      ? `<img src="${coverUrl}" class="project-thumb" alt="cover">`
      : `<div class="project-thumb flex items-center justify-center text-xl">🎬</div>`;

    return `
      <div class="project-card ${isActive ? 'active' : ''}" onclick="selectProject('${p.folder_name.replace(/'/g, "\\'")}')">
        ${coverHtml}
        <div class="project-meta">
          <div class="project-name" title="${p.display_name || p.folder_name}">${p.display_name || p.folder_name}</div>
          <div class="project-sub">
            <span>⏱️ ${p.duration_seconds}s • ${p.fps} fps</span>
            <span>📅 ${p.modified_time}</span>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

async function selectProject(folderName) {
  try {
    const res = await fetch(`/api/project?name=${encodeURIComponent(folderName)}`);
    const data = await res.json();
    if (data.status === "success") {
      activeProject = data.data;
      selectedSegments.clear();

      // Update project list active states
      document.querySelectorAll(".project-card").forEach(c => c.classList.remove("active"));
      renderProjectList(currentProjects);

      renderProjectWorkspace();
      populateSourceClipSelect();
      renderBackupList();
    }
  } catch (err) {
    showToast("Lỗi khi tải chi tiết dự án", "error");
  }
}

function renderProjectWorkspace() {
  document.getElementById("noProjectSelected").classList.add("hidden");
  const ws = document.getElementById("projectWorkspace");
  ws.classList.remove("hidden");

  document.getElementById("activeProjectTitle").textContent = activeProject.name || activeProject.folder_name;
  document.getElementById("metaDuration").textContent = `⏱️ ${activeProject.duration_seconds}s`;
  document.getElementById("metaFps").textContent = `🎬 ${activeProject.fps} FPS`;
  document.getElementById("metaTracks").textContent = `🎞️ ${activeProject.tracks.length} Tracks`;
  document.getElementById("backupBadge").textContent = (activeProject.backups || []).length;

  renderTracks();
  updateClipSelectionUI();
}

function renderTracks() {
  const container = document.getElementById("tracksContainer");
  if (!activeProject || !activeProject.tracks) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = activeProject.tracks.map(track => {
    const isVideo = track.type === "video";
    const typeLabel = isVideo ? "Video Track" : (track.type === "audio" ? "Audio Track" : "Text/Sticker Track");
    const badgeColor = isVideo ? "text-cyan" : (track.type === "audio" ? "text-purple" : "text-muted");

    const segmentsHtml = track.segments.map(seg => {
      const isSelected = selectedSegments.has(`${track.index}_${seg.index}`);
      const hasKf = seg.has_keyframes;
      let kfBadge = "";
      if (hasKf) {
        const props = seg.keyframes.map(k => k.property.replace("KFType", "")).join(", ");
        kfBadge = `<span class="segment-kf-badge" title="Đã có keyframe: ${props}">✨ ${props}</span>`;
      }

      return `
        <div class="segment-item ${isSelected ? 'selected' : ''}" onclick="toggleSegmentSelection(${track.index}, ${seg.index})">
          <div class="segment-top">
            <input type="checkbox" class="segment-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleSegmentSelection(${track.index}, ${seg.index})">
            <span class="segment-duration">${seg.duration_seconds}s</span>
          </div>
          <div class="segment-name" title="${seg.name}">${seg.name}</div>
          ${kfBadge}
        </div>
      `;
    }).join("");

    return `
      <div class="track-row">
        <div class="track-header">
          <span class="track-title ${badgeColor}">${typeLabel} ${track.index + 1} (${track.segments.length} clips)</span>
          ${isVideo ? `<button class="btn btn-xs btn-outline" onclick="selectTrackSegments(${track.index})">Chọn tất cả Track này</button>` : ''}
        </div>
        <div class="segments-list">
          ${segmentsHtml || '<p class="text-xs text-muted">Không có clip nào</p>'}
        </div>
      </div>
    `;
  }).join("");
}

function toggleSegmentSelection(trackIdx, segIdx) {
  const key = `${trackIdx}_${segIdx}`;
  if (selectedSegments.has(key)) {
    selectedSegments.delete(key);
  } else {
    selectedSegments.add(key);
  }
  updateClipSelectionUI();
}

function selectTrackSegments(trackIdx) {
  const track = activeProject.tracks.find(t => t.index === trackIdx);
  if (track) {
    track.segments.forEach(seg => {
      selectedSegments.add(`${trackIdx}_${seg.index}`);
    });
    updateClipSelectionUI();
  }
}

function updateClipSelectionUI() {
  const count = selectedSegments.size;
  document.getElementById("metaSelectedClips").textContent = `Đã chọn: ${count} clip${count !== 1 ? 's' : ''}`;
  document.getElementById("selectedCountBtn").textContent = count;
  document.getElementById("batchTargetCount").textContent = count;

  // Sync checkboxes and card selected classes
  document.querySelectorAll(".segment-item").forEach(item => {
    // Re-render tracks cleanly
  });
  renderTracks();
}

// ==========================================
// PRESET CONFIG RENDERING & CURVE PREVIEW
// ==========================================

function renderPresetParams() {
  const config = PRESET_CONFIGS[activePreset];
  if (!config) return;

  document.getElementById("currentPresetName").textContent = config.name;
  document.getElementById("curveTypeBadge").textContent = config.curveMode;

  const container = document.getElementById("presetParamsContainer");
  container.innerHTML = config.params.map(param => {
    if (param.type === "range") {
      return `
        <div class="slider-row mt-3">
          <div class="slider-header">
            <span>${param.label}:</span>
            <span id="val_${param.id}" class="slider-value">${param.default}${param.unit}</span>
          </div>
          <input type="range" id="param_${param.id}" min="${param.min}" max="${param.max}" step="${param.step}" value="${param.default}" class="range-slider" oninput="handleParamChange('${param.id}', this.value, '${param.unit}')">
        </div>
      `;
    } else if (param.type === "select") {
      const opts = param.options.map(o => `<option value="${o.value}" ${o.value === param.default ? 'selected' : ''}>${o.text}</option>`).join("");
      return `
        <div class="form-group mt-3">
          <label class="input-label text-sm text-muted">${param.label}:</label>
          <select id="param_${param.id}" class="select-box w-full mt-1" onchange="drawCurvePreview()">
            ${opts}
          </select>
        </div>
      `;
    } else if (param.type === "checkbox") {
      return `
        <div class="form-group mt-3">
          <label class="radio-label">
            <input type="checkbox" id="param_${param.id}" ${param.default ? 'checked' : ''} onchange="drawCurvePreview()">
            <span>${param.label}</span>
          </label>
        </div>
      `;
    }
  }).join("");
}

function handleParamChange(id, val, unit) {
  const el = document.getElementById(`val_${id}`);
  if (el) el.textContent = `${val}${unit}`;
  drawCurvePreview();
}

function getPresetCurrentParams() {
  const config = PRESET_CONFIGS[activePreset];
  if (!config) return {};

  const params = {};
  config.params.forEach(p => {
    const el = document.getElementById(`param_${p.id}`);
    if (el) {
      if (p.type === "checkbox") {
        params[p.id] = el.checked;
      } else if (p.type === "range") {
        params[p.id] = parseFloat(el.value);
      } else {
        params[p.id] = el.value;
      }
    }
  });
  return params;
}

// Canvas Visualizer
function drawCurvePreview() {
  const canvas = document.getElementById("curveCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  // Clear background
  ctx.fillStyle = "#0c0d11";
  ctx.fillRect(0, 0, w, h);

  // Draw grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += 30) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Draw curve according to active preset
  const params = getPresetCurrentParams();
  ctx.lineWidth = 3;
  ctx.strokeStyle = "#00f2fe";
  ctx.beginPath();

  const padX = 30;
  const padY = 20;
  const plotW = w - padX * 2;
  const plotH = h - padY * 2;

  if (activePreset === "rhythmic_switch_entrance") {
    // Entrance with overshoot and settling
    ctx.moveTo(padX, h - padY);
    const steps = 60;
    const peakX = padX + plotW * 0.4;
    const peakY = padY + plotH * 0.15; // overshoots past target
    const targetY = padY + plotH * 0.35; // settles at target
    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const x = padX + progress * plotW;
      let y;
      if (progress < 0.4) {
        const p = progress / 0.4;
        const eased = 1.0 - Math.pow(1.0 - p, 3);
        y = (h - padY) + (peakY - (h - padY)) * eased;
      } else if (progress < 0.6) {
        const p = (progress - 0.4) / 0.2;
        const eased = 0.5 * (1.0 - Math.cos(p * Math.PI));
        y = peakY + (targetY - peakY) * eased;
      } else {
        y = targetY;
      }
      ctx.lineTo(x, y);
    }
  } else if (activePreset === "rhythmic_switch_exit") {
    // Steady then steep plunge exit
    ctx.moveTo(padX, padY + plotH * 0.35);
    const steps = 60;
    const startExitX = padX + plotW * 0.6;
    const targetY = padY + plotH * 0.35;
    const endY = h - padY;
    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const x = padX + progress * plotW;
      let y;
      if (progress < 0.6) {
        y = targetY;
      } else {
        const p = (progress - 0.6) / 0.4;
        const eased = Math.pow(p, 2.5);
        y = targetY + (endY - targetY) * eased;
      }
      ctx.lineTo(x, y);
    }
  } else if (activePreset === "rhythmic_pulse_step") {
    // Repeating periodic pulses
    ctx.moveTo(padX, h - padY);
    const numPulses = 3;
    for (let p = 0; p < numPulses; p++) {
      const startX = padX + (p / numPulses) * plotW;
      const midX = startX + (0.5 / numPulses) * plotW * 0.4;
      const endX = startX + (1.0 / numPulses) * plotW * 0.4;
      const restX = padX + ((p + 1) / numPulses) * plotW;
      ctx.lineTo(startX, h - padY);
      ctx.lineTo(midX, padY + plotH * 0.2);
      ctx.lineTo(endX, h - padY);
      ctx.lineTo(restX, h - padY);
    }
  } else if (activePreset === "smooth_zoom_in" || activePreset === "smooth_zoom_out") {
    const isOut = activePreset === "smooth_zoom_out";
    const startY = isOut ? padY : h - padY;
    const endY = isOut ? h - padY : padY;

    if (params.curve_mode === "linear") {
      ctx.moveTo(padX, startY);
      ctx.lineTo(w - padX, endY);
    } else {
      // Bezier S-Curve with ease handles
      ctx.moveTo(padX, startY);
      ctx.bezierCurveTo(padX + plotW * 0.45, startY, w - padX - plotW * 0.45, endY, w - padX, endY);
    }
  } else if (activePreset === "camera_shake") {
    // Noise wave
    ctx.moveTo(padX, h / 2);
    const steps = 60;
    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const decay = params.decay ? (1.0 - progress) : 1.0;
      const freq = (params.frequency_hz || 14) * 0.5;
      const noise = (Math.sin(progress * Math.PI * freq) + Math.cos(progress * Math.PI * (freq * 1.6))) * 0.5;
      const x = padX + progress * plotW;
      const y = h / 2 - (noise * plotH * 0.4 * decay);
      ctx.lineTo(x, y);
    }
  } else if (activePreset === "elastic_bounce") {
    // Overshoot bounce
    ctx.moveTo(padX, h - padY);
    const steps = 80;
    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * 4;
      const factor = Math.exp(-t * 1.5) * Math.cos(t * 5.0);
      const val = 1.0 - factor;
      const x = padX + (i / steps) * plotW;
      const y = (h - padY) - val * plotH * 0.8;
      ctx.lineTo(x, y);
    }
  } else if (activePreset === "breathing_pulse") {
    // Sine wave
    ctx.moveTo(padX, h / 2);
    for (let i = 0; i <= plotW; i++) {
      const angle = (i / plotW) * Math.PI * 4;
      const y = h / 2 - Math.sin(angle) * (plotH * 0.35);
      ctx.lineTo(padX + i, y);
    }
  } else {
    // Default ease in-out
    ctx.moveTo(padX, h - padY);
    ctx.bezierCurveTo(padX + plotW * 0.4, h - padY, w - padX - plotW * 0.4, padY, w - padX, padY);
  }

  ctx.stroke();

  // Glow line shadow
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(0, 242, 254, 0.4)";
  ctx.stroke();
}

// ==========================================
// ACTIONS EXECUTION
// ==========================================

async function handleApplyPreset() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn ít nhất 1 clip trong danh sách!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const payload = {
    folder_name: activeProject.folder_name,
    targets: targets,
    preset: activePreset,
    params: getPresetCurrentParams(),
    replace: true
  };

  try {
    const res = await fetch("/api/apply_preset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Áp dụng keyframe thành công!", "success");
      // Reload project details to reflect new keyframes and backup
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi khi áp dụng keyframe", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối tới máy chủ", "error");
  }
}

// Beat Sync
async function loadAudioBeats() {
  if (!activeProject) return;

  const beatSource = document.querySelector("input[name='beatSource']:checked").value;
  const isBpm = beatSource === "bpm";
  const bpmVal = parseFloat(document.getElementById("inputBpm").value) || 128;

  try {
    const res = await fetch(`/api/audio_beats?name=${encodeURIComponent(activeProject.folder_name)}&use_bpm=${isBpm}&bpm=${bpmVal}`);
    const data = await res.json();
    if (data.status === "success") {
      currentBeats = data.beats_us || [];
      audioFile = data.audio_file || "";

      document.getElementById("beatCountDisplay").textContent = currentBeats.length;
      document.getElementById("audioSourceDisplay").textContent = audioFile;

      drawBeatWaveform();
    }
  } catch (err) {
    console.error("Audio beat load error", err);
  }
}

function drawBeatWaveform() {
  const canvas = document.getElementById("beatWaveformCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.fillStyle = "#0a0a0e";
  ctx.fillRect(0, 0, w, h);

  // Background baseline
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.beginPath();
  ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2);
  ctx.stroke();

  if (currentBeats.length === 0) return;

  const totalDur = activeProject ? (activeProject.duration_seconds * 1_000_000) : 15_000_000;

  // Draw simulated soundwave
  ctx.strokeStyle = "rgba(157, 78, 221, 0.35)";
  ctx.lineWidth = 2;
  for (let x = 0; x < w; x += 4) {
    const progress = x / w;
    const curTimeUs = progress * totalDur;
    // Check proximity to any beat
    let amp = 0.2;
    for (const b of currentBeats) {
      const dist = Math.abs(b - curTimeUs);
      if (dist < 150000) {
        amp = Math.max(amp, 0.9 - (dist / 150000) * 0.7);
      }
    }
    const waveH = amp * (h * 0.4);
    ctx.beginPath();
    ctx.moveTo(x, h / 2 - waveH);
    ctx.lineTo(x, h / 2 + waveH);
    ctx.stroke();
  }

  // Draw bright beat marker lines
  ctx.strokeStyle = "#00f2fe";
  ctx.lineWidth = 1.5;
  currentBeats.forEach(b => {
    const x = (b / totalDur) * w;
    ctx.beginPath();
    ctx.moveTo(x, 10);
    ctx.lineTo(x, h - 10);
    ctx.stroke();
  });
}

async function handleApplyBeatSync() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn các clip bạn muốn gắn nhịp!", "warning");
    return;
  }
  if (currentBeats.length === 0) {
    showToast("Chưa có dữ liệu beat. Vui lòng thử lại!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const activeModeCard = document.querySelector(".effect-mode-card.active");
  const mode = activeModeCard ? activeModeCard.dataset.beatMode : "bounce";

  const payload = {
    folder_name: activeProject.folder_name,
    targets: targets,
    beats_us: currentBeats,
    bounce_scale: parseFloat(document.getElementById("sliderBeatScale").value),
    bounce_duration_ms: parseInt(document.getElementById("sliderBeatDur").value),
    mode: mode,
    replace: true
  };

  try {
    const res = await fetch("/api/apply_beat_sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Đồng bộ nhịp thành công!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi khi đồng bộ nhịp", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Batch Replicate
function populateSourceClipSelect() {
  const sel = document.getElementById("selectSourceClip");
  sel.innerHTML = `<option value="">-- Chọn một clip mẫu có keyframe --</option>`;
  if (!activeProject) return;

  activeProject.tracks.forEach(t => {
    if (t.type === "video") {
      t.segments.forEach(s => {
        if (s.has_keyframes) {
          sel.innerHTML += `<option value="${t.index}_${s.index}">Track ${t.index + 1} - ${s.name} (${s.keyframes.length} nhóm KF)</option>`;
        }
      });
    }
  });
}

function handleSourceClipSelect(e) {
  const val = e.target.value;
  const box = document.getElementById("sourceKeyframeSummary");
  if (!val) {
    box.innerHTML = `<p class="text-muted text-sm">Chưa chọn clip nguồn</p>`;
    return;
  }

  const [tIdx, sIdx] = val.split("_").map(Number);
  const track = activeProject.tracks.find(t => t.index === tIdx);
  const seg = track ? track.segments[sIdx] : null;

  if (seg) {
    const kfList = seg.keyframes.map(k => `<li><strong>${k.property.replace("KFType", "")}</strong>: ${k.count} điểm keyframe</li>`).join("");
    box.innerHTML = `
      <div class="text-sm">
        <div class="text-cyan font-bold mb-1">Clip Mẫu: ${seg.name} (${seg.duration_seconds}s)</div>
        <ul class="list-disc pl-5 mt-1 space-y-1 text-xs text-muted">
          ${kfList}
        </ul>
      </div>
    `;
  }
}

async function handleApplyBatch() {
  if (!activeProject) return;
  const srcVal = document.getElementById("selectSourceClip").value;
  if (!srcVal) {
    showToast("Vui lòng chọn 1 clip mẫu có keyframe!", "warning");
    return;
  }
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn các clip mục tiêu nhận keyframe!", "warning");
    return;
  }

  const [srcT, srcS] = srcVal.split("_").map(Number);
  const destinations = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const repMode = document.querySelector("input[name='replicateMode']:checked").value;

  const payload = {
    folder_name: activeProject.folder_name,
    source: { track_index: srcT, segment_index: srcS },
    destinations: destinations,
    mode: repMode
  };

  try {
    const res = await fetch("/api/batch_replicate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Sao chép keyframe thành công!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi khi sao chép", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Curve Smoother
async function handleSmoothCurves() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn các clip cần làm mượt đường cong!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const smoothness = parseFloat(document.getElementById("sliderSmoothFactor").value);

  try {
    const res = await fetch("/api/smooth_curves", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        targets: targets,
        smoothness: smoothness
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Làm mượt đường cong thành công!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Shift Keyframes
async function handleShiftKeyframes() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn clip cần dịch chuyển thời gian!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const deltaMs = parseInt(document.getElementById("inputShiftMs").value) || 0;

  try {
    const res = await fetch("/api/shift_keyframes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        targets: targets,
        delta_ms: deltaMs
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Đã dịch chuyển keyframes!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Clear Keyframes
async function handleClearKeyframes() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn clip bạn muốn xóa keyframe!", "warning");
    return;
  }

  if (!confirm(`Bạn có chắc chắn muốn XÓA TOÀN BỘ keyframe của ${selectedSegments.size} clip đã chọn?`)) {
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  try {
    const res = await fetch("/api/clear_keyframes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        targets: targets,
        property: "all"
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Đã xóa keyframe!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Backups & Restore
function renderBackupList() {
  const container = document.getElementById("backupList");
  if (!activeProject || !activeProject.backups || activeProject.backups.length === 0) {
    container.innerHTML = `<p class="text-muted text-sm">Chưa có bản sao lưu nào cho dự án này.</p>`;
    return;
  }

  container.innerHTML = activeProject.backups.map(b => {
    return `
      <div class="backup-item">
        <div>
          <div class="font-medium text-sm">${b.filename}</div>
          <div class="text-xs text-muted">Thời gian: ${b.time}</div>
        </div>
        <button class="btn btn-sm btn-outline-warning" onclick="handleRestoreBackup('${b.filename}')">
          🔄 Khôi phục bản này
        </button>
      </div>
    `;
  }).join("");
}

async function handleRestoreBackup(filename) {
  if (!confirm(`Khôi phục dự án về bản sao lưu '${filename}'?`)) return;

  try {
    const res = await fetch("/api/restore_backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        backup_filename: filename
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast("Khôi phục dự án thành công!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi khi khôi phục", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

// Custom Directory
async function handleSetCustomDir() {
  const input = document.getElementById("inputCustomDir");
  const dir = input.value.trim();
  if (!dir) return;

  try {
    const res = await fetch("/api/set_draft_dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ directory: dir })
    });
    const data = await res.json();
    if (data.status === "success") {
      document.getElementById("modalSetDir").classList.add("hidden");
      showToast("Đã cập nhật thư mục CapCut!", "success");
      loadProjects();
    } else {
      showToast(data.message || "Thư mục không hợp lệ", "error");
    }
  } catch (err) {
    showToast("Lỗi khi kết nối tới máy chủ", "error");
  }
}

// ==========================================
// AI FRAME INSPECTOR & VIEWPORT SIMULATOR
// ==========================================

let aiInspectionReport = null;
let currentFrameIndex = 0;
let isPlayingPreview = false;
let previewInterval = null;

async function loadAIFrameInspection() {
  if (!activeProject) return;

  // Determine which clip to inspect: first selected clip, or first clip with keyframes
  let targetTrackIdx = 0;
  let targetSegIdx = 0;
  let found = false;

  if (selectedSegments.size > 0) {
    const firstKey = Array.from(selectedSegments)[0];
    const [t, s] = firstKey.split("_").map(Number);
    targetTrackIdx = t;
    targetSegIdx = s;
    found = true;
  } else {
    // Find first clip that has keyframes
    for (const t of activeProject.tracks) {
      if (t.type === "video") {
        for (const s of t.segments) {
          if (s.has_keyframes) {
            targetTrackIdx = t.index;
            targetSegIdx = s.index;
            found = true;
            break;
          }
        }
      }
      if (found) break;
    }
  }

  const track = activeProject.tracks.find(t => t.index === targetTrackIdx);
  const seg = track ? track.segments[targetSegIdx] : null;

  if (!seg) {
    document.getElementById("viewClipName").textContent = "Chưa có clip";
    return;
  }

  document.getElementById("viewClipName").textContent = `${seg.name} (${seg.duration_seconds}s)`;

  try {
    const res = await fetch("/api/ai_inspect_frames", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        track_index: targetTrackIdx,
        segment_index: targetSegIdx,
        fps: activeProject.fps || 30
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      aiInspectionReport = data;
      renderAIReport();
      seekToFrame(0);
    }
  } catch (err) {
    console.error("AI Inspect Error:", err);
  }
}

function renderAIReport() {
  if (!aiInspectionReport) return;

  const scoreEl = document.getElementById("aiScoreDisplay");
  const score = aiInspectionReport.ai_score;
  scoreEl.textContent = `${score}/100`;
  if (score >= 80) {
    scoreEl.className = "stat-number text-cyan";
  } else if (score >= 60) {
    scoreEl.className = "stat-number text-warning";
  } else {
    scoreEl.className = "stat-number text-danger";
  }

  document.getElementById("aiIssuesCountDisplay").textContent = aiInspectionReport.issues_count;

  const beatSync = aiInspectionReport.beat_sync || {};
  document.getElementById("aiBeatSyncDisplay").textContent = `${beatSync.score || '--'}%`;
  document.getElementById("aiBeatDesc").textContent = beatSync.description || "Chưa có dữ liệu beat.";

  // Render Issues list
  const issuesListEl = document.getElementById("aiIssuesList");
  if (!aiInspectionReport.issues || aiInspectionReport.issues.length === 0) {
    issuesListEl.innerHTML = `<p class="text-xs text-muted">✅ Không phát hiện chuyển động giật hoặc lỗi khung hình.</p>`;
  } else {
    issuesListEl.innerHTML = aiInspectionReport.issues.map(iss => {
      const isHigh = iss.severity === "high";
      return `
        <div class="issue-item ${isHigh ? 'high' : ''}" onclick="seekToFrame(${iss.frame})">
          <span>${isHigh ? '🚨' : '⚠️'}</span>
          <div>
            <strong>Frame ${iss.frame} (${iss.time_s}s):</strong> ${iss.description}
          </div>
        </div>
      `;
    }).join("");
  }

  // Configure Scrubber
  const scrubber = document.getElementById("vpScrubber");
  scrubber.min = 0;
  scrubber.max = aiInspectionReport.total_frames;
  scrubber.value = 0;

  // Render Frame Data Table
  const tbody = document.getElementById("frameTableBody");
  tbody.innerHTML = (aiInspectionReport.frames || []).map(f => {
    const isWarn = f.status === "warning";
    const statusText = isWarn ? `<span class="status-badge-warn">Cảnh báo</span>` : `<span class="status-badge-ok">Mượt</span>`;
    return `
      <tr id="row_frame_${f.frame_index}" onclick="seekToFrame(${f.frame_index})">
        <td><strong>#${f.frame_index}</strong></td>
        <td>${f.time_offset_s}s</td>
        <td>${f.position_x}</td>
        <td>${f.position_y}</td>
        <td>${f.scale}x</td>
        <td>${f.velocity}</td>
        <td>${statusText}</td>
      </tr>
    `;
  }).join("");
}

function seekToFrame(frameIdx) {
  if (!aiInspectionReport || !aiInspectionReport.frames) return;

  const maxF = aiInspectionReport.total_frames;
  currentFrameIndex = Math.max(0, min(maxF, frameIdx));

  document.getElementById("vpScrubber").value = currentFrameIndex;
  document.getElementById("vpFrameDisplay").textContent = `Frame: ${currentFrameIndex} / ${maxF}`;

  const frameData = aiInspectionReport.frames[currentFrameIndex];
  if (frameData) {
    document.getElementById("vpTimeDisplay").textContent = `⏱️ ${frameData.time_offset_s}s`;
    document.getElementById("vpPosDisplay").textContent = `X: ${frameData.position_x} | Y: ${frameData.position_y}`;
  }

  // Highlight table row
  document.querySelectorAll("#frameTableBody tr").forEach(r => r.classList.remove("active"));
  const row = document.getElementById(`row_frame_${currentFrameIndex}`);
  if (row) {
    row.classList.add("active");
    row.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  drawViewportFrame(currentFrameIndex);
}

function min(a, b) {
  return a < b ? a : b;
}

function togglePlayViewport() {
  const btn = document.getElementById("vpPlayPause");
  if (isPlayingPreview) {
    clearInterval(previewInterval);
    isPlayingPreview = false;
    btn.textContent = "▶ Phát Thử (30fps)";
  } else {
    isPlayingPreview = true;
    btn.textContent = "⏸️ Tạm Dừng";
    const fps = (activeProject && activeProject.fps) ? activeProject.fps : 30;
    const intervalMs = 1000 / fps;

    previewInterval = setInterval(() => {
      if (!aiInspectionReport) return;
      if (currentFrameIndex >= aiInspectionReport.total_frames) {
        currentFrameIndex = 0;
      } else {
        currentFrameIndex++;
      }
      seekToFrame(currentFrameIndex);
    }, intervalMs);
  }
}

function drawViewportFrame(frameIdx) {
  const canvas = document.getElementById("viewportCanvas");
  if (!canvas || !aiInspectionReport || !aiInspectionReport.frames) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  // Clear 9:16 mobile canvas screen
  ctx.fillStyle = "#09090d";
  ctx.fillRect(0, 0, w, h);

  // Draw rule of thirds / safe margins (Shorts/Reels overlay)
  ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
  ctx.lineWidth = 1;
  ctx.strokeRect(20, 40, w - 40, h - 80);
  ctx.beginPath();
  ctx.moveTo(w / 3, 0); ctx.lineTo(w / 3, h);
  ctx.moveTo((w * 2) / 3, 0); ctx.lineTo((w * 2) / 3, h);
  ctx.moveTo(0, h / 3); ctx.lineTo(w, h / 3);
  ctx.moveTo(0, (h * 2) / 3); ctx.lineTo(w, (h * 2) / 3);
  ctx.stroke();

  // Draw motion path trail of previous frames
  ctx.strokeStyle = "rgba(0, 242, 254, 0.35)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i <= frameIdx; i++) {
    const f = aiInspectionReport.frames[i];
    const px = (w / 2) + (f.position_x * (w / 2));
    const py = (h / 2) - (f.position_y * (h / 2));
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();

  // Draw current frame object
  const curF = aiInspectionReport.frames[frameIdx];
  if (!curF) return;

  const objX = (w / 2) + (curF.position_x * (w / 2));
  const objY = (h / 2) - (curF.position_y * (h / 2));
  const scale = curF.scale || 1.0;
  const rotRad = ((curF.rotation || 0.0) * Math.PI) / 180.0;
  const alpha = curF.alpha !== undefined ? curF.alpha : 1.0;

  ctx.save();
  ctx.translate(objX, objY);
  ctx.rotate(rotRad);
  ctx.scale(scale, scale);
  ctx.globalAlpha = alpha;

  // Draw simulated product/video element (Card)
  const cardW = 100;
  const cardH = 130;

  // Card shadow / glow
  ctx.shadowColor = curF.status === "warning" ? "rgba(245, 158, 11, 0.6)" : "rgba(0, 242, 254, 0.4)";
  ctx.shadowBlur = 12;

  // Card background
  const grad = ctx.createLinearGradient(-cardW / 2, -cardH / 2, cardW / 2, cardH / 2);
  grad.addColorStop(0, "#1f2230");
  grad.addColorStop(1, "#141620");
  ctx.fillStyle = grad;
  ctx.fillRect(-cardW / 2, -cardH / 2, cardW, cardH);

  // Card border
  ctx.strokeStyle = curF.status === "warning" ? "#f59e0b" : "#00f2fe";
  ctx.lineWidth = 2;
  ctx.strokeRect(-cardW / 2, -cardH / 2, cardW, cardH);

  // Mock product icon & label
  ctx.shadowBlur = 0;
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 24px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("👕", 0, -10);

  ctx.font = "10px sans-serif";
  ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
  ctx.fillText("Switch Item", 0, 20);

  ctx.font = "8px sans-serif";
  ctx.fillStyle = "rgba(0, 242, 254, 0.9)";
  ctx.fillText(`Scale: ${scale.toFixed(2)}x`, 0, 35);

  ctx.restore();

  // Draw crosshair at object center
  ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(objX - 6, objY); ctx.lineTo(objX + 6, objY);
  ctx.moveTo(objX, objY - 6); ctx.lineTo(objX, objY + 6);
  ctx.stroke();

  // Warning badge on viewport if frame has issue
  if (curF.status === "warning") {
    ctx.fillStyle = "rgba(245, 158, 11, 0.9)";
    ctx.font = "bold 11px sans-serif";
    ctx.fillText("⚠️ Cảnh báo gia tốc gắt!", w / 2, 30);
  }
}

async function handleAIFixAll() {
  if (!activeProject) return;

  const targets = [];
  if (selectedSegments.size > 0) {
    selectedSegments.forEach(k => {
      const [t, s] = k.split("_").map(Number);
      targets.push({ track_index: t, segment_index: s });
    });
  } else {
    showToast("Vui lòng tích chọn clip bạn muốn AI tối ưu!", "warning");
    return;
  }

  try {
    const res = await fetch("/api/ai_autofix_frames", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        targets: targets,
        fps: activeProject.fps || 30
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "AI đã tự động tối ưu hóa khung hình!", "success");
      loadAIFrameInspection();
    } else {
      showToast(data.message || "Lỗi khi tối ưu", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

async function handleGenerateFilmstrip() {
  if (!activeProject) return;

  let targetTrackIdx = 0;
  let targetSegIdx = 0;
  let found = false;

  if (selectedSegments.size > 0) {
    const firstKey = Array.from(selectedSegments)[0];
    const [t, s] = firstKey.split("_").map(Number);
    targetTrackIdx = t;
    targetSegIdx = s;
    found = true;
  } else {
    for (const t of activeProject.tracks) {
      if (t.type === "video" && t.segments.length > 0) {
        targetTrackIdx = t.index;
        targetSegIdx = 0;
        found = true;
        break;
      }
    }
  }

  const gridVal = document.getElementById("selectFilmstripGrid").value; // "5x2", "6x3", etc.
  const [cols, rows] = gridVal.split("x").map(Number);

  const btn = document.getElementById("btnGenerateFilmstrip");
  const origText = btn.textContent;
  btn.textContent = "⏳ Đang trích xuất...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/generate_filmstrip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        track_index: targetTrackIdx,
        segment_index: targetSegIdx,
        cols: cols,
        rows: rows,
        tile_width: 220
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      const container = document.getElementById("filmstripContainer");
      const img = document.getElementById("filmstripImage");
      const downloadBtn = document.getElementById("btnDownloadFilmstrip");
      const meta = document.getElementById("filmstripMeta");

      img.src = data.image_url;
      downloadBtn.href = data.image_url;
      meta.textContent = `${data.total_tiles} frames (${data.cols}x${data.rows}) • ${data.file_size_kb} KB • Độ dài: ${data.duration_seconds}s`;

      container.classList.remove("hidden");
      showToast(`Đã xuất 1 file PNG tổng hợp (${data.file_size_kb} KB)!`, "success");
    } else {
      showToast(data.message || "Lỗi khi tạo filmstrip", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  } finally {
    btn.textContent = origText;
    btn.disabled = false;
  }
}

function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  const msgEl = document.getElementById("toastMsg");
  msgEl.textContent = message;

  const iconEl = toast.querySelector(".toast-icon");
  if (type === "error") iconEl.textContent = "❌";
  else if (type === "warning") iconEl.textContent = "⚠️";
  else iconEl.textContent = "✅";

  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 3500);
}

