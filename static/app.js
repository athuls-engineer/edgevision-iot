document.addEventListener('DOMContentLoaded', () => {
  const valFps = document.getElementById('valFps');
  const hudFps = document.getElementById('hudFps');
  const valTargets = document.getElementById('valTargets');
  const valLux = document.getElementById('valLux');
  const valIntrusions = document.getElementById('valIntrusions');
  const statusPulse = document.getElementById('statusPulse');
  const armBtn = document.getElementById('armBtn');
  const alertFeed = document.getElementById('alertFeed');
  const evidenceGrid = document.getElementById('evidenceGrid');
  const refreshEvidenceBtn = document.getElementById('refreshEvidenceBtn');
  const toggleEnhancer = document.getElementById('toggleEnhancer');

  let isArmed = true;

  // 1. WebSocket Telemetry
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
  let socket;

  function connectWs() {
    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        updateTelemetry(data);
      } catch (err) {
        console.error('Error parsing telemetry payload:', err);
      }
    };

    socket.onclose = () => {
      setTimeout(connectWs, 2000);
    };
  }

  function updateTelemetry(data) {
    const m = data.metrics || {};
    const alerts = data.recent_alerts || [];

    const fps = m.fps ? m.fps.toFixed(1) : '0.0';
    valFps.textContent = fps;
    hudFps.textContent = `${fps} FPS`;

    valTargets.textContent = m.target_count || 0;
    valLux.textContent = `${(m.avg_luminance || 0).toFixed(1)} lux`;
    valIntrusions.textContent = m.total_intrusions || 0;

    // Visual pulse
    if (m.target_detected && isArmed) {
      statusPulse.classList.add('alert');
    } else {
      statusPulse.classList.remove('alert');
    }

    // Render alert feed
    if (alerts.length > 0) {
      alertFeed.innerHTML = alerts.map(a => `
        <div class="alert-item ${a.severity}">
          <div style="display:flex; justify-content:space-between; font-weight:600; margin-bottom:2px;">
            <span>[${a.type}]</span>
            <span style="font-family:'JetBrains Mono'; color:#94a3b8;">${new Date(a.timestamp * 1000).toLocaleTimeString()}</span>
          </div>
          <div>${a.message}</div>
        </div>
      `).join('');
    }
  }

  // 2. Fetch and render Evidence Gallery
  async function loadEvidence() {
    try {
      const res = await fetch('/api/evidence?limit=12');
      const data = await res.json();
      const items = data.evidence || [];

      if (items.length === 0) {
        evidenceGrid.innerHTML = '<div class="empty-state">No intrusion snapshots captured yet. Step in front of your camera to trigger an event!</div>';
        return;
      }

      evidenceGrid.innerHTML = items.map(item => `
        <div class="evidence-thumb">
          <a href="${item.url}" target="_blank">
            <img src="${item.url}" alt="${item.filename}" loading="lazy">
          </a>
          <div class="evidence-meta">
            <span class="evidence-time">${item.timestamp.split(' ')[1]}</span>
            <a href="${item.url}" download="${item.filename}" style="color:#38bdf8; text-decoration:none;">Download</a>
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error('Failed to load evidence:', err);
    }
  }

  refreshEvidenceBtn.addEventListener('click', loadEvidence);
  setInterval(loadEvidence, 6000); // Auto refresh gallery every 6s

  // 3. Arm / Disarm Toggle
  armBtn.addEventListener('click', async () => {
    isArmed = !isArmed;
    try {
      await fetch(`/api/config/arm?armed=${isArmed}`, { method: 'POST' });
      if (isArmed) {
        armBtn.textContent = '🔒 ARMED (GUARDING)';
        armBtn.className = 'btn btn-danger';
      } else {
        armBtn.textContent = '🔓 DISARMED (PAUSED)';
        armBtn.className = 'btn btn-danger disarmed';
      }
    } catch (e) {
      console.error(e);
    }
  });

  // 4. Low-Light CLAHE Toggle
  toggleEnhancer.addEventListener('change', async (e) => {
    try {
      await fetch(`/api/config/enhancer?enabled=${e.target.checked}&method=clahe`, { method: 'POST' });
    } catch (err) {
      console.error(err);
    }
  });

  // 5. Source Modal Switcher
  const sourceModal = document.getElementById('sourceModal');
  const sourceModalBtn = document.getElementById('sourceModalBtn');
  const closeSourceModal = document.getElementById('closeSourceModal');
  const sourceSelect = document.getElementById('sourceSelect');
  const webcamIndexGroup = document.getElementById('webcamIndexGroup');
  const ipUrlGroup = document.getElementById('ipUrlGroup');
  const saveSourceBtn = document.getElementById('saveSourceBtn');

  sourceModalBtn.onclick = () => { sourceModal.style.display = 'flex'; };
  closeSourceModal.onclick = () => { sourceModal.style.display = 'none'; };

  sourceSelect.onchange = () => {
    if (sourceSelect.value === 'webcam') {
      webcamIndexGroup.style.display = 'block';
      ipUrlGroup.style.display = 'none';
    } else {
      webcamIndexGroup.style.display = 'none';
      ipUrlGroup.style.display = 'block';
    }
  };

  saveSourceBtn.onclick = async () => {
    const isWebcam = sourceSelect.value === 'webcam';
    const sourceVal = isWebcam ? 'webcam' : document.getElementById('ipUrlInput').value.trim();
    const devIdx = parseInt(document.getElementById('deviceIndexInput').value, 10) || 0;

    try {
      await fetch('/api/config/source', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: sourceVal, device_index: devIdx })
      });
      document.getElementById('hudSource').textContent = isWebcam ? `Source: Webcam (${devIdx})` : `Source: IP Stream`;
      sourceModal.style.display = 'none';
      // Reload stream element
      document.getElementById('videoStream').src = '/video_feed?t=' + Date.now();
    } catch (e) {
      alert('Error updating source: ' + e);
    }
  };

  // 6. Telegram Modal
  const tgModal = document.getElementById('tgModal');
  const tgSetupBtn = document.getElementById('tgSetupBtn');
  const closeTgModal = document.getElementById('closeTgModal');
  const saveTgBtn = document.getElementById('saveTgBtn');
  const tgBadge = document.getElementById('tgBadge');

  tgSetupBtn.onclick = () => { tgModal.style.display = 'flex'; };
  closeTgModal.onclick = () => { tgModal.style.display = 'none'; };

  saveTgBtn.onclick = async () => {
    const token = document.getElementById('tgTokenInput').value.trim();
    const chatId = document.getElementById('tgChatIdInput').value.trim();
    const enabled = document.getElementById('tgEnableToggle').checked;

    try {
      await fetch('/api/config/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enabled, bot_token: token, chat_id: chatId })
      });
      tgBadge.textContent = enabled ? 'Connected (Active)' : 'Disconnected';
      tgBadge.style.color = enabled ? '#34d399' : '#94a3b8';
      tgModal.style.display = 'none';
    } catch (e) {
      alert('Error setting telegram: ' + e);
    }
  };

  window.onclick = (e) => {
    if (e.target === sourceModal) sourceModal.style.display = 'none';
    if (e.target === tgModal) tgModal.style.display = 'none';
  };

  connectWs();
  loadEvidence();
});
