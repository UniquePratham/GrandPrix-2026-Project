/**
 * Main Frontend Application Controller
 * Connects 3D Scene, Audio Player, Waveform Visualizer, AI Endpoints, and Chart.js
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize 3D Scene
  let scene3D = null;
  if (window.F1Scene3D) {
    scene3D = new F1Scene3D('f1CanvasContainer');
  }

  // 2. DOM Elements
  const playBtn = document.getElementById('playBtn');
  const playIcon = document.getElementById('playIcon');
  const playText = document.getElementById('playText');
  const audioPlayer = document.getElementById('audioPlayer');
  const waveformCanvas = document.getElementById('waveformCanvas');
  const currentTimeEl = document.getElementById('currentTime');
  const totalTimeEl = document.getElementById('totalTime');
  const diarizationFeed = document.getElementById('diarizationFeed');
  const explanationList = document.getElementById('explanationList');
  const dropZone = document.getElementById('dropZone');
  const audioFileInput = document.getElementById('audioFileInput');
  const sourceButtons = document.querySelectorAll('.source-btn');
  const camButtons = document.querySelectorAll('.cam-btn');

  let currentClipId = 'ham_monaco_stress';
  let currentAnalysis = null;
  let lapChart = null;
  let waveformPoints = [];
  let isPlaying = false;
  let animFrameId = null;

  // 3. Camera Preset Buttons
  camButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      camButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const camMode = btn.getAttribute('data-cam');
      if (scene3D) scene3D.setCameraPreset(camMode);
    });
  });

  // 4. Source Buttons
  sourceButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      sourceButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const clipId = btn.getAttribute('data-clip');
      currentClipId = clipId;
      analyzeClip(clipId);
    });
  });

  // 5. Drag and Drop Audio Upload
  if (dropZone && audioFileInput) {
    dropZone.addEventListener('click', () => audioFileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--f1-cyan)';
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = 'rgba(0, 240, 255, 0.3)';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'rgba(0, 240, 255, 0.3)';
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    audioFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });
  }

  function handleFileUpload(file) {
    const reader = new FileReader();
    reader.onload = (evt) => {
      const base64Audio = evt.target.result;
      sourceButtons.forEach((b) => b.classList.remove('active'));
      analyzeCustomAudio(base64Audio, file.name);
    };
    reader.readAsDataURL(file);
  }

  // 6. Audio Playback & Waveform Animation
  playBtn.addEventListener('click', () => {
    if (!audioPlayer.src) return;
    if (audioPlayer.paused) {
      audioPlayer.play();
      isPlaying = true;
      playIcon.textContent = '❚❚';
      playText.textContent = 'PAUSE';
      startWaveformAnimation();
    } else {
      audioPlayer.pause();
      isPlaying = false;
      playIcon.textContent = '▶';
      playText.textContent = 'PLAY TRANSMISSION';
      cancelAnimationFrame(animFrameId);
    }
  });

  audioPlayer.addEventListener('timeupdate', () => {
    const cur = audioPlayer.currentTime;
    const dur = audioPlayer.duration || 6.0;
    currentTimeEl.textContent = `${cur.toFixed(1)}s`;
    totalTimeEl.textContent = `${dur.toFixed(1)}s`;
    drawWaveform(cur / dur);
  });

  audioPlayer.addEventListener('ended', () => {
    isPlaying = false;
    playIcon.textContent = '▶';
    playText.textContent = 'PLAY TRANSMISSION';
    cancelAnimationFrame(animFrameId);
    drawWaveform(0);
  });

  function startWaveformAnimation() {
    function loop() {
      if (isPlaying) {
        const progress = audioPlayer.duration ? audioPlayer.currentTime / audioPlayer.duration : 0;
        drawWaveform(progress);
        animFrameId = requestAnimationFrame(loop);
      }
    }
    loop();
  }

  function drawWaveform(progress = 0) {
    if (!waveformCanvas) return;
    const ctx = waveformCanvas.getContext('2d');
    const width = (waveformCanvas.width = waveformCanvas.offsetWidth);
    const height = (waveformCanvas.height = waveformCanvas.offsetHeight);

    ctx.clearRect(0, 0, width, height);

    const bars = waveformPoints.length > 0 ? waveformPoints : Array(64).fill(0.25);
    const barWidth = width / bars.length;

    bars.forEach((val, i) => {
      const barHeight = Math.max(4, val * height * 0.9);
      const x = i * barWidth;
      const y = (height - barHeight) / 2;
      const barProgress = i / bars.length;

      if (barProgress <= progress) {
        // Active played portion
        ctx.fillStyle = currentAnalysis?.stress_analysis?.mood === 'Stressed' ? '#FF2A24' : '#00F0FF';
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 8;
      } else {
        // Unplayed portion
        ctx.fillStyle = 'rgba(255, 255, 255, 0.18)';
        ctx.shadowBlur = 0;
      }

      ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
    });
  }

  // 7. API Communication
  // Static demo data, used when the Python AI backend is not running.
  let staticClips = null;

  async function loadStaticClips() {
    if (staticClips) return staticClips;
    const res = await fetch('data/clips.json');
    staticClips = await res.json();
    return staticClips;
  }

  async function analyzeClip(clipId) {
    try {
      const response = await fetch('/api/analyze-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clip_id: clipId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error('backend unavailable');
      renderDashboard(data);
    } catch (err) {
      console.error('Failed to analyze clip:', err);
      // No backend: fall back to the pre-computed demo payloads.
      try {
        const clips = await loadStaticClips();
        const data = clips[clipId];
        if (data) renderDashboard(data);
        else console.error('No demo data for clip:', clipId);
      } catch (e) {
        console.error('Failed to analyze clip:', err);
      }
    }
  }

  async function analyzeCustomAudio(base64Audio, filename) {
    try {
      const response = await fetch('/api/analyze-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_base64: base64Audio, filename: filename }),
      });
      const data = await response.json();
      renderDashboard(data);
    } catch (err) {
      console.error('Failed to analyze custom audio:', err);
    }
  }

  // 8. Render Dashboard Data
  function renderDashboard(data) {
    currentAnalysis = data;
    const meta = data.metadata || {};
    const stress = data.stress_analysis || {};
    const telem = data.telemetry || {};
    const snap = telem.snapshot || {};

    // 1. Top Bar & Viewport Header
    document.getElementById('driverNameBadge').textContent = (meta.driver_name || 'LEWIS HAMILTON').toUpperCase();
    document.getElementById('racingNumBadge').textContent = meta.racing_number || '44';
    document.getElementById('gpSessionBadge').textContent = `${(meta.grand_prix || 'MONACO GP').toUpperCase()} • LAP ${meta.lap || 48}/60`;

    // 2. HUD Telemetry
    document.getElementById('speedVal').textContent = snap.speed_kmh || 284;
    document.getElementById('gearVal').textContent = `G ${snap.gear || 7}`;
    if (snap.tire_temps_celsius) {
      document.getElementById('tempFL').textContent = `${snap.tire_temps_celsius.front_left}°C`;
      document.getElementById('tempFR').textContent = `${snap.tire_temps_celsius.front_right}°C`;
      document.getElementById('tempRL').textContent = `${snap.tire_temps_celsius.rear_left}°C`;
      document.getElementById('tempRR').textContent = `${snap.tire_temps_celsius.rear_right}°C`;
    }

    // 3. Stress Radar & Mood Banner
    const mood = stress.mood || 'Calm';
    const moodBadge = document.getElementById('moodBadge');
    const moodText = document.getElementById('moodText');
    const moodIcon = document.getElementById('moodIcon');
    const heroCard = document.getElementById('stressHeroCard');
    const scoreVal = document.getElementById('stressScoreVal');

    moodText.textContent = mood.toUpperCase();
    scoreVal.textContent = (stress.stress_level || 20.0).toFixed(1);
    document.getElementById('confidenceVal').textContent = `${Math.round((stress.confidence || 0.85) * 100)}%`;
    document.getElementById('pacePenaltyVal').textContent = telem.correlation_summary?.lap_delta_penalty || '+0.15s';
    document.getElementById('f0MeanVal').textContent = `${stress.metrics?.f0_mean_hz || 150} Hz`;
    document.getElementById('jitterVal').textContent = stress.metrics?.vocal_jitter || 0.02;

    moodBadge.className = `mood-badge-large ${mood.toLowerCase()}`;
    heroCard.className = `stress-hero-card glass-panel ${mood.toLowerCase()}`;

    if (mood === 'Stressed') {
      moodIcon.textContent = '🔥';
      scoreVal.style.color = 'var(--f1-neon-red)';
    } else if (mood === 'Tired') {
      moodIcon.textContent = '💤';
      scoreVal.style.color = 'var(--f1-amber)';
    } else {
      moodIcon.textContent = '🟢';
      scoreVal.style.color = 'var(--f1-cyan)';
    }

    // 4. AI Diagnostics
    explanationList.innerHTML = '';
    const explanations = stress.explanations || [];
    explanations.forEach((exp) => {
      const div = document.createElement('div');
      div.className = 'explanation-item';
      div.textContent = exp;
      explanationList.appendChild(div);
    });

    // 5. Speaker Diarization Conversation Feed
    diarizationFeed.innerHTML = '';
    const turns = data.diarized_turns || [];
    turns.forEach((turn) => {
      const turnDiv = document.createElement('div');
      const isDriver = turn.role === 'driver';
      turnDiv.className = `diarization-turn ${isDriver ? 'driver' : 'engineer'} ${isDriver && mood === 'Stressed' ? 'stressed' : ''}`;

      const icon = isDriver ? '🏎️' : '🎧';
      const title = isDriver ? 'DRIVER (COCKPIT)' : 'PIT WALL ENGINEER';
      const timeStr = `${turn.start.toFixed(1)}s - ${turn.end.toFixed(1)}s`;

      turnDiv.innerHTML = `
        <div class="turn-header">
          <div class="turn-speaker-label">
            <span>${icon}</span>
            <span>${title}</span>
            <span style="font-size: 0.7rem; color: var(--text-dim); margin-left: 6px;">[Conf: ${Math.round(turn.confidence * 100)}%]</span>
          </div>
          <div class="turn-time">${timeStr}</div>
        </div>
        <div class="turn-text">"${turn.text}"</div>
      `;
      diarizationFeed.appendChild(turnDiv);
    });

    // 6. Audio Waveform & Player Source
    waveformPoints = data.waveform || [];
    drawWaveform(0);
    if (data.audio_url) {
      audioPlayer.src = data.audio_url;
      audioPlayer.load();
    }

    // 7. Update 3D Scene Visuals
    if (scene3D) {
      scene3D.updateStressState(mood, stress.stress_level, telem);
    }

    // 8. Update Lap Telemetry Chart
    renderLapChart(telem.lap_history || [], telem.radio_lap || 48);
  }

  // 9. Chart.js Lap Telemetry Curve
  function renderLapChart(lapHistory, radioLap) {
    const ctx = document.getElementById('lapTelemetryChart').getContext('2d');
    const labels = lapHistory.map((l) => `L${l.lap}`);
    const lapTimes = lapHistory.map((l) => l.lap_time);
    const stressIndices = lapHistory.map((l) => l.stress_index);

    if (lapChart) {
      lapChart.destroy();
    }

    lapChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Lap Time (seconds)',
            data: lapTimes,
            borderColor: '#00F0FF',
            backgroundColor: 'rgba(0, 240, 255, 0.05)',
            borderWidth: 2,
            pointRadius: (ctx) => (lapHistory[ctx.dataIndex]?.lap === radioLap ? 8 : 1),
            pointBackgroundColor: (ctx) => (lapHistory[ctx.dataIndex]?.lap === radioLap ? '#FF2A24' : '#00F0FF'),
            pointBorderColor: '#FFF',
            fill: true,
            tension: 0.3,
            yAxisID: 'y',
          },
          {
            label: 'Driver Stress Index (0-100)',
            data: stressIndices,
            borderColor: 'rgba(255, 42, 36, 0.7)',
            borderDash: [4, 4],
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            labels: { color: '#8E9BAE', font: { family: 'Rajdhani', size: 12 } },
          },
          tooltip: {
            backgroundColor: 'rgba(14, 18, 28, 0.95)',
            titleColor: '#00F0FF',
            bodyColor: '#FFF',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
          },
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#8E9BAE', font: { family: 'Rajdhani', size: 10 } },
          },
          y: {
            type: 'linear',
            position: 'left',
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#00F0FF', font: { family: 'Orbitron', size: 10 } },
            title: { display: true, text: 'Lap Pace (s)', color: '#00F0FF' },
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#FF2A24', font: { family: 'Orbitron', size: 10 } },
            min: 0,
            max: 100,
            title: { display: true, text: 'Stress Score', color: '#FF2A24' },
          },
        },
      },
    });
  }

  // 10. Initial Load
  analyzeClip(currentClipId);

  // Live Clock ticker
  setInterval(() => {
    const now = new Date();
    const clockEl = document.getElementById('liveClock');
    if (clockEl) {
      clockEl.textContent = `${now.toTimeString().split(' ')[0]} UTC`;
    }
  }, 1000);
});
