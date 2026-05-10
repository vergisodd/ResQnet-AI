import * as THREE from "./vendor/three/three.module.js";

const canvas = document.getElementById("hero3d-canvas");

if (canvas) {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const lowPower =
    window.matchMedia("(max-width: 760px)").matches ||
    navigator.connection?.saveData ||
    navigator.deviceMemory <= 4 ||
    navigator.hardwareConcurrency <= 4;

  const pixelRatio = Math.min(window.devicePixelRatio || 1, lowPower ? 1.15 : 1.7);
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x06101c, 8, 20);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 40);
  camera.position.set(4.9, 4.15, 6.4);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: !lowPower,
    alpha: true,
    powerPreference: "high-performance",
    stencil: false,
    depth: true,
  });
  renderer.setPixelRatio(pixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x050b16, 1);

  const root = new THREE.Group();
  root.position.set(0, -0.72, 0);
  root.rotation.y = -0.38;
  scene.add(root);

  const pointer = { x: 0, y: 0 };
  const clock = new THREE.Clock();
  let running = true;
  let frameId = 0;

  scene.add(new THREE.AmbientLight(0x88b8ff, 0.48));

  const keyLight = new THREE.DirectionalLight(0xc4f6ff, 1.35);
  keyLight.position.set(4, 7, 5);
  scene.add(keyLight);

  const cyanLight = new THREE.PointLight(0x62e6ff, 2.2, 8);
  cyanLight.position.set(1.8, 1.7, 2.4);
  scene.add(cyanLight);

  const amberLight = new THREE.PointLight(0xffb057, 1.5, 6);
  amberLight.position.set(-2.4, 0.8, 1.8);
  scene.add(amberLight);

  const baseMaterial = new THREE.MeshStandardMaterial({
    color: 0x061529,
    emissive: 0x03101c,
    roughness: 0.64,
    metalness: 0.38,
  });
  const base = new THREE.Mesh(new THREE.BoxGeometry(8.8, 0.08, 6.2), baseMaterial);
  base.position.y = -0.08;
  root.add(base);

  const grid = new THREE.GridHelper(8.8, 22, 0x1fe3ff, 0x20445a);
  grid.position.y = -0.03;
  grid.scale.z = 0.7;
  grid.material.transparent = true;
  grid.material.opacity = lowPower ? 0.24 : 0.34;
  root.add(grid);

  const buildingSpecs = createBuildingSpecs(lowPower ? 50 : 86);
  const buildingGeometry = new THREE.BoxGeometry(1, 1, 1);
  const buildingMaterial = new THREE.MeshStandardMaterial({
    color: 0x173149,
    emissive: 0x051424,
    roughness: 0.5,
    metalness: 0.42,
    vertexColors: true,
  });
  const buildings = new THREE.InstancedMesh(buildingGeometry, buildingMaterial, buildingSpecs.length);
  buildings.instanceMatrix.setUsage(THREE.StaticDrawUsage);
  const matrix = new THREE.Matrix4();
  buildingSpecs.forEach((spec, index) => {
    matrix.compose(
      new THREE.Vector3(spec.x, spec.h / 2, spec.z),
      new THREE.Quaternion(),
      new THREE.Vector3(spec.w, spec.h, spec.d)
    );
    buildings.setMatrixAt(index, matrix);
    buildings.setColorAt(index, new THREE.Color(spec.color));
  });
  buildings.instanceMatrix.needsUpdate = true;
  buildings.instanceColor.needsUpdate = true;
  root.add(buildings);

  const edgeMaterial = new THREE.LineBasicMaterial({
    color: 0x62e6ff,
    transparent: true,
    opacity: lowPower ? 0.12 : 0.18,
  });
  buildingSpecs.slice(0, lowPower ? 28 : 54).forEach((spec) => {
    const edges = new THREE.EdgesGeometry(buildingGeometry);
    const line = new THREE.LineSegments(edges, edgeMaterial);
    line.position.set(spec.x, spec.h / 2, spec.z);
    line.scale.set(spec.w, spec.h, spec.d);
    root.add(line);
  });

  const nodeData = [
    { p: new THREE.Vector3(-2.9, 0.12, -1.9), c: 0x62e6ff, s: 0.15 },
    { p: new THREE.Vector3(2.65, 0.12, -1.52), c: 0x9a7cff, s: 0.14 },
    { p: new THREE.Vector3(-1.28, 0.12, 1.78), c: 0xffb057, s: 0.18 },
    { p: new THREE.Vector3(2.2, 0.12, 1.56), c: 0x62e6ff, s: 0.12 },
    { p: new THREE.Vector3(0.32, 0.12, 0.12), c: 0xffffff, s: 0.12 },
  ];

  const nodeMeshes = [];
  const ringMeshes = [];
  const nodeGeometry = new THREE.SphereGeometry(1, lowPower ? 12 : 18, lowPower ? 8 : 12);
  const ringGeometry = new THREE.TorusGeometry(1, 0.01, 6, 64);
  nodeData.forEach((node, index) => {
    const material = new THREE.MeshBasicMaterial({ color: node.c });
    const mesh = new THREE.Mesh(nodeGeometry, material);
    mesh.position.copy(node.p);
    mesh.scale.setScalar(node.s);
    root.add(mesh);
    nodeMeshes.push(mesh);

    if (!lowPower || index < 3) {
      const ring = new THREE.Mesh(
        ringGeometry,
        new THREE.MeshBasicMaterial({
          color: node.c,
          transparent: true,
          opacity: 0.26,
          blending: THREE.AdditiveBlending,
        })
      );
      ring.position.copy(node.p);
      ring.rotation.x = Math.PI / 2;
      ring.scale.setScalar(index === 4 ? 0.52 : 0.72);
      root.add(ring);
      ringMeshes.push(ring);
    }
  });

  const pathMaterial = new THREE.LineBasicMaterial({
    color: 0x62e6ff,
    transparent: true,
    opacity: 0.52,
    blending: THREE.AdditiveBlending,
  });
  const alertPathMaterial = new THREE.LineBasicMaterial({
    color: 0xffb057,
    transparent: true,
    opacity: 0.58,
    blending: THREE.AdditiveBlending,
  });
  const paths = [
    [nodeData[0].p, new THREE.Vector3(-1.4, 0.2, -0.78), nodeData[4].p, new THREE.Vector3(1.26, 0.2, 0.62), nodeData[3].p],
    [nodeData[1].p, new THREE.Vector3(1.25, 0.22, -0.7), nodeData[4].p, new THREE.Vector3(-0.82, 0.24, 0.96), nodeData[2].p],
    [nodeData[2].p, new THREE.Vector3(-2.6, 0.16, 0.42), nodeData[0].p],
  ];
  paths.forEach((points, index) => {
    const curve = new THREE.CatmullRomCurve3(points);
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getPoints(lowPower ? 42 : 76)),
      index === 1 ? alertPathMaterial : pathMaterial
    );
    root.add(line);
  });

  const pulseGeometry = new THREE.SphereGeometry(0.05, 12, 8);
  const pulseMaterial = new THREE.MeshBasicMaterial({
    color: 0x62e6ff,
    transparent: true,
    opacity: 0.82,
    blending: THREE.AdditiveBlending,
  });
  const pulses = reduceMotion ? [] : paths.slice(0, lowPower ? 2 : 3).map((points, index) => {
    const curve = new THREE.CatmullRomCurve3(points);
    const mesh = new THREE.Mesh(pulseGeometry, pulseMaterial.clone());
    mesh.material.color.set(index === 1 ? 0xffb057 : 0x62e6ff);
    root.add(mesh);
    return { curve, mesh, offset: index * 0.28 };
  });

  const barCount = lowPower ? 18 : 32;
  const barGeometry = new THREE.BoxGeometry(0.075, 1, 0.075);
  const barMaterial = new THREE.MeshBasicMaterial({
    color: 0x62e6ff,
    transparent: true,
    opacity: 0.48,
    blending: THREE.AdditiveBlending,
  });
  const bars = new THREE.InstancedMesh(barGeometry, barMaterial, barCount);
  bars.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const barSpecs = Array.from({ length: barCount }, (_, index) => {
    const angle = index * 2.399;
    const radius = 0.45 + (index % 7) * 0.22;
    return {
      x: Math.cos(angle) * radius + (index % 3 - 1) * 0.9,
      z: Math.sin(angle) * radius + (index % 4 - 1.5) * 0.7,
      h: 0.18 + (index % 5) * 0.08,
      phase: index * 0.42,
    };
  });
  root.add(bars);

  const particleCount = lowPower ? 90 : 180;
  const particleGeometry = new THREE.BufferGeometry();
  const particlePositions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i += 1) {
    const seed = seeded(i + 11);
    particlePositions[i * 3] = (seed.x - 0.5) * 9.8;
    particlePositions[i * 3 + 1] = 0.18 + seed.y * 2.7;
    particlePositions[i * 3 + 2] = (seed.z - 0.5) * 7.2;
  }
  particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
  const particles = new THREE.Points(
    particleGeometry,
    new THREE.PointsMaterial({
      color: 0x8ff4ff,
      size: lowPower ? 0.026 : 0.036,
      transparent: true,
      opacity: lowPower ? 0.35 : 0.5,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  root.add(particles);

  const halo = new THREE.Mesh(
    new THREE.RingGeometry(2.7, 2.74, 128),
    new THREE.MeshBasicMaterial({
      color: 0x62e6ff,
      transparent: true,
      opacity: 0.2,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    })
  );
  halo.position.y = 0.02;
  halo.rotation.x = Math.PI / 2;
  root.add(halo);

  updateBars(0);
  resize();

  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(canvas.parentElement || canvas);
  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("pointermove", handlePointerMove, { passive: true });
  document.addEventListener("visibilitychange", handleVisibility);
  window.addEventListener("pagehide", destroy, { once: true });

  render();

  function createBuildingSpecs(count) {
    const specs = [];
    let index = 0;
    for (let x = -3.8; x <= 3.8 && specs.length < count; x += 0.55) {
      for (let z = -2.55; z <= 2.55 && specs.length < count; z += 0.48) {
        const skipCore = Math.abs(x) < 0.62 && Math.abs(z) < 0.55;
        const skipRoad = Math.abs((x + z) % 1.4) < 0.14;
        if (skipCore || skipRoad || (index % 7 === 0 && Math.abs(z) > 1.4)) {
          index += 1;
          continue;
        }
        const h = 0.18 + ((index * 17) % 11) * 0.075 + (Math.abs(x) < 1.3 ? 0.28 : 0);
        specs.push({
          x,
          z,
          h,
          w: 0.18 + ((index * 5) % 4) * 0.045,
          d: 0.18 + ((index * 3) % 4) * 0.04,
          color: index % 9 === 0 ? 0x226077 : index % 13 === 0 ? 0x594a70 : 0x173149,
        });
        index += 1;
      }
    }
    return specs;
  }

  function seeded(seed) {
    const x = Math.sin(seed * 12.9898) * 43758.5453;
    const y = Math.sin(seed * 78.233) * 12415.873;
    const z = Math.sin(seed * 4.1414) * 9135.157;
    return { x: x - Math.floor(x), y: y - Math.floor(y), z: z - Math.floor(z) };
  }

  function handlePointerMove(event) {
    if (reduceMotion) return;
    pointer.x = (event.clientX / window.innerWidth - 0.5) * 2;
    pointer.y = (event.clientY / window.innerHeight - 0.5) * 2;
  }

  function handleVisibility() {
    running = !document.hidden;
    if (running) render();
  }

  function updateBars(time) {
    const temp = new THREE.Matrix4();
    barSpecs.forEach((bar, index) => {
      const wave = reduceMotion ? 0.5 : Math.sin(time * 1.7 + bar.phase) * 0.5 + 0.5;
      const height = bar.h + wave * 0.55;
      temp.compose(
        new THREE.Vector3(bar.x, height / 2 + 0.08, bar.z),
        new THREE.Quaternion(),
        new THREE.Vector3(1, height, 1)
      );
      bars.setMatrixAt(index, temp);
    });
    bars.instanceMatrix.needsUpdate = true;
  }

  function resize() {
    const parent = canvas.parentElement || canvas;
    const width = Math.max(1, parent.clientWidth || canvas.clientWidth);
    const height = Math.max(1, parent.clientHeight || canvas.clientHeight);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(pixelRatio);
    renderer.setSize(width, height, false);
  }

  function render() {
    if (!running) return;
    const time = clock.getElapsedTime();
    const drift = reduceMotion ? 0 : Math.sin(time * 0.32) * 0.035;

    root.rotation.y += ((-0.38 + pointer.x * 0.1 + drift) - root.rotation.y) * 0.035;
    root.rotation.x += ((pointer.y * 0.035) - root.rotation.x) * 0.035;
    particles.rotation.y = time * 0.025;
    halo.rotation.z = time * 0.05;

    ringMeshes.forEach((ring, index) => {
      const scale = 0.7 + index * 0.07 + (reduceMotion ? 0 : Math.sin(time * 1.2 + index) * 0.035);
      ring.scale.setScalar(scale);
      ring.material.opacity = 0.16 + (reduceMotion ? 0 : Math.sin(time * 1.4 + index) * 0.04);
    });

    nodeMeshes.forEach((node, index) => {
      const scale = nodeData[index].s * (1 + (reduceMotion ? 0 : Math.sin(time * 2 + index) * 0.18));
      node.scale.setScalar(scale);
    });

    pulses.forEach((pulse) => {
      const t = (time * 0.14 + pulse.offset) % 1;
      pulse.mesh.position.copy(pulse.curve.getPointAt(t));
      pulse.mesh.position.y += 0.07;
    });

    updateBars(time);
    renderer.render(scene, camera);

    if (!reduceMotion) {
      frameId = window.requestAnimationFrame(render);
    }
  }

  function destroy() {
    running = false;
    window.cancelAnimationFrame(frameId);
    resizeObserver.disconnect();
    window.removeEventListener("resize", resize);
    window.removeEventListener("pointermove", handlePointerMove);
    document.removeEventListener("visibilitychange", handleVisibility);

    scene.traverse((object) => {
      if (object.geometry) object.geometry.dispose();
      if (object.material) {
        if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose());
        else object.material.dispose();
      }
    });
    renderer.dispose();
  }
}
