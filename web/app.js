// CapCut Keyframe Studio Pro - Interactive Frontend Application

let currentProjects = [];
let activeProject = null;
let selectedSegments = new Set(); // Stores composite keys: "trackIdx_segIdx"
let activePreset = "rhythmic_switch_entrance";
let activeSpeedPreset = "hero";
let currentBeats = [];
let audioFile = "";
let stabAnchorMode = "center";
let stabAnchorXRatio = 0.5;
let stabAnchorYRatio = 0.5;
let stabMode = "dead_lock";
let playheadTime = 0.0;
let isPlaying = false;
let playInterval = null;
let isLooping = true;
let previewMode = "composite"; // "composite" or "solo"
let trackVisibility = {}; // { trackIndex: boolean }
let timelineZoomPxPerSec = 75;
let cachedLayerImages = {};

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

  // Select only keyframed clips
  document.getElementById("btnTlSelectKeyframed")?.addEventListener("click", () => {
    if (!activeProject) return;
    selectedSegments.clear();
    activeProject.tracks.forEach(track => {
      track.segments.forEach(seg => {
        if (seg.has_keyframes) {
          selectedSegments.add(`${track.index}_${seg.index}`);
        }
      });
    });
    updateClipSelectionUI();
    showToast(`Đã chọn ${selectedSegments.size} clip có keyframe!`, "success");
  });

  // Timeline Zoom Controls
  const sliderZoom = document.getElementById("sliderTlZoom");
  if (sliderZoom) {
    sliderZoom.addEventListener("input", (e) => {
      timelineZoomPxPerSec = parseInt(e.target.value);
      renderCapCutTimeline();
      updatePlayheadPosition();
    });
  }

  document.getElementById("btnTlZoomOut")?.addEventListener("click", () => {
    if (sliderZoom) {
      sliderZoom.value = Math.max(25, parseInt(sliderZoom.value) - 15);
      timelineZoomPxPerSec = parseInt(sliderZoom.value);
      renderCapCutTimeline();
      updatePlayheadPosition();
    }
  });

  document.getElementById("btnTlZoomIn")?.addEventListener("click", () => {
    if (sliderZoom) {
      sliderZoom.value = Math.min(250, parseInt(sliderZoom.value) + 15);
      timelineZoomPxPerSec = parseInt(sliderZoom.value);
      renderCapCutTimeline();
      updatePlayheadPosition();
    }
  });

  document.getElementById("btnTlZoomFit")?.addEventListener("click", () => {
    if (!activeProject) return;
    const scroller = document.getElementById("timelineLanesScroller");
    const dur = activeProject.duration_seconds || 10;
    if (scroller && dur > 0) {
      const fitZoom = Math.max(25, Math.min(250, Math.floor((scroller.clientWidth - 40) / dur)));
      if (sliderZoom) sliderZoom.value = fitZoom;
      timelineZoomPxPerSec = fitZoom;
      renderCapCutTimeline();
      updatePlayheadPosition();
    }
  });

  // Master Preview Player Controls
  document.getElementById("btnPlayerPlayPause")?.addEventListener("click", togglePlayPause);
  document.getElementById("btnPlayerPrevFrame")?.addEventListener("click", stepPrevFrame);
  document.getElementById("btnPlayerNextFrame")?.addEventListener("click", stepNextFrame);
  document.getElementById("btnPlayerStart")?.addEventListener("click", () => seekToTime(0));
  document.getElementById("btnPlayerEnd")?.addEventListener("click", () => {
    if (activeProject) seekToTime(activeProject.duration_seconds || 0);
  });

  document.getElementById("btnPlayerLoop")?.addEventListener("click", () => {
    isLooping = !isLooping;
    const btn = document.getElementById("btnPlayerLoop");
    if (btn) btn.textContent = isLooping ? "🔁 Lặp: Bật" : "🔁 Lặp: Tắt";
  });

  document.getElementById("selectPreviewMode")?.addEventListener("change", (e) => {
    previewMode = e.target.value;
    updateMasterPreview();
  });

  document.getElementById("masterScrubber")?.addEventListener("input", (e) => {
    if (!activeProject) return;
    const dur = activeProject.duration_seconds || 10;
    const t = (parseFloat(e.target.value) / 1000.0) * dur;
    seekToTime(t);
  });

  // Timeline Ruler & Lanes Click/Drag to Scrub
  const lanesArea = document.getElementById("timelineLanesArea");
  if (lanesArea) {
    let isScrubbing = false;
    const scrubFromEvent = (e) => {
      if (!activeProject) return;
      const rect = lanesArea.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const dur = activeProject.duration_seconds || 10;
      const t = Math.max(0, Math.min(dur, clickX / timelineZoomPxPerSec));
      seekToTime(t);
    };

    lanesArea.addEventListener("mousedown", (e) => {
      // If clicking directly on a clip block, let clip selection handle it
      if (e.target.closest(".timeline-clip-block")) return;
      isScrubbing = true;
      scrubFromEvent(e);
    });
    window.addEventListener("mousemove", (e) => {
      if (isScrubbing) scrubFromEvent(e);
    });
    window.addEventListener("mouseup", () => {
      isScrubbing = false;
    });
  }

  // Global Keyboard Shortcuts (Space to play, Arrows to step frame)
  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
    if (e.code === "Space") {
      e.preventDefault();
      togglePlayPause();
    } else if (e.code === "ArrowLeft") {
      e.preventDefault();
      stepPrevFrame();
    } else if (e.code === "ArrowRight") {
      e.preventDefault();
      stepNextFrame();
    } else if (e.code === "Home") {
      e.preventDefault();
      seekToTime(0);
    } else if (e.code === "End" && activeProject) {
      e.preventDefault();
      seekToTime(activeProject.duration_seconds || 0);
    }
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
      // Speed ramp graph preview
      if (btn.dataset.tab === "tabSpeedRamp") {
        drawSpeedGraphPreview();
      }
      // Point-lock Stabilizer Canvas preview
      if (btn.dataset.tab === "tabStabilizer") {
        drawStabilizerCanvas();
      }
    });
  });

  // Preset Card Clicks (Motion presets)
  document.querySelectorAll(".preset-card[data-preset]").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card[data-preset]").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activePreset = card.dataset.preset;
      renderPresetParams();
      drawCurvePreview();
    });
  });

  // Speed Ramp Preset Clicks
  document.querySelectorAll(".preset-card[data-speed-preset]").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card[data-speed-preset]").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activeSpeedPreset = card.dataset.speedPreset;
      drawSpeedGraphPreview();
    });
  });

  // Speed Ramp Sliders & Controls
  document.getElementById("sliderFastSpeed").addEventListener("input", (e) => {
    document.getElementById("fastSpeedVal").textContent = `${e.target.value}x`;
    drawSpeedGraphPreview();
  });
  document.getElementById("sliderSlowSpeed").addEventListener("input", (e) => {
    document.getElementById("slowSpeedVal").textContent = `${e.target.value}x`;
    drawSpeedGraphPreview();
  });
  document.getElementById("chkSpeedBeatSync").addEventListener("change", drawSpeedGraphPreview);
  document.getElementById("btnApplySpeedRamp").addEventListener("click", handleApplySpeedRamp);
  document.getElementById("btnResetSpeed").addEventListener("click", handleResetSpeed);

  // Stabilizer Anchor Preset Buttons
  document.querySelectorAll(".anchor-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".anchor-btn").forEach(b => {
        b.classList.remove("btn-primary", "active");
        b.classList.add("btn-secondary");
      });
      btn.classList.remove("btn-secondary");
      btn.classList.add("btn-primary", "active");

      const mode = btn.dataset.anchor;
      stabAnchorMode = mode;
      if (mode === "center") {
        stabAnchorXRatio = 0.5;
        stabAnchorYRatio = 0.5;
      } else if (mode === "face") {
        stabAnchorXRatio = 0.5;
        stabAnchorYRatio = 0.30;
      } else if (mode === "chest") {
        stabAnchorXRatio = 0.5;
        stabAnchorYRatio = 0.55;
      }
      updateStabilizerAnchorDisplay();
      drawStabilizerCanvas();
    });
  });

  // Stabilizer Canvas Click & Drag Picker
  const stabCanvas = document.getElementById("stabilizerCanvas");
  if (stabCanvas) {
    let isStabDragging = false;
    const updateAnchorFromEvent = (e) => {
      const rect = stabCanvas.getBoundingClientRect();
      const scaleX = stabCanvas.width / rect.width;
      const scaleY = stabCanvas.height / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      stabAnchorXRatio = Math.max(0.05, Math.min(0.95, clickX / stabCanvas.width));
      stabAnchorYRatio = Math.max(0.05, Math.min(0.95, clickY / stabCanvas.height));
      stabAnchorMode = "custom";

      document.querySelectorAll(".anchor-btn").forEach(b => {
        b.classList.remove("btn-primary", "active");
        b.classList.add("btn-secondary");
        if (b.dataset.anchor === "custom") {
          b.classList.remove("btn-secondary");
          b.classList.add("btn-primary", "active");
        }
      });

      updateStabilizerAnchorDisplay();
      drawStabilizerCanvas();
    };

    stabCanvas.addEventListener("mousedown", (e) => {
      isStabDragging = true;
      updateAnchorFromEvent(e);
    });
    window.addEventListener("mousemove", (e) => {
      if (isStabDragging) updateAnchorFromEvent(e);
    });
    window.addEventListener("mouseup", () => {
      isStabDragging = false;
    });
  }

  // Reset Anchor Button
  document.getElementById("btnResetAnchor").addEventListener("click", () => {
    stabAnchorMode = "center";
    stabAnchorXRatio = 0.5;
    stabAnchorYRatio = 0.5;
    document.querySelectorAll(".anchor-btn").forEach(b => {
      b.classList.remove("btn-primary", "active");
      b.classList.add("btn-secondary");
      if (b.dataset.anchor === "center") {
        b.classList.remove("btn-secondary");
        b.classList.add("btn-primary", "active");
      }
    });
    updateStabilizerAnchorDisplay();
    drawStabilizerCanvas();
  });

  // Stabilizer Mode Cards
  document.querySelectorAll(".stab-mode-card").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".stab-mode-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      stabMode = card.dataset.stabMode;
      const winGroup = document.getElementById("stabSmoothWindowGroup");
      if (stabMode === "smooth") {
        winGroup.classList.remove("hidden");
      } else {
        winGroup.classList.add("hidden");
      }
    });
  });

  // Stabilizer Sliders
  document.getElementById("sliderStabSmoothWin").addEventListener("input", (e) => {
    document.getElementById("stabSmoothWinVal").textContent = `${e.target.value} frames`;
  });
  document.getElementById("sliderStabMinZoom").addEventListener("input", (e) => {
    document.getElementById("stabMinZoomVal").textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
  });

  // Apply Stabilizer Button
  document.getElementById("btnApplyStabilizer").addEventListener("click", handleApplyStabilizer);

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

  // Initialize track visibility for all tracks
  activeProject.tracks.forEach(t => {
    if (trackVisibility[t.index] === undefined) {
      trackVisibility[t.index] = true;
    }
  });

  // Aspect ratio badge
  const aspectBadge = document.getElementById("previewAspectBadge");
  if (aspectBadge) {
    aspectBadge.textContent = `${activeProject.canvas_width || 1080}x${activeProject.canvas_height || 1920}`;
  }

  // Duration display in player
  const totalTimeEl = document.getElementById("playerTotalTime");
  if (totalTimeEl) totalTimeEl.textContent = `⏱️ ${formatTimecode(activeProject.duration_seconds || 0)}`;

  renderCapCutTimeline();
  updateMasterPreview();
  updateClipSelectionUI();
}

function renderCapCutTimeline() {
  if (!activeProject || !activeProject.tracks) return;

  const totalDur = activeProject.duration_seconds || 10.0;
  const lanesWidth = Math.max(900, Math.ceil(totalDur * timelineZoomPxPerSec) + 80);

  // Set lanes area width
  const lanesArea = document.getElementById("timelineLanesArea");
  if (lanesArea) {
    lanesArea.style.width = lanesWidth + "px";
  }

  // Badges
  const trackCountBadge = document.getElementById("timelineTrackCountBadge");
  if (trackCountBadge) trackCountBadge.textContent = `${activeProject.tracks.length} Tracks`;

  let totalClips = 0;
  activeProject.tracks.forEach(t => totalClips += t.segments.length);
  const clipCountBadge = document.getElementById("timelineClipCountBadge");
  if (clipCountBadge) clipCountBadge.textContent = `${totalClips} clips`;

  // Draw Time Ruler Canvas
  const rulerCanvas = document.getElementById("timelineRulerCanvas");
  if (rulerCanvas) {
    rulerCanvas.width = lanesWidth;
    rulerCanvas.height = 28;
    const ctx = rulerCanvas.getContext("2d");
    ctx.clearRect(0, 0, lanesWidth, 28);

    // Ruler background
    ctx.fillStyle = "#101016";
    ctx.fillRect(0, 0, lanesWidth, 28);

    // Minor ticks (every 0.2s or 0.5s) and Major ticks (every 1.0s)
    const tickStep = timelineZoomPxPerSec > 110 ? 0.2 : (timelineZoomPxPerSec > 50 ? 0.5 : 1.0);
    const numTicks = Math.ceil(totalDur / tickStep);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
    ctx.font = "9px Inter, sans-serif";
    ctx.textAlign = "left";

    for (let i = 0; i <= numTicks; i++) {
      const t = i * tickStep;
      if (t > totalDur) break;
      const x = Math.round(t * timelineZoomPxPerSec);
      const isMajor = Math.abs(t - Math.round(t)) < 0.001;

      ctx.beginPath();
      if (isMajor) {
        ctx.moveTo(x, 10);
        ctx.lineTo(x, 28);
        ctx.stroke();
        ctx.fillText(`${Math.round(t)}s`, x + 3, 22);
      } else {
        ctx.moveTo(x, 18);
        ctx.lineTo(x, 28);
        ctx.stroke();
      }
    }

    // Draw Gold Beat Markers if beats are loaded
    if (currentBeats && currentBeats.length > 0) {
      ctx.fillStyle = "#f5a623";
      currentBeats.forEach(beatUs => {
        const beatSec = beatUs / 1000000.0;
        const bx = beatSec * timelineZoomPxPerSec;
        if (bx <= lanesWidth) {
          ctx.beginPath();
          ctx.moveTo(bx, 0);
          ctx.lineTo(bx - 3, 6);
          ctx.lineTo(bx + 3, 6);
          ctx.closePath();
          ctx.fill();
        }
      });
    }
  }

  // Render Track Headers Column
  const headersCol = document.getElementById("timelineTrackHeaders");
  if (headersCol) {
    const headersHtml = activeProject.tracks.map(track => {
      const isVideo = track.type === "video";
      const icon = isVideo ? "🎬" : (track.type === "audio" ? "🎵" : (track.type === "sticker" ? "🏷️" : "🎨"));
      const badge = isVideo ? `V${track.index}` : (track.type === "audio" ? `A${track.index}` : `T${track.index}`);
      const isVisible = trackVisibility[track.index] !== false;

      return `
        <div class="timeline-track-header-row">
          <div class="track-header-info">
            <span class="font-bold ${isVideo ? 'text-cyan' : (track.type === 'audio' ? 'text-purple' : 'text-muted')}">${icon} ${badge}</span>
            <span class="text-xs text-muted" title="${track.type} track (${track.segments.length} clips)">(${track.segments.length})</span>
          </div>
          <div class="track-header-actions">
            <button class="btn-eye-toggle ${isVisible ? 'active' : ''}" onclick="toggleTrackVisibility(${track.index})" title="${isVisible ? 'Ẩn lớp này khỏi Preview' : 'Hiện lớp này'}">
              ${isVisible ? '👁️' : '👁️‍🗨️'}
            </button>
            ${isVideo ? `<button class="btn btn-xs btn-outline py-0 px-1 text-xs" onclick="selectTrackSegments(${track.index})" title="Chọn tất cả clip trong Track này">Chọn</button>` : ''}
          </div>
        </div>
      `;
    }).join("");

    headersCol.innerHTML = `
      <div class="timeline-ruler-header">
        <span>Track / Layer</span>
      </div>
      ${headersHtml}
    `;
  }

  // Render Track Lanes Stack
  const lanesStack = document.getElementById("timelineLanesStack");
  if (lanesStack) {
    const lanesHtml = activeProject.tracks.map(track => {
      const clipsHtml = track.segments.map(seg => {
        const isSelected = selectedSegments.has(`${track.index}_${seg.index}`);
        const leftPx = Math.round(seg.start_seconds * timelineZoomPxPerSec);
        const widthPx = Math.max(24, Math.round(seg.duration_seconds * timelineZoomPxPerSec));

        // Keyframe Diamonds HTML
        let kfDiamondsHtml = "";
        if (seg.has_keyframes && seg.raw_common_keyframes) {
          const offsets = new Set();
          seg.raw_common_keyframes.forEach(g => {
            (g.keyframe_list || []).forEach(k => offsets.add(k.time_offset));
          });
          offsets.forEach(offUs => {
            const relSec = offUs / 1000000.0;
            const pct = Math.max(0, Math.min(100, (relSec / seg.duration_seconds) * 100));
            kfDiamondsHtml += `<span class="timeline-kf-diamond" style="left: ${pct}%;" title="Keyframe lúc ${(seg.start_seconds + relSec).toFixed(3)}s">◆</span>`;
          });
        }

        // Mini thumbnail on clip block
        let thumbHtml = "";
        if (seg.file_path) {
          const thumbUrl = `/api/media_frame?path=${encodeURIComponent(seg.file_path)}&t=0.0&w=64&h=64`;
          thumbHtml = `<img src="${thumbUrl}" class="clip-mini-thumb" loading="lazy" onerror="this.style.display='none'">`;
        }

        const speedTag = (seg.speed && seg.speed !== 1.0) ? `<span class="badge-mini text-purple">⚡${seg.speed}x</span>` : "";

        return `
          <div class="timeline-clip-block track-${track.type} ${isSelected ? 'selected' : ''} ${seg.has_keyframes ? 'has-kf' : ''}"
               style="left: ${leftPx}px; width: ${widthPx}px;"
               onclick="toggleSegmentSelection(${track.index}, ${seg.index})"
               title="${seg.name} [${seg.start_seconds}s - ${seg.end_seconds}s]${seg.has_keyframes ? ' (Có Keyframe)' : ''}">
            ${thumbHtml}
            <div class="clip-info-text">
              <span class="clip-title">${seg.name}</span>
              <span class="clip-duration-tag">${seg.duration_seconds}s ${speedTag}</span>
            </div>
            ${kfDiamondsHtml}
          </div>
        `;
      }).join("");

      return `
        <div class="timeline-lane-row" style="width: ${lanesWidth}px;">
          ${clipsHtml}
        </div>
      `;
    }).join("");

    lanesStack.innerHTML = lanesHtml;
  }

  updatePlayheadPosition();
}

function toggleTrackVisibility(trackIdx) {
  trackVisibility[trackIdx] = !(trackVisibility[trackIdx] !== false);
  renderCapCutTimeline();
  updateMasterPreview();
}

function updateMasterPreview() {
  if (!activeProject) return;

  const canvas = document.getElementById("masterPreviewCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const cw = canvas.width;
  const ch = canvas.height;

  // Background
  ctx.fillStyle = "#0a0a0f";
  ctx.fillRect(0, 0, cw, ch);

  // Find active segments at playheadTime
  const activeSegments = [];
  const tracks = activeProject.tracks || [];

  tracks.forEach(track => {
    // If track is hidden by user, skip it
    if (trackVisibility[track.index] === false) return;

    for (const seg of track.segments) {
      if (seg.start_seconds <= playheadTime && playheadTime <= seg.end_seconds) {
        activeSegments.push({ track, seg });
        break;
      }
    }
  });

  // Render Active Layers Chips
  const chipsContainer = document.getElementById("activeLayersChips");
  const countBadge = document.getElementById("activeLayersCount");
  if (chipsContainer) {
    if (activeSegments.length === 0) {
      chipsContainer.innerHTML = `<span class="text-muted text-xs">Không có layer nào tại thời điểm này</span>`;
      if (countBadge) countBadge.textContent = "0 layers";
    } else {
      if (countBadge) countBadge.textContent = `${activeSegments.length} layers active`;
      chipsContainer.innerHTML = activeSegments.map(({ track, seg }) => {
        const isVideo = track.type === "video";
        const icon = isVideo ? "🎬" : (track.type === "audio" ? "🎵" : "🏷️");
        const badge = isVideo ? `V${track.index}` : `A${track.index}`;
        const isSelected = selectedSegments.has(`${track.index}_${seg.index}`);
        const kfTag = seg.has_keyframes ? `<span class="segment-kf-badge-mini">◆ KFs</span>` : "";

        return `
          <div class="layer-chip ${isSelected ? 'selected' : ''}" onclick="toggleSegmentSelection(${track.index}, ${seg.index})">
            <span class="layer-chip-badge">${icon} ${badge}</span>
            <span>${seg.name}</span>
            ${kfTag}
          </div>
        `;
      }).join("");
    }
  }

  // Draw Visual Layers onto Canvas from bottom layer (Track 0) to top layer
  activeSegments.forEach(({ track, seg }) => {
    if (track.type !== "video" && track.type !== "sticker") return;

    // If in Solo mode, only draw if this segment is selected
    if (previewMode === "solo" && !selectedSegments.has(`${track.index}_${seg.index}`)) {
      return;
    }

    if (!seg.file_path) return;

    const relSec = Math.max(0, playheadTime - seg.start_seconds);
    const transform = getSegmentTransformAt(seg, relSec);

    const screenX = cw / 2 + transform.posX * (cw / 2);
    const screenY = ch / 2 - transform.posY * (ch / 2);

    ctx.save();
    ctx.translate(screenX, screenY);
    ctx.scale(transform.scaleX, transform.scaleX);
    if (transform.rot) {
      ctx.rotate((transform.rot * Math.PI) / 180);
    }

    const srcStartSec = seg.source_start_seconds || 0;
    const isMp4 = seg.file_path.toLowerCase().endsWith(".mp4") || seg.file_path.toLowerCase().endsWith(".mov");
    const srcOffsetSec = isMp4 ? Math.max(0, (relSec * (seg.speed || 1.0)) + srcStartSec) : 0;
    const imgUrl = `/api/media_frame?path=${encodeURIComponent(seg.file_path)}&t=${srcOffsetSec.toFixed(2)}&w=360&h=640`;

    let img = cachedLayerImages[imgUrl];
    if (!img) {
      img = new Image();
      img.src = imgUrl;
      img.onload = () => {
        if (!isPlaying) updateMasterPreview();
      };
      img.onerror = () => {
        if (srcOffsetSec > 0) {
          const fbUrl = `/api/media_frame?path=${encodeURIComponent(seg.file_path)}&t=0.00&w=360&h=640`;
          let fbImg = cachedLayerImages[fbUrl];
          if (!fbImg) {
            fbImg = new Image();
            fbImg.src = fbUrl;
            fbImg.onload = () => { if (!isPlaying) updateMasterPreview(); };
            cachedLayerImages[fbUrl] = fbImg;
          }
        }
      };
      cachedLayerImages[imgUrl] = img;
    }

    if (img.complete && img.naturalWidth > 0) {
      const imgAspect = img.naturalWidth / img.naturalHeight;
      const canvasAspect = cw / ch;
      let drawW = cw;
      let drawH = ch;

      if (Math.abs(imgAspect - canvasAspect) < 0.05) {
        drawW = cw;
        drawH = ch;
      } else if (imgAspect > canvasAspect) {
        drawW = cw;
        drawH = cw / imgAspect;
      } else {
        drawH = ch;
        drawW = ch * imgAspect;
      }

      ctx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH);
    } else {
      ctx.fillStyle = "rgba(0, 242, 254, 0.05)";
      ctx.fillRect(-cw / 2, -ch / 2, cw, ch);
      ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`⏳ Đang nạp ${seg.name.substring(0, 20)}...`, 0, 0);
    }
    ctx.restore();
  });

  // Timecode and Scrubber updates
  const dur = activeProject.duration_seconds || 10.0;
  const fps = activeProject.fps || 30;
  const curFrame = Math.round(playheadTime * fps);
  const totalFrames = Math.round(dur * fps);

  const curTimeEl = document.getElementById("playerCurrentTime");
  if (curTimeEl) curTimeEl.textContent = `⏱️ ${formatTimecode(playheadTime)}`;

  const frameNumEl = document.getElementById("playerFrameNumber");
  if (frameNumEl) frameNumEl.textContent = `Frame ${curFrame} / ${totalFrames}`;

  const overlayText = document.getElementById("masterPreviewOverlayText");
  if (overlayText) overlayText.textContent = formatTimecode(playheadTime);

  const scrubber = document.getElementById("masterScrubber");
  if (scrubber && dur > 0) {
    scrubber.value = Math.round((playheadTime / dur) * 1000);
  }

  updatePlayheadPosition();
}

function getSegmentTransformAt(seg, relTimeSec) {
  let posX = 0.0;
  let posY = 0.0;
  let scaleX = 1.0;
  let rot = 0.0;

  if (!seg.raw_common_keyframes || !Array.isArray(seg.raw_common_keyframes)) {
    return { posX, posY, scaleX, rot };
  }

  const relTimeUs = Math.round(relTimeSec * 1_000_000);

  for (const group of seg.raw_common_keyframes) {
    const ptype = group.property_type;
    const list = group.keyframe_list || [];
    if (!list.length) continue;

    let val = list[0].values?.[0] ?? 0;
    if (relTimeUs <= list[0].time_offset) {
      val = list[0].values?.[0] ?? 0;
    } else if (relTimeUs >= list[list.length - 1].time_offset) {
      val = list[list.length - 1].values?.[0] ?? 0;
    } else {
      for (let i = 0; i < list.length - 1; i++) {
        const k0 = list[i];
        const k1 = list[i + 1];
        if (k0.time_offset <= relTimeUs && relTimeUs <= k1.time_offset) {
          const deltaT = k1.time_offset - k0.time_offset;
          const prog = deltaT > 0 ? (relTimeUs - k0.time_offset) / deltaT : 0;
          const v0 = k0.values?.[0] ?? 0;
          const v1 = k1.values?.[0] ?? 0;
          const eased = 0.5 * (1.0 - Math.cos(prog * Math.PI));
          val = v0 + (v1 - v0) * eased;
          break;
        }
      }
    }

    if (ptype === "KFTypePositionX") posX = val;
    else if (ptype === "KFTypePositionY") posY = val;
    else if (ptype === "KFTypeScaleX") scaleX = val;
    else if (ptype === "KFTypeRotation") rot = val;
  }

  return { posX, posY, scaleX, rot };
}

function formatTimecode(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

function togglePlayPause() {
  if (!activeProject) return;
  isPlaying = !isPlaying;
  const btn = document.getElementById("btnPlayerPlayPause");

  if (isPlaying) {
    if (btn) btn.textContent = "⏸ Tạm Dừng";
    const fps = activeProject.fps || 30;
    const intervalMs = Math.round(1000 / fps);
    playInterval = setInterval(() => {
      const dur = activeProject.duration_seconds || 10.0;
      playheadTime += 1.0 / fps;
      if (playheadTime >= dur) {
        if (isLooping) {
          playheadTime = 0.0;
        } else {
          playheadTime = dur;
          togglePlayPause();
          return;
        }
      }
      updateMasterPreview();
    }, intervalMs);
  } else {
    if (btn) btn.textContent = "▶ Phát";
    if (playInterval) {
      clearInterval(playInterval);
      playInterval = null;
    }
  }
}

function stepPrevFrame() {
  if (!activeProject) return;
  const fps = activeProject.fps || 30;
  seekToTime(Math.max(0, playheadTime - 1.0 / fps));
}

function stepNextFrame() {
  if (!activeProject) return;
  const fps = activeProject.fps || 30;
  const dur = activeProject.duration_seconds || 10.0;
  seekToTime(Math.min(dur, playheadTime + 1.0 / fps));
}

function seekToTime(t) {
  if (!activeProject) return;
  const dur = activeProject.duration_seconds || 10.0;
  playheadTime = Math.max(0, Math.min(dur, t));
  updateMasterPreview();
}

function updatePlayheadPosition() {
  const line = document.getElementById("timelinePlayheadLine");
  if (line) {
    const x = Math.round(playheadTime * timelineZoomPxPerSec);
    line.style.transform = `translateX(${x}px)`;
  }
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

  renderCapCutTimeline();
  updateMasterPreview();
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

function drawSpeedGraphPreview() {
  const canvas = document.getElementById("speedGraphCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.fillStyle = "#0a0a0e";
  ctx.fillRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 45) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += 26) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Draw 1.0x baseline
  const base1xY = h - 25;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(0, base1xY);
  ctx.lineTo(w, base1xY);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.font = "10px sans-serif";
  ctx.fillText("1.0x Chuẩn", 10, base1xY - 4);

  const fastVal = parseFloat(document.getElementById("sliderFastSpeed").value) || 5.0;
  const slowVal = parseFloat(document.getElementById("sliderSlowSpeed").value) || 0.4;
  const isBeatSync = document.getElementById("chkSpeedBeatSync").checked;

  const padX = 25;
  const plotW = w - padX * 2;
  const plotH = h - 45;

  ctx.lineWidth = 3;
  ctx.strokeStyle = "#9d4edd";
  ctx.beginPath();

  function speedToY(spd) {
    // Logarithmic scale so slow-mo (0.2x) and fast (8x) are both visible
    const norm = (Math.log(Math.max(0.05, spd)) - Math.log(0.1)) / (Math.log(10.0) - Math.log(0.1));
    return (h - 15) - norm * plotH;
  }

  if (isBeatSync) {
    ctx.moveTo(padX, speedToY(fastVal));
    const dips = 3;
    for (let i = 0; i < dips; i++) {
      const bx = padX + ((i + 0.5) / dips) * plotW;
      const wDip = (plotW / dips) * 0.25;
      ctx.lineTo(bx - wDip, speedToY(fastVal));
      ctx.lineTo(bx, speedToY(slowVal));
      ctx.lineTo(bx + wDip, speedToY(fastVal));
    }
    ctx.lineTo(w - padX, speedToY(fastVal));
  } else if (activeSpeedPreset === "hero") {
    ctx.moveTo(padX, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.3, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.45, speedToY(slowVal));
    ctx.lineTo(padX + plotW * 0.65, speedToY(slowVal));
    ctx.lineTo(padX + plotW * 0.78, speedToY(fastVal));
    ctx.lineTo(w - padX, speedToY(fastVal));
  } else if (activeSpeedPreset === "bullet") {
    ctx.moveTo(padX, speedToY(1.0));
    ctx.lineTo(padX + plotW * 0.35, speedToY(1.0));
    ctx.lineTo(padX + plotW * 0.4, speedToY(slowVal * 0.5));
    ctx.lineTo(padX + plotW * 0.6, speedToY(slowVal * 0.5));
    ctx.lineTo(padX + plotW * 0.65, speedToY(1.0));
    ctx.lineTo(w - padX, speedToY(1.0));
  } else if (activeSpeedPreset === "flash_in") {
    ctx.moveTo(padX, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.25, speedToY(fastVal));
    ctx.bezierCurveTo(padX + plotW * 0.45, speedToY(fastVal), padX + plotW * 0.45, speedToY(1.0), padX + plotW * 0.6, speedToY(1.0));
    ctx.lineTo(w - padX, speedToY(1.0));
  } else if (activeSpeedPreset === "flash_out") {
    ctx.moveTo(padX, speedToY(1.0));
    ctx.lineTo(padX + plotW * 0.5, speedToY(1.0));
    ctx.bezierCurveTo(padX + plotW * 0.65, speedToY(1.0), padX + plotW * 0.65, speedToY(fastVal), padX + plotW * 0.8, speedToY(fastVal));
    ctx.lineTo(w - padX, speedToY(fastVal));
  } else if (activeSpeedPreset === "montage") {
    ctx.moveTo(padX, speedToY(2.0));
    ctx.lineTo(padX + plotW * 0.5, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.8, speedToY(slowVal));
    ctx.lineTo(w - padX, speedToY(1.0));
  } else {
    // Jump cut
    ctx.moveTo(padX, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.25, speedToY(1.0));
    ctx.lineTo(padX + plotW * 0.5, speedToY(fastVal));
    ctx.lineTo(padX + plotW * 0.75, speedToY(1.0));
    ctx.lineTo(w - padX, speedToY(fastVal));
  }

  ctx.stroke();

  // Glow line
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(157, 78, 221, 0.4)";
  ctx.stroke();
}

async function handleApplySpeedRamp() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn clip bạn muốn uốn tốc độ!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const isBeat = document.getElementById("chkSpeedBeatSync").checked;
  const fastSpeed = parseFloat(document.getElementById("sliderFastSpeed").value) || 5.0;
  const slowSpeed = parseFloat(document.getElementById("sliderSlowSpeed").value) || 0.4;

  const payload = {
    folder_name: activeProject.folder_name,
    targets: targets,
    preset: activeSpeedPreset,
    params: { fast_speed: fastSpeed, slow_speed: slowSpeed },
    use_beat: isBeat,
    beats_us: currentBeats
  };

  try {
    const res = await fetch("/api/apply_speed_ramp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Áp dụng Speed Ramp thành công!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
}

async function handleResetSpeed() {
  if (!activeProject) return;
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn clip cần khôi phục tốc độ!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  try {
    const res = await fetch("/api/reset_speed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_name: activeProject.folder_name,
        targets: targets
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Đã khôi phục tốc độ chuẩn!", "success");
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối", "error");
  }
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

// ==========================================
// POINT-LOCK STABILIZER FUNCTIONS
// ==========================================

function updateStabilizerAnchorDisplay() {
  const modeDisplay = document.getElementById("stabAnchorDisplay");
  const coordDisplay = document.getElementById("stabCoordDisplay");

  const xPct = (stabAnchorXRatio * 100).toFixed(1);
  const yPct = (stabAnchorYRatio * 100).toFixed(1);

  if (stabAnchorMode === "center") {
    modeDisplay.textContent = "Tâm Giữa (50%, 50%)";
  } else if (stabAnchorMode === "face") {
    modeDisplay.textContent = "Mặt / Đầu (50%, 30%)";
  } else if (stabAnchorMode === "chest") {
    modeDisplay.textContent = "Áo / Logo (50%, 55%)";
  } else {
    modeDisplay.textContent = `Tùy Chọn (${xPct}%, ${yPct}%)`;
  }

  coordDisplay.textContent = `X: ${xPct}% | Y: ${yPct}%`;
}

function drawStabilizerCanvas() {
  const canvas = document.getElementById("stabilizerCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  // Background - Dark Studio Viewport
  ctx.fillStyle = "#121218";
  ctx.fillRect(0, 0, w, h);

  // Subtle Rule-of-Thirds Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);

  // Vertical grid lines
  ctx.beginPath();
  ctx.moveTo(w / 3, 0); ctx.lineTo(w / 3, h);
  ctx.moveTo((w * 2) / 3, 0); ctx.lineTo((w * 2) / 3, h);
  // Horizontal grid lines
  ctx.moveTo(0, h / 3); ctx.lineTo(w, h / 3);
  ctx.moveTo(0, (h * 2) / 3); ctx.lineTo(w, (h * 2) / 3);
  ctx.stroke();
  ctx.setLineDash([]);

  // Center axes (subtle)
  ctx.strokeStyle = "rgba(0, 242, 254, 0.15)";
  ctx.beginPath();
  ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h);
  ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2);
  ctx.stroke();

  // Draw Stylized Subject Reference Silhouette (Head at 30%, Torso at 55%)
  ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
  // Head
  ctx.beginPath();
  ctx.arc(w * 0.5, h * 0.30, 28, 0, Math.PI * 2);
  ctx.fill();
  // Shoulders & Torso
  ctx.beginPath();
  ctx.ellipse(w * 0.5, h * 0.58, 55, 80, 0, 0, Math.PI * 2);
  ctx.fill();

  // Reference Text for Key Landmarks
  ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("👤 Khu vực Mặt / Đầu", w * 0.5, h * 0.30 - 34);
  ctx.fillText("👕 Khu vực Ngực / Logo", w * 0.5, h * 0.55 + 5);

  // Safe Margins / Auto-Zoom Border Guide
  const minZoom = parseFloat(document.getElementById("sliderStabMinZoom")?.value || 1.15);
  const marginX = ((minZoom - 1.0) / minZoom) * (w / 2);
  const marginY = ((minZoom - 1.0) / minZoom) * (h / 2);

  ctx.strokeStyle = "rgba(245, 166, 35, 0.35)";
  ctx.setLineDash([3, 3]);
  ctx.strokeRect(marginX, marginY, w - marginX * 2, h - marginY * 2);
  ctx.setLineDash([]);
  ctx.fillStyle = "rgba(245, 166, 35, 0.7)";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(`Viền an toàn (${minZoom.toFixed(2)}x Zoom)`, marginX + 4, marginY + 12);

  // Active Anchor Target Coordinates
  const targetX = stabAnchorXRatio * w;
  const targetY = stabAnchorYRatio * h;

  // Outer Glowing Target Circle
  ctx.shadowColor = "#00f2fe";
  ctx.shadowBlur = 10;
  ctx.strokeStyle = "#00f2fe";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(targetX, targetY, 20, 0, Math.PI * 2);
  ctx.stroke();

  // Inner Target Dot
  ctx.fillStyle = "#00f2fe";
  ctx.beginPath();
  ctx.arc(targetX, targetY, 4, 0, Math.PI * 2);
  ctx.fill();

  // Crosshair Lines
  ctx.shadowBlur = 0;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(targetX - 28, targetY); ctx.lineTo(targetX - 8, targetY);
  ctx.moveTo(targetX + 8, targetY); ctx.lineTo(targetX + 28, targetY);
  ctx.moveTo(targetX, targetY - 28); ctx.lineTo(targetX, targetY - 8);
  ctx.moveTo(targetX, targetY + 8); ctx.lineTo(targetX, targetY + 28);
  ctx.stroke();

  // Target Badge Label
  ctx.fillStyle = "rgba(0, 242, 254, 0.9)";
  ctx.font = "bold 9px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("MỐC KHÓA TRỤC 🎯", targetX, targetY + 34);
}

async function handleApplyStabilizer() {
  if (!activeProject) {
    showToast("Vui lòng chọn một dự án CapCut trước!", "warning");
    return;
  }
  if (selectedSegments.size === 0) {
    showToast("Vui lòng tích chọn clip bạn muốn chống rung!", "warning");
    return;
  }

  const targets = Array.from(selectedSegments).map(key => {
    const [t, s] = key.split("_").map(Number);
    return { track_index: t, segment_index: s };
  });

  const smoothWin = parseInt(document.getElementById("sliderStabSmoothWin")?.value || 15);
  const minZoom = parseFloat(document.getElementById("sliderStabMinZoom")?.value || 1.15);

  const payload = {
    folder_name: activeProject.folder_name,
    targets: targets,
    anchor_mode: stabAnchorMode,
    anchor_x_ratio: stabAnchorXRatio,
    anchor_y_ratio: stabAnchorYRatio,
    stabilize_mode: stabMode,
    smooth_window: smoothWin,
    min_zoom: minZoom,
    fps: activeProject.fps || 30
  };

  const btn = document.getElementById("btnApplyStabilizer");
  const origText = btn.textContent;
  btn.textContent = "⏳ Đang theo dõi khung hình & chống rung...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/apply_stabilizer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.status === "success") {
      showToast(data.message || "Chống rung và khóa điểm mốc thành công!", "success");

      // Display results summary box
      const resBox = document.getElementById("stabResultsBox");
      if (resBox && data.details && data.details.length > 0) {
        const d = data.details[0];
        document.getElementById("resStabFrames").textContent = `${d.total_frames} frames`;
        document.getElementById("resStabZoom").textContent = `${d.auto_zoom}x`;
        document.getElementById("resStabOffset").textContent = `ΔX: ${d.max_deviation_x} | ΔY: ${d.max_deviation_y}`;
        resBox.classList.remove("hidden");
      }

      // Refresh project to reflect new keyframes
      selectProject(activeProject.folder_name);
    } else {
      showToast(data.message || "Lỗi khi xử lý chống rung", "error");
    }
  } catch (err) {
    showToast("Lỗi kết nối máy chủ", "error");
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

