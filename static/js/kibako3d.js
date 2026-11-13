import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

/**
 * Atelier Kibako — Moteur CAD 3D WebGL (Three.js)
 * Modélisation procédurale d'une boîte à musique en bois massif + cylindre laiton + peigne 18/30 lames.
 */
const WOOD_PALETTES = {
  "Cerisier Sakura": { base: "#9e5034", grain: "#6e2e1a", roughness: 0.42 },
  "Noyer Kurumi": { base: "#4d3527", grain: "#2b1b12", roughness: 0.46 },
  "Cyprès Hinoki": { base: "#dcc198", grain: "#b89668", roughness: 0.55 },
  "Chêne Ébénisé": { base: "#272320", grain: "#12100e", roughness: 0.38 },
  "Érable Ondé": { base: "#c99255", grain: "#96632f", roughness: 0.40 },
  "Bambou Torréfié": { base: "#7c5534", grain: "#4a3019", roughness: 0.48 },
  "Acajou Maritime": { base: "#6f2e22", grain: "#42160f", roughness: 0.36 },
  "Cèdre Fumé": { base: "#5e4332", grain: "#382419", roughness: 0.50 },
};

function createWoodTexture(woodName) {
  const palette = WOOD_PALETTES[woodName] || WOOD_PALETTES["Noyer Kurumi"];
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = palette.base;
  ctx.fillRect(0, 0, 512, 512);

  // Veines procédurales du bois
  ctx.strokeStyle = palette.grain;
  for (let i = 0; i < 95; i++) {
    ctx.globalAlpha = 0.08 + (i % 5) * 0.035;
    ctx.lineWidth = 1 + (i % 3);
    ctx.beginPath();
    const yBase = (i / 95) * 512;
    ctx.moveTo(0, yBase);
    for (let x = 0; x <= 512; x += 32) {
      const wave = Math.sin(x * 0.025 + i * 0.4) * 6;
      ctx.lineTo(x, yBase + wave);
    }
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return { texture, roughness: palette.roughness };
}

function initKibako3D(container) {
  const width = container.clientWidth || 600;
  const height = container.clientHeight || 420;
  const initialWood = container.dataset.wood || "Noyer Kurumi";
  const mechanismLabel = container.dataset.mechanism || "18 lames";
  const tineCount = mechanismLabel.includes("30") ? 30 : 18;

  let melodyNotes = [];
  const notesEl = document.getElementById("melody-notes-data");
  if (notesEl) {
    try {
      melodyNotes = JSON.parse(notesEl.textContent || "[]");
    } catch (_) {
      melodyNotes = [];
    }
  }

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#181512");
  scene.fog = new THREE.FogExp2("#181512", 0.045);

  const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
  camera.position.set(4.8, 3.8, 5.4);

  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  container.innerHTML = "";
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.minDistance = 3.2;
  controls.maxDistance = 12;
  controls.maxPolarAngle = Math.PI / 2 - 0.05;

  // Éclairage studio d'atelier
  const ambient = new THREE.AmbientLight("#fff3e0", 0.65);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight("#ffe6c2", 2.4);
  keyLight.position.set(5, 8, 5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight("#9ec5ff", 0.85);
  rimLight.position.set(-5, 4, -4);
  scene.add(rimLight);

  // Grille technique CAD au sol
  const grid = new THREE.GridHelper(18, 24, "#b8863b", "#2d2823");
  grid.position.y = -0.02;
  scene.add(grid);

  // Matériaux
  let { texture: woodTex, roughness: woodRough } = createWoodTexture(initialWood);
  const woodMat = new THREE.MeshPhysicalMaterial({
    map: woodTex,
    roughness: woodRough,
    metalness: 0.05,
    clearcoat: 0.35,
    clearcoatRoughness: 0.25,
  });

  const brassMat = new THREE.MeshStandardMaterial({
    color: "#d4a64a",
    metalness: 0.88,
    roughness: 0.22,
  });

  const steelMat = new THREE.MeshStandardMaterial({
    color: "#cfd4da",
    metalness: 0.92,
    roughness: 0.18,
  });

  const velvetMat = new THREE.MeshStandardMaterial({
    color: "#221b18",
    roughness: 0.95,
  });

  // Groupe principal de la boîte
  const boxGroup = new THREE.Group();
  scene.add(boxGroup);

  // Base du coffret (4 parois + fond)
  const baseGroup = new THREE.Group();
  boxGroup.add(baseGroup);

  const floorMesh = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.14, 2.4), woodMat);
  floorMesh.position.y = 0.07;
  floorMesh.receiveShadow = true;
  floorMesh.castShadow = true;
  baseGroup.add(floorMesh);

  const velvetMesh = new THREE.Mesh(new THREE.BoxGeometry(3.1, 0.04, 2.1), velvetMat);
  velvetMesh.position.y = 0.16;
  baseGroup.add(velvetMesh);

  const wallSpecs = [
    { size: [3.4, 0.95, 0.16], pos: [0, 0.545, 1.12] },
    { size: [3.4, 0.95, 0.16], pos: [0, 0.545, -1.12] },
    { size: [0.16, 0.95, 2.08], pos: [-1.62, 0.545, 0] },
    { size: [0.16, 0.95, 2.08], pos: [1.62, 0.545, 0] },
  ];
  wallSpecs.forEach((w) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...w.size), woodMat);
    mesh.position.set(...w.pos);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    baseGroup.add(mesh);
  });

  // Couvercle articulé
  const lidPivot = new THREE.Group();
  lidPivot.position.set(0, 1.02, -1.12);
  boxGroup.add(lidPivot);

  const lidMesh = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.18, 2.4), woodMat);
  lidMesh.position.set(0, 0.09, 1.12);
  lidMesh.castShadow = true;
  lidPivot.add(lidMesh);

  // Plaque laiton gravée sous le couvercle
  const inlayMesh = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.02, 1.6), brassMat);
  inlayMesh.position.set(0, -0.005, 1.12);
  lidPivot.add(inlayMesh);

  lidPivot.rotation.x = -Math.PI * 0.42; // Ouvert par défaut

  // Mécanisme musical interne (Platine + Cylindre + Picots + Peigne)
  const mechGroup = new THREE.Group();
  mechGroup.position.set(0, 0.22, 0);
  boxGroup.add(mechGroup);

  const plateMesh = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.06, 1.45), brassMat);
  plateMesh.position.set(0, 0.03, 0);
  plateMesh.castShadow = true;
  mechGroup.add(plateMesh);

  // Barillet / moteur à ressort
  const springDrum = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.34, 28), brassMat);
  springDrum.position.set(-0.85, 0.26, -0.25);
  springDrum.castShadow = true;
  mechGroup.add(springDrum);

  // Roue d'engrenage
  const gearWheel = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.05, 16), brassMat);
  gearWheel.rotation.x = Math.PI / 2;
  gearWheel.position.set(-0.38, 0.32, -0.18);
  mechGroup.add(gearWheel);

  // Cylindre rotatif picoté
  const cylinderGroup = new THREE.Group();
  cylinderGroup.position.set(0.35, 0.34, -0.22);
  mechGroup.add(cylinderGroup);

  const cylinderMesh = new THREE.Mesh(
    new THREE.CylinderGeometry(0.21, 0.21, 1.35, 32),
    brassMat
  );
  cylinderMesh.rotation.z = Math.PI / 2;
  cylinderMesh.castShadow = true;
  cylinderGroup.add(cylinderMesh);

  // Picots sur le cylindre basés sur les notes ou générés procéduralement
  const pinGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.05, 6);
  const pinCount = Math.max(24, melodyNotes.length * 2);
  for (let i = 0; i < pinCount; i++) {
    const angle = (i / pinCount) * Math.PI * 2;
    const xPos = -0.58 + ((i * 7) % 18) * (1.16 / 18);
    const pin = new THREE.Mesh(pinGeo, steelMat);
    pin.position.set(xPos, Math.cos(angle) * 0.22, Math.sin(angle) * 0.22);
    pin.rotation.x = angle;
    cylinderGroup.add(pin);
  }

  // Peigne métallique (18 ou 30 lames individuelles animables)
  const combGroup = new THREE.Group();
  combGroup.position.set(0.35, 0.14, 0.36);
  mechGroup.add(combGroup);

  const combBase = new THREE.Mesh(new THREE.BoxGeometry(1.42, 0.11, 0.28), brassMat);
  combBase.position.set(0, 0, 0.14);
  combGroup.add(combBase);

  const tines = [];
  const combWidth = 1.24;
  const tineStep = combWidth / tineCount;
  for (let i = 0; i < tineCount; i++) {
    const tineLen = 0.44 - (i / tineCount) * 0.12;
    const tineGeo = new THREE.BoxGeometry(tineStep * 0.65, 0.018, tineLen);
    tineGeo.translate(0, 0, -tineLen / 2);
    const tine = new THREE.Mesh(tineGeo, steelMat);
    tine.position.set(-combWidth / 2 + i * tineStep + tineStep / 2, 0.06, 0.04);
    combGroup.add(tine);
    tines.push(tine);
  }

  // Clef de remontage latérale
  const keyShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.45, 12), brassMat);
  keyShaft.rotation.z = Math.PI / 2;
  keyShaft.position.set(-1.82, 0.45, 0);
  baseGroup.add(keyShaft);

  // État interactif
  let isPlayingAudio = false;
  let isExploded = false;
  let isOpen = true;
  let isWireframe = false;
  let autoRotate = true;

  // Boutons de contrôle CAD
  const rootCard = container.closest(".cad-stage") || document;
  const btnExplode = rootCard.querySelector("[data-cad='explode']");
  const btnLid = rootCard.querySelector("[data-cad='lid']");
  const btnWire = rootCard.querySelector("[data-cad='wireframe']");
  const btnReset = rootCard.querySelector("[data-cad='reset']");
  const woodSelect = rootCard.querySelector("[data-cad='wood-select']");

  function toggleExplode() {
    isExploded = !isExploded;
    if (btnExplode) btnExplode.classList.toggle("active", isExploded);
    const targetMechY = isExploded ? 1.15 : 0.22;
    const targetLidY = isExploded ? 1.85 : 1.02;
    if (window.gsap) {
      window.gsap.to(mechGroup.position, { y: targetMechY, duration: 0.7, ease: "power3.out" });
      window.gsap.to(lidPivot.position, { y: targetLidY, duration: 0.7, ease: "power3.out" });
    } else {
      mechGroup.position.y = targetMechY;
      lidPivot.position.y = targetLidY;
    }
  }

  function toggleLid() {
    isOpen = !isOpen;
    if (btnLid) btnLid.classList.toggle("active", !isOpen);
    const targetRot = isOpen ? -Math.PI * 0.42 : 0;
    if (window.gsap) {
      window.gsap.to(lidPivot.rotation, { x: targetRot, duration: 0.75, ease: "power2.inOut" });
    } else {
      lidPivot.rotation.x = targetRot;
    }
  }

  function toggleWireframe() {
    isWireframe = !isWireframe;
    if (btnWire) btnWire.classList.toggle("active", isWireframe);
    [woodMat, brassMat, steelMat, velvetMat].forEach((m) => {
      m.wireframe = isWireframe;
    });
  }

  function resetCamera() {
    if (window.gsap) {
      window.gsap.to(camera.position, { x: 4.8, y: 3.8, z: 5.4, duration: 0.7, ease: "power2.out" });
    } else {
      camera.position.set(4.8, 3.8, 5.4);
    }
    controls.target.set(0, 0.6, 0);
  }

  if (btnExplode) btnExplode.addEventListener("click", toggleExplode);
  if (btnLid) btnLid.addEventListener("click", toggleLid);
  if (btnWire) btnWire.addEventListener("click", toggleWireframe);
  if (btnReset) btnReset.addEventListener("click", resetCamera);

  if (woodSelect) {
    woodSelect.addEventListener("change", (e) => {
      const next = createWoodTexture(e.target.value);
      woodMat.map = next.texture;
      woodMat.roughness = next.roughness;
      woodMat.needsUpdate = true;
    });
  }

  // Synchronisation avec le lecteur audio Web Audio API
  window.addEventListener("kibako:play-start", () => {
    isPlayingAudio = true;
    autoRotate = false;
  });

  window.addEventListener("kibako:play-stop", () => {
    isPlayingAudio = false;
    autoRotate = true;
    tines.forEach((t) => (t.rotation.x = 0));
  });

  window.addEventListener("kibako:note-pluck", (e) => {
    const freq = e.detail?.freq || 523;
    const idx = Math.min(
      tines.length - 1,
      Math.max(0, Math.round(((freq - 250) / 800) * (tines.length - 1)))
    );
    const tine = tines[idx];
    if (tine && window.gsap) {
      window.gsap.fromTo(
        tine.rotation,
        { x: -0.18 },
        { x: 0, duration: 0.45, ease: "elastic.out(1.2, 0.35)" }
      );
    }
  });

  // Boucle de rendu 60fps
  const clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();

    if (isPlayingAudio) {
      cylinderGroup.rotation.x += dt * 1.45;
      gearWheel.rotation.z -= dt * 2.2;
      keyShaft.rotation.x += dt * 1.1;
    } else if (autoRotate) {
      boxGroup.rotation.y += dt * 0.18;
    }

    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // ResizeObserver pour adaptation fluide
  const ro = new ResizeObserver(() => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w > 0 && h > 0) {
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
  });
  ro.observe(container);
}

document.querySelectorAll("[data-kibako-3d]").forEach((el) => initKibako3D(el));
