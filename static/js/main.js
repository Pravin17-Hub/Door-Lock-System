/* FaceSecure Web Application - Live Frontend Controller */

document.addEventListener('DOMContentLoaded', () => {
  const dashboardEsp32Status = document.getElementById('dashboard-esp32-status');
  const bannerCard = document.getElementById('banner-card');
  const bannerStatus = document.getElementById('banner-status');
  const bannerName = document.getElementById('banner-name');
  const bannerConf = document.getElementById('banner-conf');
  const doorStateLbl = document.getElementById('door-state-lbl');
  const cmdLogLbl = document.getElementById('cmd-log-lbl');
  const videoFeedElement = document.querySelector('.video-feed');
  const enrollCamImg = document.getElementById('enroll-cam-img');

  let activeCameraHeartbeatTimer = null;

  function startCameraHeartbeat() {
    if (!activeCameraHeartbeatTimer) {
      activeCameraHeartbeatTimer = setInterval(() => {
        fetch('/api/camera_heartbeat').catch(() => {});
      }, 1000);
      fetch('/api/camera_heartbeat').catch(() => {});
    }
  }

  function stopCameraHeartbeat() {
    if (activeCameraHeartbeatTimer) {
      clearInterval(activeCameraHeartbeatTimer);
      activeCameraHeartbeatTimer = null;
    }
  }

  // If user is on the Camera Recognition Page (/camera), start camera heartbeat!
  if (videoFeedElement) {
    startCameraHeartbeat();
  }

  // --- OPTION 1: BROWSER WEBSERIAL API MOTOR CONTROLLER ---
  let webSerialPort = null;
  let webSerialWriter = null;
  let webSerialIsConnected = false;
  let lastWebSerialUnlockTime = 0;

  const webserialStatusBadge = document.getElementById('webserial-status-badge');
  const btnConnectWebserial = document.getElementById('btn-connect-webserial');
  const btnDisconnectWebserial = document.getElementById('btn-disconnect-webserial');
  const btnTestWebserial = document.getElementById('btn-test-webserial');
  const webserialMsg = document.getElementById('webserial-msg');
  const cameraWebserialBadge = document.getElementById('camera-webserial-badge');
  const btnCameraConnectWebserial = document.getElementById('btn-camera-connect-webserial');

  function updateWebSerialBadges(connected, portName = "USB ESP32") {
    webSerialIsConnected = connected;
    if (webserialStatusBadge) {
      if (connected) {
        webserialStatusBadge.textContent = `Connected (${portName}) 🟢`;
        webserialStatusBadge.style.color = 'var(--success)';
      } else {
        webserialStatusBadge.textContent = 'Disconnected 🔴';
        webserialStatusBadge.style.color = 'var(--danger)';
      }
    }
    if (cameraWebserialBadge) {
      if (connected) {
        cameraWebserialBadge.textContent = `WebSerial: Connected 🟢`;
        cameraWebserialBadge.style.color = 'var(--success)';
      } else {
        cameraWebserialBadge.textContent = `WebSerial: Off 🔴`;
        cameraWebserialBadge.style.color = 'var(--danger)';
      }
    }
    if (btnConnectWebserial && btnDisconnectWebserial) {
      btnConnectWebserial.style.display = connected ? 'none' : 'inline-block';
      btnDisconnectWebserial.style.display = connected ? 'inline-block' : 'none';
    }
  }

  async function connectWebSerial() {
    if (!('serial' in navigator)) {
      alert('Web Serial API is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Opera.');
      return false;
    }

    try {
      webSerialPort = await navigator.serial.requestPort();
      await webSerialPort.open({ baudRate: 9600 });

      const textEncoder = new TextEncoderStream();
      const writableStreamClosed = textEncoder.readable.pipeTo(webSerialPort.writable);
      webSerialWriter = textEncoder.writable.getWriter();

      updateWebSerialBadges(true);
      if (webserialMsg) webserialMsg.innerHTML = '<span style="color: var(--success);">🟢 Browser USB Connected! Motor ready to receive signals.</span>';
      
      webSerialPort.addEventListener('disconnect', () => {
        disconnectWebSerial(false);
      });
      return true;
    } catch (err) {
      console.error('WebSerial connection error:', err);
      if (webserialMsg) webserialMsg.innerHTML = `<span style="color: var(--danger);">⚠️ ${err.message || 'Connection canceled'}</span>`;
      updateWebSerialBadges(false);
      return false;
    }
  }

  async function disconnectWebSerial(userInitiated = true) {
    try {
      if (webSerialWriter) {
        await webSerialWriter.close();
        webSerialWriter = null;
      }
      if (webSerialPort) {
        await webSerialPort.close();
        webSerialPort = null;
      }
    } catch (e) {
      console.warn('Error during WebSerial close:', e);
    }
    updateWebSerialBadges(false);
    if (webserialMsg) webserialMsg.textContent = userInitiated ? 'Browser USB Disconnected.' : 'USB Device Disconnected.';
  }

  async function sendWebSerialCommand(command) {
    if (!webSerialIsConnected || !webSerialWriter) return false;
    try {
      await webSerialWriter.write(`${command.trim().toUpperCase()}\n`);
      console.log(`[WebSerial API] Transmitted: ${command}`);
      return true;
    } catch (err) {
      console.error('[WebSerial API] Write error:', err);
      disconnectWebSerial(false);
      return false;
    }
  }

  if (btnConnectWebserial) {
    btnConnectWebserial.addEventListener('click', connectWebSerial);
  }
  if (btnDisconnectWebserial) {
    btnDisconnectWebserial.addEventListener('click', () => disconnectWebSerial(true));
  }
  if (btnCameraConnectWebserial) {
    btnCameraConnectWebserial.addEventListener('click', connectWebSerial);
  }

  if (btnTestWebserial) {
    btnTestWebserial.addEventListener('click', async () => {
      if (!webSerialIsConnected) {
        const ok = await connectWebSerial();
        if (!ok) return;
      }
      const sent = await sendWebSerialCommand('UNLOCK');
      if (sent) {
        alert('WebSerial Signal Sent: UNLOCK (Servo motor rotating 90° for 5s)');
        setTimeout(() => {
          sendWebSerialCommand('LOCK');
        }, 5000);
      }
    });
  }

  // --- CONTINUOUS REAL-TIME HARDWARE & SYSTEM POLLING (500ms) ---
  setInterval(async () => {
    try {
      const response = await fetch('/api/status');
      if (response.ok) {
        const data = await response.json();

        // Update ESP32 hardware status badge on dashboard
        if (dashboardEsp32Status) {
          if (data.esp32_connected) {
            dashboardEsp32Status.textContent = `Connected (${data.esp32_port}) 🟢`;
            dashboardEsp32Status.style.color = 'var(--success)';
          } else {
            dashboardEsp32Status.textContent = 'Disconnected 🔴';
            dashboardEsp32Status.style.color = 'var(--danger)';
          }
        }

        // Update Camera page live banner if present
        if (bannerCard) {
          updateLiveBanner(data);
        }
      }
    } catch (err) {
      console.error('Error polling status:', err);
    }
  }, 500);

  let webSerialDoorOpen = false;

  function updateLiveBanner(data) {
    if (!bannerCard) return;

    if (data.door_is_open) {
      bannerCard.className = 'banner-card granted';
      bannerStatus.textContent = 'ACCESS GRANTED 🔓';
      bannerStatus.style.color = 'var(--success)';
      bannerName.textContent = data.person_name ? `Welcome, ${data.person_name}!` : 'Person Detected';
      bannerConf.textContent = `Match Confidence: ${data.confidence}%`;
      
      if (doorStateLbl) {
        doorStateLbl.textContent = `Door Opened 🔓 (Auto-locking in ${data.seconds_remaining}s)`;
        doorStateLbl.className = 'badge badge-success';
      }
      if (cmdLogLbl) {
        const serialTag = webSerialIsConnected ? ' [WebSerial Active]' : '';
        cmdLogLbl.textContent = `SENT 'UNLOCK' -> Door Open (${data.seconds_remaining}s left)${serialTag}`;
      }

      // Automatically transmit UNLOCK over Browser WebSerial if connected
      if (webSerialIsConnected && !webSerialDoorOpen && (Date.now() - lastWebSerialUnlockTime > 4000)) {
        webSerialDoorOpen = true;
        lastWebSerialUnlockTime = Date.now();
        sendWebSerialCommand('UNLOCK');
      }
    } else if (data.status_type === 'DENIED') {
      bannerCard.className = 'banner-card denied';
      bannerStatus.textContent = 'FACE NOT MATCHED 🔒';
      bannerStatus.style.color = 'var(--danger)';
      bannerName.textContent = 'Unauthorized / Unknown Face';
      bannerConf.textContent = `Match Confidence: ${data.confidence}%`;

      if (doorStateLbl) {
        doorStateLbl.textContent = 'Door Closed 🔒';
        doorStateLbl.className = 'badge badge-warning';
      }
      if (cmdLogLbl) {
        const serialTag = webSerialIsConnected ? ' [WebSerial Active]' : '';
        cmdLogLbl.textContent = `SENT 'ALARM' -> Door Kept Closed${serialTag}`;
      }

      if (webSerialIsConnected && webSerialDoorOpen) {
        webSerialDoorOpen = false;
        sendWebSerialCommand('LOCK');
      }
    } else {
      bannerCard.className = 'banner-card';
      bannerStatus.textContent = 'SCANNING...';
      bannerStatus.style.color = 'var(--text-secondary)';
      bannerName.textContent = 'No Face Detected';
      bannerConf.textContent = 'Confidence: --';

      if (doorStateLbl) {
        doorStateLbl.textContent = 'Door Closed 🔒';
        doorStateLbl.className = 'badge badge-warning';
      }
      if (cmdLogLbl) {
        cmdLogLbl.textContent = 'Ready (Idle)';
      }

      if (webSerialIsConnected && webSerialDoorOpen) {
        webSerialDoorOpen = false;
        sendWebSerialCommand('LOCK');
      }
    }
  }

  // --- AJAX ESP32 HARDWARE CONNECT, DISCONNECT, & COM PORT REFRESH ---
  const btnConnectEsp32 = document.getElementById('btn-connect-esp32');
  const btnDisconnectEsp32 = document.getElementById('btn-disconnect-esp32');
  const btnRefreshPorts = document.getElementById('btn-refresh-ports');
  const btnTestUnlock = document.getElementById('btn-test-unlock');
  const selectComPort = document.getElementById('select-com-port');
  const esp32DiagMsg = document.getElementById('esp32-diagnostic-msg');

  if (btnTestUnlock) {
    btnTestUnlock.addEventListener('click', async () => {
      try {
        const response = await fetch('/api/test_unlock', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        if (esp32DiagMsg) esp32DiagMsg.innerHTML = `<span style="color: var(--success); font-weight:700;">${data.message}</span>`;
      } catch (err) {
        alert('Server communication error.');
      }
    });
  }

  if (btnRefreshPorts) {
    btnRefreshPorts.addEventListener('click', async () => {
      btnRefreshPorts.textContent = '🔄 Scanning...';
      try {
        const response = await fetch('/api/refresh_ports');
        if (response.ok) {
          const data = await response.json();
          selectComPort.innerHTML = '<option value="COM7">COM7 (CP2102 ESP32 Board)</option><option value="AUTO">Auto-Detect USB Hardware</option>';
          data.ports.forEach(p => {
            if (p.device !== 'COM7') {
              const opt = document.createElement('option');
              opt.value = p.device;
              opt.textContent = p.label;
              selectComPort.appendChild(opt);
            }
          });
          alert(`Found ${data.ports.length} connected USB COM port(s).`);
        }
      } catch (err) {
        console.error('Error scanning COM ports:', err);
      } finally {
        btnRefreshPorts.textContent = '🔄 Refresh COM Ports';
      }
    });
  }

  if (btnConnectEsp32) {
    btnConnectEsp32.addEventListener('click', async () => {
      const port = selectComPort.value;
      btnConnectEsp32.disabled = true;
      btnConnectEsp32.textContent = '⚡ Connecting...';

      try {
        const response = await fetch('/api/connect_esp32', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ com_port: port })
        });
        const data = await response.json();
        btnConnectEsp32.disabled = false;
        btnConnectEsp32.textContent = '⚡ Connect ESP32';

        if (response.ok) {
          alert(data.message);
          if (esp32DiagMsg) esp32DiagMsg.innerHTML = `<span style="color: var(--success); font-weight:700;">${data.message}</span>`;
        } else {
          alert(data.message || 'Connection failed.');
          if (esp32DiagMsg) esp32DiagMsg.innerHTML = `<span style="color: var(--danger); font-weight:700;">⚠️ ${data.message}</span>`;
        }
      } catch (err) {
        btnConnectEsp32.disabled = false;
        btnConnectEsp32.textContent = '⚡ Connect ESP32';
        alert('Server communication error.');
      }
    });
  }

  if (btnDisconnectEsp32) {
    btnDisconnectEsp32.addEventListener('click', async () => {
      try {
        const response = await fetch('/api/disconnect_esp32', { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
          alert('ESP32 Disconnected.');
          if (esp32DiagMsg) esp32DiagMsg.textContent = 'ESP32 disconnected.';
        }
      } catch (err) {
        console.error('Error disconnecting:', err);
      }
    });
  }

  // --- 10-SECOND LIVE CAMERA ENROLLMENT SCREEN & TIMER ---
  const btnStartEnroll = document.getElementById('btn-start-enroll');
  const inputEnrollName = document.getElementById('live-enroll-name');
  const enrollCamContainer = document.getElementById('enroll-cam-container');
  const timerOverlay = document.getElementById('enroll-timer-overlay');
  const progressBox = document.getElementById('enroll-progress-box');
  const progressText = document.getElementById('enroll-status-text');
  const progressBar = document.getElementById('enroll-progress-bar');

  if (btnStartEnroll) {
    btnStartEnroll.addEventListener('click', async () => {
      const name = inputEnrollName.value.trim();
      if (!name) {
        alert('Please enter the person full name first.');
        return;
      }

      btnStartEnroll.disabled = true;
      btnStartEnroll.textContent = '⏳ Enrollment in Progress...';
      startCameraHeartbeat();
      
      if (enrollCamImg) {
        const feedUrl = enrollCamImg.getAttribute('data-src');
        enrollCamImg.src = feedUrl;
      }
      if (enrollCamContainer) enrollCamContainer.style.display = 'block';
      if (progressBox) progressBox.style.display = 'block';

      try {
        const response = await fetch('/api/start_enrollment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name })
        });

        const data = await response.json();
        if (!response.ok) {
          alert(data.error || 'Failed to start enrollment.');
          stopCameraHeartbeat();
          btnStartEnroll.disabled = false;
          btnStartEnroll.textContent = '📸 Start 10-Second Live Camera Enrollment (20 Photos)';
          if (enrollCamImg) enrollCamImg.src = '';
          if (enrollCamContainer) enrollCamContainer.style.display = 'none';
          if (progressBox) progressBox.style.display = 'none';
          return;
        }

        // Poll enrollment status and timer countdown
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch('/api/enrollment_status');
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              if (progressText) progressText.textContent = statusData.status;

              if (timerOverlay) {
                timerOverlay.textContent = `⏱️ Time Left: ${statusData.time_left}s`;
              }

              const pct = (statusData.captured / statusData.total) * 100;
              if (progressBar) progressBar.style.width = `${pct}%`;

              if (!statusData.is_enrolling) {
                clearInterval(pollInterval);
                stopCameraHeartbeat();
                if (enrollCamImg) enrollCamImg.src = '';
                btnStartEnroll.disabled = false;
                btnStartEnroll.textContent = '📸 Start 10-Second Live Camera Enrollment (20 Photos)';
                
                setTimeout(() => {
                  window.location.reload();
                }, 1500);
              }
            }
          } catch (err) {
            console.error('Error checking enrollment status:', err);
          }
        }, 250);

      } catch (err) {
        alert('Server communication error.');
        stopCameraHeartbeat();
        if (enrollCamImg) enrollCamImg.src = '';
        btnStartEnroll.disabled = false;
        btnStartEnroll.textContent = '📸 Start 10-Second Live Camera Enrollment (20 Photos)';
      }
    });
  }

  // --- AUTOMATIC CAMERA SHUTDOWN ON TAB CLOSE / UNLOAD ---
  window.addEventListener('beforeunload', () => {
    stopCameraHeartbeat();
    if (videoFeedElement) {
      videoFeedElement.src = '';
    }
    if (enrollCamImg) {
      enrollCamImg.src = '';
    }
  });
});
