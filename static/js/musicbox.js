/**
 * Atelier Kibako — Synthétiseur Web Audio API + Oscilloscope DSP + Synchro 3D
 */
(function () {
  const playerRoot = document.getElementById("musicbox-player");
  if (!playerRoot) return;

  const notesDataEl = document.getElementById("melody-notes-data");
  const playBtn = document.getElementById("mb-play-btn");
  const stopBtn = document.getElementById("mb-stop-btn");
  const tempoInput = document.getElementById("mb-tempo");
  const tempoVal = document.getElementById("mb-tempo-val");
  const noteReadout = document.getElementById("mb-note-readout");
  const combEl = document.getElementById("mb-comb");
  const scopeCanvas = document.getElementById("mb-scope");
  const scopeCtx = scopeCanvas ? scopeCanvas.getContext("2d") : null;

  let notes = [];
  try {
    notes = JSON.parse(notesDataEl.textContent || "[]");
  } catch (e) {
    notes = [];
  }

  const tines = [];
  if (combEl) {
    combEl.innerHTML = "";
    for (let i = 0; i < 16; i++) {
      const tine = document.createElement("div");
      tine.className = "comb-tine";
      tine.style.height = `${35 + ((i * 17) % 45)}%`;
      combEl.appendChild(tine);
      tines.push(tine);
    }
  }

  let audioCtx = null;
  let analyser = null;
  let masterGain = null;
  let isPlaying = false;
  let timers = [];
  let rafId = null;

  function ensureAudioGraph() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContextClass();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      masterGain = audioCtx.createGain();
      masterGain.gain.value = 0.85;
      masterGain.connect(analyser);
      analyser.connect(audioCtx.destination);
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
  }

  function drawScope() {
    if (!scopeCtx || !analyser) return;
    const w = scopeCanvas.width;
    const h = scopeCanvas.height;
    const bufferLen = analyser.frequencyBinCount;
    const timeData = new Uint8Array(bufferLen);
    const freqData = new Uint8Array(bufferLen);

    function renderFrame() {
      if (!isPlaying) {
        scopeCtx.clearRect(0, 0, w, h);
        scopeCtx.strokeStyle = "rgba(230, 190, 122, 0.25)";
        scopeCtx.beginPath();
        scopeCtx.moveTo(0, h / 2);
        scopeCtx.lineTo(w, h / 2);
        scopeCtx.stroke();
        return;
      }

      rafId = requestAnimationFrame(renderFrame);
      analyser.getByteTimeDomainData(timeData);
      analyser.getByteFrequencyData(freqData);

      scopeCtx.fillStyle = "rgba(20, 17, 14, 0.35)";
      scopeCtx.fillRect(0, 0, w, h);

      // Spectre FFT en arrière-plan
      const barWidth = w / 32;
      for (let i = 0; i < 32; i++) {
        const val = freqData[i] / 255;
        const barH = val * h * 0.85;
        scopeCtx.fillStyle = "rgba(184, 134, 59, 0.28)";
        scopeCtx.fillRect(i * barWidth, h - barH, barWidth - 2, barH);
      }

      // Forme d'onde temporelle
      scopeCtx.lineWidth = 2;
      scopeCtx.strokeStyle = "#f2c879";
      scopeCtx.beginPath();
      const sliceWidth = w / bufferLen;
      let x = 0;
      for (let i = 0; i < bufferLen; i++) {
        const v = timeData[i] / 128.0;
        const y = (v * h) / 2;
        if (i === 0) scopeCtx.moveTo(x, y);
        else scopeCtx.lineTo(x, y);
        x += sliceWidth;
      }
      scopeCtx.stroke();
    }
    renderFrame();
  }

  function pluckTine(freq, duration) {
    ensureAudioGraph();
    const now = audioCtx.currentTime;

    const osc1 = audioCtx.createOscillator();
    const osc2 = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    const harmonicGain = audioCtx.createGain();

    osc1.type = "sine";
    osc1.frequency.setValueAtTime(freq, now);

    osc2.type = "triangle";
    osc2.frequency.setValueAtTime(freq * 2, now);

    gainNode.gain.setValueAtTime(0.001, now);
    gainNode.gain.exponentialRampToValueAtTime(0.28, now + 0.012);
    gainNode.gain.exponentialRampToValueAtTime(0.0008, now + Math.max(0.8, duration * 1.9));

    harmonicGain.gain.setValueAtTime(0.06, now);
    harmonicGain.gain.exponentialRampToValueAtTime(0.0005, now + 0.25);

    osc1.connect(gainNode);
    osc2.connect(harmonicGain);
    harmonicGain.connect(gainNode);
    gainNode.connect(masterGain);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + Math.max(0.9, duration * 2.0));
    osc2.stop(now + 0.3);
  }

  function highlightTine(freq) {
    if (!tines.length) return;
    tines.forEach((t) => t.classList.remove("active"));
    const idx = Math.min(
      tines.length - 1,
      Math.max(0, Math.round(((freq - 250) / 800) * (tines.length - 1)))
    );
    tines[idx].classList.add("active");
    setTimeout(() => tines[idx].classList.remove("active"), 260);
  }

  function stopPlayback() {
    isPlaying = false;
    timers.forEach((id) => clearTimeout(id));
    timers = [];
    if (rafId) cancelAnimationFrame(rafId);
    tines.forEach((t) => t.classList.remove("active"));
    if (playBtn) playBtn.textContent = "▶ Écouter la mélodie";
    if (noteReadout) noteReadout.textContent = "Prêt";
    window.dispatchEvent(new CustomEvent("kibako:play-stop"));
  }

  function startPlayback() {
    if (!notes.length) return;
    if (isPlaying) {
      stopPlayback();
      return;
    }

    ensureAudioGraph();
    isPlaying = true;
    if (playBtn) playBtn.textContent = "⏸ Lecture en cours…";
    window.dispatchEvent(new CustomEvent("kibako:play-start"));
    drawScope();

    const speed = tempoInput ? parseFloat(tempoInput.value) || 1.0 : 1.0;
    let elapsedMs = 0;
    notes.forEach((item, index) => {
      const dur = (item.dur || 0.45) / speed;
      const tId = setTimeout(() => {
        if (!isPlaying) return;
        pluckTine(item.freq, dur);
        highlightTine(item.freq);
        window.dispatchEvent(
          new CustomEvent("kibako:note-pluck", { detail: { freq: item.freq, note: item.note } })
        );
        if (noteReadout) {
          noteReadout.textContent = `${item.note} (${Math.round(item.freq)} Hz) · ${index + 1}/${notes.length}`;
        }
      }, elapsedMs);
      timers.push(tId);
      elapsedMs += Math.round(dur * 1000);
    });

    const endTimer = setTimeout(() => {
      stopPlayback();
    }, elapsedMs + 450);
    timers.push(endTimer);
  }

  if (tempoInput && tempoVal) {
    tempoInput.addEventListener("input", () => {
      tempoVal.textContent = `${parseFloat(tempoInput.value).toFixed(2)}×`;
    });
  }
  if (playBtn) playBtn.addEventListener("click", startPlayback);
  if (stopBtn) stopBtn.addEventListener("click", stopPlayback);
})();
