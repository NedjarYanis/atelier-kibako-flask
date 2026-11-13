/**
 * Atelier Kibako — Lecteur Web Audio API simulant les lames d'une boîte à musique
 */
(function () {
  const playerRoot = document.getElementById("musicbox-player");
  if (!playerRoot) return;

  const notesDataEl = document.getElementById("melody-notes-data");
  const playBtn = document.getElementById("mb-play-btn");
  const stopBtn = document.getElementById("mb-stop-btn");
  const noteReadout = document.getElementById("mb-note-readout");
  const combEl = document.getElementById("mb-comb");

  let notes = [];
  try {
    notes = JSON.parse(notesDataEl.textContent || "[]");
  } catch (e) {
    notes = [];
  }

  // Génère 16 lames visuelles pour le peigne métallique
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
  let isPlaying = false;
  let timers = [];

  function pluckTine(freq, duration) {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContextClass();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }

    const now = audioCtx.currentTime;

    // Fondamentale cristalline (onde sinusoïdale) + harmonique métallique douce
    const osc1 = audioCtx.createOscillator();
    const osc2 = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    const harmonicGain = audioCtx.createGain();

    osc1.type = "sine";
    osc1.frequency.setValueAtTime(freq, now);

    osc2.type = "triangle";
    osc2.frequency.setValueAtTime(freq * 2, now);

    // Enveloppe percussive typique d'une lame pincée par un picot de cylindre
    gainNode.gain.setValueAtTime(0.001, now);
    gainNode.gain.exponentialRampToValueAtTime(0.28, now + 0.012);
    gainNode.gain.exponentialRampToValueAtTime(0.0008, now + Math.max(0.8, duration * 1.9));

    harmonicGain.gain.setValueAtTime(0.06, now);
    harmonicGain.gain.exponentialRampToValueAtTime(0.0005, now + 0.25);

    osc1.connect(gainNode);
    osc2.connect(harmonicGain);
    harmonicGain.connect(gainNode);
    gainNode.connect(audioCtx.destination);

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
    tines.forEach((t) => t.classList.remove("active"));
    if (playBtn) playBtn.textContent = "▶ Écouter la mélodie";
    if (noteReadout) noteReadout.textContent = "Prêt";
  }

  function startPlayback() {
    if (!notes.length) return;
    if (isPlaying) {
      stopPlayback();
      return;
    }

    isPlaying = true;
    if (playBtn) playBtn.textContent = "⏸ Lecture en cours…";

    let elapsedMs = 0;
    notes.forEach((item, index) => {
      const tId = setTimeout(() => {
        if (!isPlaying) return;
        pluckTine(item.freq, item.dur || 0.45);
        highlightTine(item.freq);
        if (noteReadout) {
          noteReadout.textContent = `Note ${index + 1}/${notes.length} · ${item.note}`;
        }
      }, elapsedMs);
      timers.push(tId);
      elapsedMs += Math.round((item.dur || 0.45) * 1000);
    });

    const endTimer = setTimeout(() => {
      stopPlayback();
    }, elapsedMs + 450);
    timers.push(endTimer);
  }

  if (playBtn) playBtn.addEventListener("click", startPlayback);
  if (stopBtn) stopBtn.addEventListener("click", stopPlayback);
})();
