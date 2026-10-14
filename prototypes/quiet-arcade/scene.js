/**
 * The quiet arcade: one small room, two rounded cabinets, a stool and the
 * lantern keeper, lit by a pendant lamp against muted violet. Everything is
 * procedural geometry; nothing is loaded from a file.
 *
 * Nothing moves on its own. The scene renders when something changes and
 * during the one short response to a selection, then goes quiet again. In
 * still mode no transform animates at all: a selection only changes light.
 */
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const COLOURS = {
  violet: 0x2b2443, wallBack: 0x463a66, wallSide: 0x3d3259, floor: 0x5b4436, rug: 0x5e4756,
  cream: 0xe8dcc8, teal: 0x3f6b72, coral: 0xd88b72, gold: 0xe6b963, ivory: 0xf4ecdd, ink: 0x151c26,
  screen: 0x1b1a2b, cushion: 0xc9a27a, stool: 0x2f2742, plant: 0x4f7a5a, pot: 0x8a5a4a,
};

const HOTSPOTS = [
  { id: 'keeper', name: 'Lantern keeper', hint: 'Press Enter to greet.' },
  { id: 'harbor', name: 'Harbor cabinet', hint: 'Press Enter to select.' },
  { id: 'demo', name: 'Demo cabinet', hint: 'Press Enter to select.' },
];

export async function start() {
  const canvas = document.getElementById('scene');
  const stage = document.getElementById('stage');
  const statusLine = document.getElementById('status');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(COLOURS.violet);
  scene.fog = new THREE.Fog(COLOURS.violet, 9, 17);

  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 40);
  const cameraHome = new THREE.Vector3(3.9, 2.55, 5.5);
  const cameraLook = new THREE.Vector3(-0.15, 0.8, -0.35);
  camera.position.copy(cameraHome);
  camera.lookAt(cameraLook);

  // ---------------------------------------------------------------- materials
  const matte = (color, roughness = 0.92) => new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  const sheen = (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.05 });
  const rounded = (w, h, d, r = 0.08, seg = 4) => new THREE.Mesh(new RoundedBoxGeometry(w, h, d, seg, r));
  const place = (mesh, x, y, z, material, shadow = true) => {
    mesh.position.set(x, y, z);
    if (material) mesh.material = material;
    mesh.castShadow = shadow;
    mesh.receiveShadow = true;
    scene.add(mesh);
    return mesh;
  };

  // ---------------------------------------------------------------- the room
  const floor = place(rounded(6.4, 0.3, 5.2, 0.1), 0, -0.15, 0, matte(COLOURS.floor, 0.9));
  floor.castShadow = false;
  const backWall = place(rounded(6.4, 3.4, 0.3, 0.1), 0, 1.55, -2.75, matte(COLOURS.wallBack, 0.95));
  const sideWall = place(rounded(0.3, 3.4, 5.2, 0.1), -3.35, 1.55, 0, matte(COLOURS.wallSide, 0.95));
  const rug = place(new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.15, 0.02, 48)), 0.35, 0.01, 0.75, matte(COLOURS.rug, 0.98), false);
  const skirting = place(rounded(6.4, 0.12, 0.08, 0.03), 0, 0.06, -2.56, matte(COLOURS.cream, 0.9), false);

  // A small framed picture and a plant keep the wall from being bare.
  place(rounded(0.9, 0.62, 0.06, 0.02), -2.25, 2.15, -2.57, matte(COLOURS.cream, 0.9));
  place(rounded(0.8, 0.52, 0.03, 0.01), -2.25, 2.15, -2.53, matte(0x5b6a8a, 0.9), false);
  const pot = place(new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.15, 0.34, 24)), -2.6, 0.17, -1.9, matte(COLOURS.pot, 0.9));
  for (const [dx, dy, dz, r] of [[0, 0.5, 0, 0.26], [-0.16, 0.42, 0.1, 0.17], [0.17, 0.44, -0.08, 0.18], [0.02, 0.68, -0.04, 0.16]]) {
    place(new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16)), pot.position.x + dx, dy + 0.1, pot.position.z + dz, matte(COLOURS.plant, 0.95));
  }

  // ------------------------------------------------------------- the cabinets
  const screenCanvas = (variant) => {
    const c = document.createElement('canvas');
    c.width = 256; c.height = 192;
    const g = c.getContext('2d');
    if (variant === 'harbor') {
      const sky = g.createLinearGradient(0, 0, 0, 192);
      sky.addColorStop(0, '#3a3568'); sky.addColorStop(0.55, '#6b6a8a'); sky.addColorStop(0.6, '#2d4a52'); sky.addColorStop(1, '#1b2f36');
      g.fillStyle = sky; g.fillRect(0, 0, 256, 192);
      g.fillStyle = '#e6b963'; g.beginPath(); g.arc(196, 76, 18, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#1b2430'; g.fillRect(0, 118, 256, 6);
    } else {
      const glow = g.createRadialGradient(128, 96, 10, 128, 96, 150);
      glow.addColorStop(0, '#33304d'); glow.addColorStop(1, '#171527');
      g.fillStyle = glow; g.fillRect(0, 0, 256, 192);
    }
    const texture = new THREE.CanvasTexture(c);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  };

  function cabinet(x, bodyColour, marqueeColour, variant) {
    const group = new THREE.Group();
    group.position.set(x, 0, -1.85);
    const body = rounded(1.0, 1.75, 0.85, 0.12, 5);
    body.position.y = 0.875; body.material = sheen(bodyColour); body.castShadow = true; body.receiveShadow = true;
    group.add(body);
    const marquee = rounded(1.06, 0.26, 0.9, 0.1, 5);
    marquee.position.set(0, 1.86, -0.02); marquee.material = sheen(marqueeColour); marquee.castShadow = true; marquee.receiveShadow = true;
    group.add(marquee);
    const bezel = rounded(0.82, 0.62, 0.06, 0.04, 4);
    bezel.position.set(0, 1.28, 0.43); bezel.material = matte(COLOURS.ink, 0.6); bezel.castShadow = true;
    group.add(bezel);
    const screenMaterial = new THREE.MeshPhysicalMaterial({
      map: screenCanvas(variant), color: 0xffffff, roughness: 0.25, metalness: 0, clearcoat: 0.8, clearcoatRoughness: 0.2,
      emissive: new THREE.Color(variant === 'harbor' ? 0x8c7a66 : 0x3a3560), emissiveMap: screenCanvas(variant), emissiveIntensity: 0.35,
    });
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.5), screenMaterial);
    screen.position.set(0, 1.28, 0.465);
    group.add(screen);
    const deck = rounded(0.96, 0.12, 0.42, 0.04, 4);
    deck.position.set(0, 0.86, 0.5); deck.rotation.x = -0.28; deck.material = sheen(COLOURS.ink); deck.castShadow = true; deck.receiveShadow = true;
    group.add(deck);
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.2, 12), matte(COLOURS.ivory, 0.7));
    stick.position.set(-0.26, 0.98, 0.5); stick.rotation.x = -0.28; stick.castShadow = true; group.add(stick);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.055, 20, 14), sheen(COLOURS.coral));
    ball.position.set(-0.26, 1.08, 0.53); ball.castShadow = true; group.add(ball);
    for (const [bx, colour] of [[0.1, COLOURS.ivory], [0.26, COLOURS.coral]]) {
      const button = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.04, 20), sheen(colour));
      button.position.set(bx, 0.93, 0.5); button.rotation.x = -0.28; button.castShadow = true; group.add(button);
    }
    const base = rounded(1.0, 0.14, 0.85, 0.05, 4);
    base.position.y = 0.07; base.material = matte(COLOURS.ink, 0.9); base.receiveShadow = true; group.add(base);
    scene.add(group);
    return { group, screenMaterial, body };
  }
  const harbor = cabinet(-0.35, COLOURS.cream, COLOURS.coral, 'harbor');
  const demo = cabinet(1.05, COLOURS.teal, COLOURS.gold, 'demo');

  // ----------------------------------------------------------------- the stool
  const stool = new THREE.Group();
  stool.position.set(0.35, 0, -0.55);
  const stoolBase = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 0.42, 32), matte(COLOURS.stool, 0.9));
  stoolBase.position.y = 0.21; stoolBase.castShadow = true; stoolBase.receiveShadow = true; stool.add(stoolBase);
  const cushion = rounded(0.6, 0.18, 0.6, 0.09, 5);
  cushion.position.y = 0.5; cushion.material = matte(COLOURS.cushion, 0.98); cushion.castShadow = true; cushion.receiveShadow = true; stool.add(cushion);
  scene.add(stool);

  // ---------------------------------------------------------- the lantern keeper
  // A pebble of a figure: a bell body in the coral robe, a hooded ivory head
  // with closed eyes, and a lantern on a short pole held out to one side.
  const keeper = new THREE.Group();
  keeper.position.set(-1.15, 0, 0.55);
  keeper.rotation.y = 0.55;
  const bow = new THREE.Group();
  keeper.add(bow);
  const profile = [];
  for (let i = 0; i <= 12; i += 1) {
    const t = i / 12;
    const y = t * 0.78;
    const r = 0.36 * Math.pow(1 - t, 0.55) * (1 - 0.18 * Math.sin(t * Math.PI)) + 0.08 * t;
    profile.push(new THREE.Vector2(Math.max(r, 0.12), y));
  }
  profile.push(new THREE.Vector2(0.001, 0.8));
  const robe = new THREE.Mesh(new THREE.LatheGeometry(profile, 48), matte(COLOURS.coral, 0.97));
  robe.castShadow = true; robe.receiveShadow = true; bow.add(robe);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.27, 40, 28), matte(COLOURS.ivory, 0.9));
  head.position.set(0, 0.98, 0.02); head.castShadow = true; head.receiveShadow = true; bow.add(head);
  const hood = new THREE.Mesh(new THREE.SphereGeometry(0.31, 40, 28, Math.PI * 0.75, Math.PI * 1.5, 0, Math.PI * 0.82), matte(COLOURS.coral, 0.97));
  hood.position.set(0, 1.0, -0.03); hood.castShadow = true; bow.add(hood);
  for (const sx of [-0.1, 0.1]) {
    const eye = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.012, 8, 16, Math.PI), matte(COLOURS.ink, 0.6));
    eye.position.set(sx, 0.97, 0.26); bow.add(eye);
  }
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 1.0, 12), matte(0x6e5a4a, 0.8));
  pole.position.set(0.42, 0.62, 0.1); pole.castShadow = true; bow.add(pole);
  const lanternCage = new THREE.Group();
  lanternCage.position.set(0.42, 1.0, 0.1);
  const lanternGlass = new THREE.Mesh(new THREE.SphereGeometry(0.09, 24, 16), new THREE.MeshStandardMaterial({
    color: 0xffd9a8, emissive: 0xffb36b, emissiveIntensity: 1.4, roughness: 0.5,
  }));
  lanternCage.add(lanternGlass);
  for (const ry of [0, Math.PI / 2]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.105, 0.008, 6, 32), matte(COLOURS.ink, 0.6));
    ring.rotation.y = ry; lanternCage.add(ring);
  }
  const lanternCap = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.06, 20), matte(COLOURS.ink, 0.6));
  lanternCap.position.y = 0.13; lanternCage.add(lanternCap);
  const lanternLight = new THREE.PointLight(0xffb36b, 2.2, 2.6, 2);
  lanternCage.add(lanternLight);
  bow.add(lanternCage);
  scene.add(keeper);

  // ----------------------------------------------------------------- the lights
  scene.add(new THREE.HemisphereLight(0x7a6aa8, 0x3a2a22, 0.75));
  const key = new THREE.DirectionalLight(0xffd9b3, 2.1);
  key.position.set(3.2, 5.2, 2.4); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 6; key.shadow.bias = -0.0006;
  Object.assign(key.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 1, far: 16 });
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8a7cc9, 0.55);
  fill.position.set(-4, 3, -2); scene.add(fill);
  const pendant = new THREE.Group();
  pendant.position.set(0.2, 3.2, 0.3);
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.9, 8), matte(COLOURS.ink, 0.8));
  cord.position.y = -0.45; pendant.add(cord);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.34, 32, 1, true), new THREE.MeshStandardMaterial({ color: COLOURS.cream, roughness: 0.9, side: THREE.DoubleSide }));
  shade.position.y = -1.05; shade.castShadow = true; pendant.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 12), new THREE.MeshStandardMaterial({ color: 0xfff1d6, emissive: 0xffc28a, emissiveIntensity: 2.2 }));
  bulb.position.y = -1.12; pendant.add(bulb);
  const lamp = new THREE.PointLight(0xffc28a, 24, 9, 2);
  lamp.position.y = -1.2; lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.002;
  pendant.add(lamp);
  scene.add(pendant);

  // Soft contact shadows under the things that stand on the floor.
  const contact = (() => {
    const c = document.createElement('canvas'); c.width = 128; c.height = 128;
    const g = c.getContext('2d');
    const grad = g.createRadialGradient(64, 64, 8, 64, 64, 64);
    grad.addColorStop(0, 'rgba(0,0,0,0.55)'); grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  })();
  for (const [x, z, s] of [[keeper.position.x, keeper.position.z, 1.1], [stool.position.x, stool.position.z, 0.9], [harbor.group.position.x, harbor.group.position.z + 0.1, 1.5], [demo.group.position.x, demo.group.position.z + 0.1, 1.5]]) {
    const disc = new THREE.Mesh(new THREE.PlaneGeometry(s, s), new THREE.MeshBasicMaterial({ map: contact, transparent: true, depthWrite: false }));
    disc.rotation.x = -Math.PI / 2; disc.position.set(x, 0.012, z); scene.add(disc);
  }

  // Focus and selection rings on the floor, never on the object itself.
  const ringFor = (colour, inner, outer) => {
    const mesh = new THREE.Mesh(new THREE.RingGeometry(inner, outer, 64), new THREE.MeshBasicMaterial({ color: colour, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }));
    mesh.rotation.x = -Math.PI / 2; mesh.position.y = 0.02; mesh.visible = false; scene.add(mesh); return mesh;
  };
  const focusRing = ringFor(COLOURS.gold, 0.62, 0.68);
  const selectRing = ringFor(COLOURS.ivory, 0.5, 0.56);
  const anchors = {
    keeper: { object: keeper, floor: new THREE.Vector3(keeper.position.x, 0, keeper.position.z), radius: 0.6 },
    harbor: { object: harbor.group, floor: new THREE.Vector3(harbor.group.position.x, 0, harbor.group.position.z + 0.15), radius: 0.75 },
    demo: { object: demo.group, floor: new THREE.Vector3(demo.group.position.x, 0, demo.group.position.z + 0.15), radius: 0.75 },
  };
  const scaleRing = (ring, radius) => { ring.scale.setScalar(radius / 0.65); };

  // ------------------------------------------------------------------- state
  const state = {
    ready: false, focused: null, selected: null, still: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    lastResponse: null, panel: null, demoLit: false, frames: 0,
    // The peaks of the last greeting and whether it has finished, recorded by
    // the animation itself so a slow renderer cannot hide them.
    responsePeak: null, responseDone: true,
  };
  const animations = new Set();
  let rafPending = false;
  const ease = (t) => 1 - Math.pow(1 - t, 3);

  function animate(duration, step, done) {
    const startAt = performance.now();
    const run = { tick(now) {
      const t = Math.min(1, (now - startAt) / duration);
      step(ease(t), t);
      if (t >= 1) { animations.delete(run); done?.(); }
    } };
    animations.add(run);
    requestFrame();
  }
  function requestFrame() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame((now) => {
      rafPending = false;
      for (const run of [...animations]) run.tick(now);
      renderer.render(scene, camera);
      state.frames += 1;
      if (animations.size) requestFrame();
    });
  }

  function resize() {
    const { clientWidth: w, clientHeight: h } = stage;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    requestFrame();
  }
  new ResizeObserver(resize).observe(stage);
  resize();

  function say(text) { statusLine.textContent = text; }
  function hotspot(id) { return HOTSPOTS.find((one) => one.id === id); }

  function setFocus(id) {
    state.focused = id;
    if (id) {
      const a = anchors[id];
      focusRing.visible = true; focusRing.position.set(a.floor.x, 0.02, a.floor.z); scaleRing(focusRing, a.radius);
      const spot = hotspot(id);
      say(`${spot.name}. ${spot.hint}`);
    } else {
      focusRing.visible = false;
    }
    requestFrame();
  }

  const cameraTarget = cameraHome.clone();
  function moveCamera(toward) {
    const target = toward ? cameraHome.clone().lerp(toward.clone().setY(cameraHome.y - 0.2), 0.05) : cameraHome.clone();
    if (state.still) { camera.position.copy(target); camera.lookAt(cameraLook); requestFrame(); return; }
    const from = camera.position.clone();
    animate(650, (k) => { camera.position.lerpVectors(from, target, k); camera.lookAt(cameraLook); });
  }

  function greet() {
    // One restrained response: a short bow with the lantern brightening, or in
    // still mode the lantern alone. Never repeated on its own.
    state.lastResponse = state.still ? 'glow' : 'bow';
    state.responsePeak = { bow: 0, lantern: lanternLight.intensity };
    state.responseDone = false;
    say('The lantern keeper bows.');
    const record = () => {
      state.responsePeak.bow = Math.max(state.responsePeak.bow, bow.rotation.x);
      state.responsePeak.lantern = Math.max(state.responsePeak.lantern, lanternLight.intensity);
    };
    const finish = () => { state.responseDone = true; };
    const brighten = (k) => { const pulse = Math.sin(k * Math.PI); lanternLight.intensity = 2.2 + 2.6 * pulse; lanternGlass.material.emissiveIntensity = 1.4 + 1.2 * pulse; record(); };
    if (state.still) { animate(900, brighten, finish); return; }
    animate(1100, (k, t) => { brighten(t); bow.rotation.x = 0.2 * Math.sin(Math.min(1, t * 1.15) * Math.PI); record(); }, finish);
  }

  function select(id) {
    if (!id) {
      state.selected = null; selectRing.visible = false; moveCamera(null);
      if (state.focused) setFocus(state.focused); else say('');
      return;
    }
    state.selected = id;
    const a = anchors[id];
    selectRing.visible = true; selectRing.position.set(a.floor.x, 0.02, a.floor.z); scaleRing(selectRing, a.radius);
    if (id === 'keeper') { greet(); moveCamera(null); }
    else { say(`${hotspot(id).name}, selected.`); moveCamera(a.object.position); }
    requestFrame();
  }

  function setStill(on) {
    state.still = on;
    for (const run of animations) animations.delete(run);
    state.responseDone = true;
    bow.rotation.x = 0; lanternLight.intensity = 2.2; lanternGlass.material.emissiveIntensity = 1.4;
    camera.position.copy(cameraHome); camera.lookAt(cameraLook);
    requestFrame();
  }

  function setDemoLit(on) {
    state.demoLit = on;
    demo.screenMaterial.emissiveIntensity = on ? 1.1 : 0.35;
    demo.screenMaterial.emissive.set(on ? 0x8a7aa0 : 0x3a3560);
    requestFrame();
  }

  // ---------------------------------------------------------------- the keys
  const menuButtons = () => [...document.querySelectorAll('.menu button')];
  stage.addEventListener('keydown', (event) => {
    const order = HOTSPOTS.map((one) => one.id);
    const index = order.indexOf(state.focused);
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      const next = index < 0 ? 0 : (index + (event.key === 'ArrowRight' ? 1 : order.length - 1)) % order.length;
      setFocus(order[next]); event.preventDefault();
    } else if (event.key === 'Enter' || event.key === ' ') {
      if (state.focused) select(state.focused); else setFocus(order[0]);
      event.preventDefault();
    } else if (event.key === 'Escape') {
      if (state.selected) select(null); else setFocus(null);
      event.preventDefault();
    } else if (event.key === 'ArrowUp') {
      menuButtons()[0]?.focus(); event.preventDefault();
    }
  });
  stage.addEventListener('focus', () => { if (!state.focused) setFocus(HOTSPOTS[0].id); });
  document.querySelector('.menu').addEventListener('keydown', (event) => {
    const buttons = menuButtons();
    const i = buttons.indexOf(document.activeElement);
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      buttons[(i + (event.key === 'ArrowRight' ? 1 : buttons.length - 1)) % buttons.length]?.focus(); event.preventDefault();
    } else if (event.key === 'ArrowDown') { stage.focus(); event.preventDefault(); }
  });

  // -------------------------------------------------------------- the pointer
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const pick = (event) => {
    const rect = canvas.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    for (const [id, a] of Object.entries(anchors)) {
      if (raycaster.intersectObject(a.object, true).length) return id;
    }
    return null;
  };
  canvas.addEventListener('pointermove', (event) => { const id = pick(event); if (id !== state.focused) setFocus(id); canvas.style.cursor = id ? 'pointer' : 'default'; });
  canvas.addEventListener('click', (event) => { const id = pick(event); stage.focus({ preventScroll: true }); if (id) { setFocus(id); select(id); } else if (state.selected) select(null); });

  // ------------------------------------------------------- for the verifier
  window.__quietArcade = {
    get ready() { return state.ready; },
    state: () => ({ ...state, camera: camera.position.toArray(), bow: bow.rotation.x, lantern: lanternLight.intensity }),
    focus: setFocus, select, setStill, setDemoLit,
    pickAt(x, y) { return pick({ clientX: x, clientY: y }); },
    screenPosition(id) {
      const a = anchors[id];
      const v = a.object.position.clone().setY(0.9).project(camera);
      const rect = canvas.getBoundingClientRect();
      return { x: rect.left + ((v.x + 1) / 2) * rect.width, y: rect.top + ((1 - v.y) / 2) * rect.height };
    },
  };
  renderer.render(scene, camera);
  state.ready = true;
  say('');
  return window.__quietArcade;
}
