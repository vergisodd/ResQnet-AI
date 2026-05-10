import { OrbitControls } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  CatmullRomCurve3,
  Color,
  DoubleSide,
  DynamicDrawUsage,
  Group,
  InstancedMesh,
  Line as ThreeLine,
  LineBasicMaterial,
  Material,
  Mesh,
  Object3D,
  Points,
  PointsMaterial,
  Vector3
} from 'three';
import {
  cityNodes,
  createBuildingSpecs,
  createDataBarSpecs,
  networkPaths,
  type CityNode,
  type Vec3
} from '../../data/torontoSceneData';
import type { RenderQuality } from '../../hooks/useRenderProfile';
import { sceneTransition, smoothstep } from '../../motion/sceneTransitionState';

type BaseSceneProps = {
  lowPower: boolean;
  reducedMotion: boolean;
};

type SceneProps = BaseSceneProps & {
  quality: RenderQuality;
  postprocessing: boolean;
};

const TorontoSceneEffects = lazy(() =>
  import('./TorontoSceneEffects').then((module) => ({
    default: module.TorontoSceneEffects
  }))
);

const nodeColors = {
  cyan: '#62e6ff',
  blue: '#3a8bff',
  violet: '#9a7cff',
  amber: '#ffb057'
};

export function TorontoSmartCityScene({ lowPower, reducedMotion, postprocessing }: SceneProps) {
  const root = useRef<Group>(null);
  const cameraTarget = useMemo(() => new Vector3(), []);

  useFrame(({ clock, pointer, camera }, delta) => {
    if (!root.current) return;
    const t = clock.elapsedTime;
    const transition = smoothstep(0.02, 0.72, sceneTransition.progress);
    const targetX = reducedMotion ? 0 : pointer.y * 0.08;
    const targetY = reducedMotion ? -0.38 : -0.38 + pointer.x * 0.1;
    root.current.rotation.x += (targetX - root.current.rotation.x) * Math.min(1, delta * 2.2);
    root.current.rotation.y += (targetY - transition * 0.16 - root.current.rotation.y) * Math.min(1, delta * 2.2);
    root.current.position.y = -0.72 + (reducedMotion ? 0 : Math.sin(t * 0.35) * 0.035) - transition * 0.26;
    root.current.scale.setScalar(1 - transition * 0.1);
    cameraTarget.set(
      4.6 + transition * 1.5 + (reducedMotion ? 0 : pointer.x * 0.12),
      4.1 + transition * 0.95,
      6.2 + transition * 2.35
    );
    camera.position.lerp(cameraTarget, Math.min(1, delta * 2.6));
    camera.lookAt(0, 0.4, 0);
  });

  return (
    <>
      <ambientLight intensity={0.55} color="#9fc9ff" />
      <directionalLight position={[4, 7, 4]} intensity={1.8} color="#ffffff" castShadow={!lowPower} />
      <pointLight position={[-3.5, 2.6, 2.8]} intensity={5.8} color="#62e6ff" distance={9} />
      <pointLight position={[3.3, 2.2, 1.6]} intensity={3.6} color="#ffb057" distance={8} />
      <pointLight position={[0, 3.5, -3]} intensity={2.8} color="#9a7cff" distance={8} />

      <group ref={root} rotation={[0, -0.38, 0]} position={[0, -0.72, 0]}>
        <BasePlate lowPower={lowPower} />
        <InstancedBuildings lowPower={lowPower} />
        <NetworkPaths reducedMotion={reducedMotion} lowPower={lowPower} />
        <FloatingDataBars reducedMotion={reducedMotion} lowPower={lowPower} />
        <CityNodes reducedMotion={reducedMotion} lowPower={lowPower} />
        <ParticleField reducedMotion={reducedMotion} lowPower={lowPower} />
      </group>

      <OrbitControls
        enablePan={false}
        enableZoom={false}
        enableRotate={!reducedMotion}
        autoRotate={!reducedMotion}
        autoRotateSpeed={0.18}
        minPolarAngle={Math.PI / 3.6}
        maxPolarAngle={Math.PI / 2.35}
      />
      {postprocessing && (
        <Suspense fallback={null}>
          <TorontoSceneEffects />
        </Suspense>
      )}
    </>
  );
}

function BasePlate({ lowPower }: { lowPower: boolean }) {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[8.8, 6.2, 1, 1]} />
        <meshStandardMaterial color="#07111f" metalness={0.42} roughness={0.68} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.012, 0]}>
        <ringGeometry args={[2.4, 3.85, lowPower ? 64 : 96]} />
        <meshBasicMaterial color="#62e6ff" transparent opacity={0.07} side={DoubleSide} />
      </mesh>
    </group>
  );
}

function InstancedBuildings({ lowPower }: { lowPower: boolean }) {
  const mesh = useRef<InstancedMesh>(null);
  const specs = useMemo(() => createBuildingSpecs(lowPower), [lowPower]);
  const dummy = useMemo(() => new Object3D(), []);
  const color = useMemo(() => new Color(), []);

  useEffect(() => {
    if (!mesh.current) return;
    specs.forEach((building, index) => {
      dummy.position.set(...building.position);
      dummy.scale.set(...building.scale);
      dummy.rotation.y = (index % 4) * 0.035;
      dummy.updateMatrix();
      mesh.current?.setMatrixAt(index, dummy.matrix);
      const hex = building.tone === 'cyan' ? '#153a4e' : building.tone === 'blue' ? '#102946' : '#121c2c';
      mesh.current?.setColorAt(index, color.set(hex));
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
  }, [color, dummy, specs]);

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, specs.length]} castShadow={!lowPower} receiveShadow frustumCulled>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color="#132136"
        emissive="#07111f"
        emissiveIntensity={0.45}
        metalness={0.62}
        roughness={0.38}
      />
    </instancedMesh>
  );
}

function NetworkPaths({ reducedMotion, lowPower }: BaseSceneProps) {
  return (
    <group>
      {networkPaths.map((path, index) => (
        <AnimatedPath
          key={path.id}
          color={path.color}
          points={path.points}
          phase={index * 0.6}
          reducedMotion={reducedMotion}
          lowPower={lowPower}
        />
      ))}
    </group>
  );
}

function AnimatedPath({
  points,
  color,
  phase,
  reducedMotion,
  lowPower
}: {
  points: Vec3[];
  color: string;
  phase: number;
  reducedMotion: boolean;
  lowPower: boolean;
}) {
  const pulse = useRef<Mesh>(null);
  const curve = useMemo(() => new CatmullRomCurve3(points.map((point) => new Vector3(...point))), [points]);
  const linePoints = useMemo(() => curve.getPoints(lowPower ? 26 : 42), [curve, lowPower]);
  useFrame(({ clock }) => {
    if (reducedMotion || !pulse.current) return;
    const t = (clock.elapsedTime * 0.16 + phase) % 1;
    const point = curve.getPointAt(t);
    pulse.current.position.copy(point);
    const scale = 0.8 + Math.sin(clock.elapsedTime * 3 + phase) * 0.12;
    pulse.current.scale.setScalar(scale);
  });

  return (
    <group>
      <Polyline points={linePoints} color={color} opacity={0.72} />
      {!lowPower && (
        <mesh ref={pulse}>
          <sphereGeometry args={[0.045, 10, 10]} />
          <meshBasicMaterial color={color} transparent opacity={0.92} />
        </mesh>
      )}
    </group>
  );
}

function Polyline({ points, color, opacity }: { points: Vector3[]; color: string; opacity: number }) {
  const line = useMemo(() => {
    const geometry = new BufferGeometry().setFromPoints(points);
    const material = new LineBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: AdditiveBlending,
      depthWrite: false
    });
    const object = new ThreeLine(geometry, material);
    object.frustumCulled = true;
    return object;
  }, [color, opacity, points]);

  useEffect(
    () => () => {
      line.geometry.dispose();
      (line.material as Material).dispose();
    },
    [line]
  );

  return <primitive object={line} />;
}

function FloatingDataBars({ reducedMotion, lowPower }: BaseSceneProps) {
  const mesh = useRef<InstancedMesh>(null);
  const frame = useRef(0);
  const specs = useMemo(() => createDataBarSpecs(), []);
  const dummy = useMemo(() => new Object3D(), []);
  const colorCache = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(nodeColors).map(([tone, color]) => [tone, new Color(color)])
      ) as Record<keyof typeof nodeColors, Color>,
    []
  );

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    if (lowPower) {
      frame.current = (frame.current + 1) % 2;
      if (frame.current !== 0) return;
    }
    const t = clock.elapsedTime;
    specs.forEach((bar, index) => {
      const pulse = reducedMotion ? 1 : 1 + Math.sin(t * 1.7 + index * 0.72) * 0.22;
      const h = bar.height * pulse;
      dummy.position.set(bar.position[0], h / 2 + 0.1, bar.position[2]);
      dummy.scale.set(0.075, h, 0.075);
      dummy.rotation.y = index * 0.24;
      dummy.updateMatrix();
      mesh.current?.setMatrixAt(index, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  useEffect(() => {
    if (!mesh.current) return;
    specs.forEach((bar, index) => {
      mesh.current?.setColorAt(index, colorCache[bar.tone] ?? colorCache.cyan);
    });
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
  }, [colorCache, specs]);

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, specs.length]} frustumCulled>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color="#62e6ff"
        emissive="#62e6ff"
        emissiveIntensity={lowPower ? 0.8 : 1.5}
        metalness={0.5}
        roughness={0.22}
        toneMapped={false}
      />
    </instancedMesh>
  );
}

function CityNodes({ reducedMotion, lowPower }: BaseSceneProps) {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  useEffect(() => () => {
    document.body.style.cursor = '';
  }, []);

  return (
    <group>
      {cityNodes.map((node) => (
        <InteractiveNode
          key={node.id}
          node={node}
          active={activeNode === node.id}
          reducedMotion={reducedMotion}
          lowPower={lowPower}
          onActive={setActiveNode}
        />
      ))}
    </group>
  );
}

function InteractiveNode({
  node,
  active,
  reducedMotion,
  lowPower,
  onActive
}: {
  node: CityNode;
  active: boolean;
  reducedMotion: boolean;
  lowPower: boolean;
  onActive: (id: string | null) => void;
}) {
  const mesh = useRef<Mesh>(null);
  const color = nodeColors[node.tone];

  useFrame(({ clock }) => {
    if (!mesh.current || reducedMotion) return;
    const pulse = active ? 1.3 : 1 + Math.sin(clock.elapsedTime * 2.2 + node.position[0]) * 0.06;
    mesh.current.scale.setScalar(pulse);
  });

  return (
    <group position={node.position}>
      <mesh
        ref={mesh}
        onPointerOver={(event) => {
          event.stopPropagation();
          onActive(node.id);
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          onActive(null);
          document.body.style.cursor = '';
        }}
      >
        <sphereGeometry args={[0.105, lowPower ? 10 : 18, lowPower ? 10 : 18]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={active ? 2.4 : 1.45} toneMapped={false} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.29, 0]}>
        <ringGeometry args={[0.16, active ? 0.34 : 0.26, lowPower ? 18 : 32]} />
        <meshBasicMaterial color={color} transparent opacity={active ? 0.45 : 0.22} side={DoubleSide} />
      </mesh>
      {active && (
        <group position={[0.14, 0.24, 0]}>
          <mesh>
            <planeGeometry args={[1.08, 0.32]} />
            <meshBasicMaterial color="#07111f" transparent opacity={0.88} />
          </mesh>
        </group>
      )}
    </group>
  );
}

function ParticleField({ reducedMotion, lowPower }: BaseSceneProps) {
  const points = useRef<Points>(null);
  const count = lowPower ? 112 : 260;
  const positions = useMemo(() => {
    const random = createSeededRandom(lowPower ? 2701 : 8101);
    const values = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      values[i * 3] = (random() - 0.5) * 8.2;
      values[i * 3 + 1] = random() * 2.9 + 0.18;
      values[i * 3 + 2] = (random() - 0.5) * 5.8;
    }
    return values;
  }, [count]);
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    const attr = new BufferAttribute(positions, 3);
    attr.setUsage(DynamicDrawUsage);
    geo.setAttribute('position', attr);
    return geo;
  }, [positions]);
  const material = useMemo(
    () =>
      new PointsMaterial({
        color: '#9fcfff',
        size: lowPower ? 0.018 : 0.026,
        transparent: true,
        opacity: lowPower ? 0.36 : 0.52,
        blending: AdditiveBlending,
        depthWrite: false
      }),
    [lowPower]
  );

  useFrame(({ clock }) => {
    if (!points.current || reducedMotion) return;
    const t = clock.elapsedTime;
    points.current.rotation.y = t * 0.018;
    points.current.rotation.x = Math.sin(t * 0.12) * 0.025;
  });

  return <points ref={points} geometry={geometry} material={material} frustumCulled />;
}

function createSeededRandom(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
