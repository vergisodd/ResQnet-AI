import { OrbitControls } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { lazy, Suspense, useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import {
  AdditiveBlending,
  BackSide,
  BufferAttribute,
  BufferGeometry,
  CatmullRomCurve3,
  Color,
  DoubleSide,
  Group,
  Line as ThreeLine,
  LineBasicMaterial,
  Material,
  Mesh,
  Points,
  PointsMaterial,
  ShaderMaterial,
  SphereGeometry,
  Vector3
} from 'three';
import { globalConnections, globalNodes, toneColors, type GeoPoint, type GlobalConnection } from '../../data/globalNetworkData';
import type { RenderQuality } from '../../hooks/useRenderProfile';
import { sceneTransition, smoothstep } from '../../motion/sceneTransitionState';

type BaseEarthSceneProps = {
  lowPower: boolean;
  reducedMotion: boolean;
};

type EarthSceneProps = BaseEarthSceneProps & {
  quality: RenderQuality;
  postprocessing: boolean;
};

const GlobalSceneEffects = lazy(() =>
  import('./GlobalSceneEffects').then((module) => ({
    default: module.GlobalSceneEffects
  }))
);

const EARTH_RADIUS = 1.72;

export function GlobalEarthScene({ lowPower, reducedMotion, postprocessing }: EarthSceneProps) {
  const earth = useRef<Group>(null);
  const atmosphere = useRef<Mesh>(null);
  const cameraTarget = useMemo(() => new Vector3(), []);

  useFrame(({ clock, pointer, camera }, delta) => {
    if (!earth.current) return;
    const t = clock.elapsedTime;
    const transition = smoothstep(0.42, 1, sceneTransition.progress);
    const rotationSpeed = (reducedMotion ? 0.012 : 0.045) * (0.72 + transition * 0.62);
    earth.current.rotation.y += delta * rotationSpeed;
    earth.current.rotation.x += (0.26 + pointer.y * 0.07 - transition * 0.08 - earth.current.rotation.x) * Math.min(1, delta * 1.7);
    earth.current.position.y = (reducedMotion ? 0 : Math.sin(t * 0.3) * 0.035) - (1 - transition) * 0.16;
    earth.current.scale.setScalar(0.86 + transition * 0.14);
    cameraTarget.set(pointer.x * 0.08, 0.35 - transition * 0.08, 6.45 - transition * 0.58);
    camera.position.lerp(cameraTarget, Math.min(1, delta * 2.2));
    camera.lookAt(0, 0, 0);

    if (atmosphere.current && !reducedMotion) {
      const pulse = 1 + Math.sin(t * 0.72) * 0.012;
      atmosphere.current.scale.setScalar(pulse);
    }
  });

  return (
    <>
      <ambientLight intensity={0.3} color="#8abaff" />
      <directionalLight position={[3.6, 2.4, 4.2]} intensity={2.4} color="#ffffff" />
      <pointLight position={[-3.4, 1.8, 3]} intensity={5.2} color="#62e6ff" distance={10} />
      <pointLight position={[3.2, -1.4, 2.8]} intensity={2.2} color="#ffb057" distance={9} />

      <StarField lowPower={lowPower} reducedMotion={reducedMotion} />
      <group ref={earth} rotation={[0.26, -0.72, -0.08]}>
        <EarthBody lowPower={lowPower} />
        <Atmosphere atmosphereRef={atmosphere} lowPower={lowPower} />
        <ContinentGlow lowPower={lowPower} />
        <GlobalConnections lowPower={lowPower} reducedMotion={reducedMotion} />
        <GlowingCityNodes reducedMotion={reducedMotion} lowPower={lowPower} />
        <OrbitalNetwork reducedMotion={reducedMotion} lowPower={lowPower} />
      </group>

      <OrbitControls
        enablePan={false}
        enableZoom={false}
        enableRotate={!reducedMotion}
        autoRotate={!reducedMotion}
        autoRotateSpeed={0.12}
        minPolarAngle={Math.PI / 3.2}
        maxPolarAngle={Math.PI / 1.55}
      />

      {postprocessing && (
        <Suspense fallback={null}>
          <GlobalSceneEffects />
        </Suspense>
      )}
    </>
  );
}

function EarthBody({ lowPower }: { lowPower: boolean }) {
  const material = useMemo(
    () =>
      new ShaderMaterial({
        uniforms: {
          deepColor: { value: new Color('#081529') },
          coastColor: { value: new Color('#1b5f78') },
          rimColor: { value: new Color('#62e6ff') }
        },
        vertexShader: `
          precision mediump float;
          varying vec3 vNormal;
          varying vec3 vWorldPosition;

          void main() {
            vNormal = normalize(normalMatrix * normal);
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          precision mediump float;
          uniform vec3 deepColor;
          uniform vec3 coastColor;
          uniform vec3 rimColor;
          varying vec3 vNormal;
          varying vec3 vWorldPosition;

          float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
          }

          void main() {
            vec3 normal = normalize(vNormal);
            float rim = pow(1.0 - max(dot(normal, vec3(0.0, 0.0, 1.0)), 0.0), 2.2);
            float bands = sin(vWorldPosition.y * 7.0 + sin(vWorldPosition.x * 5.0) * 1.2);
            float noise = hash(vWorldPosition.xz * 2.4 + bands);
            float land = smoothstep(0.48, 0.72, noise + bands * 0.12);
            vec3 color = mix(deepColor, coastColor, land * 0.62);
            color += rimColor * rim * 0.32;
            gl_FragColor = vec4(color, 1.0);
          }
        `
      }),
    []
  );

  return (
    <mesh>
      <sphereGeometry args={[EARTH_RADIUS, lowPower ? 48 : 96, lowPower ? 32 : 64]} />
      <primitive object={material} attach="material" />
    </mesh>
  );
}

function Atmosphere({ atmosphereRef, lowPower }: { atmosphereRef: RefObject<Mesh | null>; lowPower: boolean }) {
  return (
    <mesh ref={atmosphereRef} scale={1.055}>
      <sphereGeometry args={[EARTH_RADIUS, lowPower ? 48 : 96, lowPower ? 32 : 64]} />
      <meshBasicMaterial
        color="#62e6ff"
        transparent
        opacity={0.16}
        side={BackSide}
        blending={AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}

function ContinentGlow({ lowPower }: { lowPower: boolean }) {
  const points = useMemo(() => {
    const random = createSeededRandom(lowPower ? 3709 : 9143);
    const count = lowPower ? 72 : 164;
    const values = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      const lat = -54 + random() * 116;
      const lon = -170 + random() * 340;
      const position = geoToVector(lat, lon, EARTH_RADIUS + 0.018);
      values[i * 3] = position.x;
      values[i * 3 + 1] = position.y;
      values[i * 3 + 2] = position.z;
    }
    return values;
  }, [lowPower]);
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    geo.setAttribute('position', new BufferAttribute(points, 3));
    return geo;
  }, [points]);
  const material = useMemo(
    () =>
      new PointsMaterial({
        color: '#9fcfff',
        size: lowPower ? 0.012 : 0.016,
        transparent: true,
        opacity: 0.44,
        blending: AdditiveBlending,
        depthWrite: false
      }),
    [lowPower]
  );

  return <points geometry={geometry} material={material} />;
}

function GlobalConnections({ lowPower, reducedMotion }: BaseEarthSceneProps) {
  const nodeMap = useMemo(() => Object.fromEntries(globalNodes.map((node) => [node.id, node])), []);
  const selectedConnections = lowPower ? globalConnections.slice(0, 8) : globalConnections;

  return (
    <group>
      {selectedConnections.map((connection, index) => {
        const from = nodeMap[connection.from];
        const to = nodeMap[connection.to];
        if (!from || !to) return null;
        return (
          <ConnectionArc
            key={connection.id}
            connection={connection}
            from={from}
            to={to}
            index={index}
            reducedMotion={reducedMotion}
            lowPower={lowPower}
          />
        );
      })}
    </group>
  );
}

function ConnectionArc({
  connection,
  from,
  to,
  index,
  reducedMotion,
  lowPower
}: {
  connection: GlobalConnection;
  from: GeoPoint;
  to: GeoPoint;
  index: number;
  reducedMotion: boolean;
  lowPower: boolean;
}) {
  const pulse = useRef<Mesh>(null);
  const color = toneColors[connection.tone];
  const curve = useMemo(() => createArcCurve(from, to), [from, to]);
  const points = useMemo(() => curve.getPoints(lowPower ? 30 : 46), [curve, lowPower]);

  useFrame(({ clock }) => {
    if (!pulse.current || reducedMotion) return;
    const t = (clock.elapsedTime * 0.11 + index * 0.083) % 1;
    pulse.current.position.copy(curve.getPointAt(t));
    pulse.current.scale.setScalar(0.82 + Math.sin(clock.elapsedTime * 3.2 + index) * 0.08);
  });

  return (
    <group>
      <Polyline points={points} color={color} opacity={0.52} />
      {!lowPower && (
        <mesh ref={pulse}>
          <sphereGeometry args={[0.028, 10, 10]} />
          <meshBasicMaterial color={color} transparent opacity={0.92} blending={AdditiveBlending} />
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

function GlowingCityNodes({ reducedMotion, lowPower }: BaseEarthSceneProps) {
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => () => {
    document.body.style.cursor = '';
  }, []);

  return (
    <group>
      {globalNodes.map((node) => (
        <EarthNode
          key={node.id}
          node={node}
          active={active === node.id}
          reducedMotion={reducedMotion}
          lowPower={lowPower}
          onActive={setActive}
        />
      ))}
    </group>
  );
}

function EarthNode({
  node,
  active,
  reducedMotion,
  lowPower,
  onActive
}: {
  node: GeoPoint;
  active: boolean;
  reducedMotion: boolean;
  lowPower: boolean;
  onActive: (id: string | null) => void;
}) {
  const mesh = useRef<Mesh>(null);
  const position = useMemo(() => geoToVector(node.lat, node.lon, EARTH_RADIUS + 0.05), [node.lat, node.lon]);
  const color = toneColors[node.tone];

  useFrame(({ clock }) => {
    if (!mesh.current || reducedMotion) return;
    const pulse = active ? 1.38 : 1 + Math.sin(clock.elapsedTime * 2.0 + position.x) * 0.08;
    mesh.current.scale.setScalar(pulse);
  });

  return (
    <group position={position}>
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
        <sphereGeometry args={[0.045, lowPower ? 8 : 14, lowPower ? 8 : 14]} />
        <meshBasicMaterial color={color} transparent opacity={1} toneMapped={false} />
      </mesh>
      <mesh>
        <ringGeometry args={[0.07, active ? 0.13 : 0.1, lowPower ? 14 : 24]} />
        <meshBasicMaterial color={color} transparent opacity={active ? 0.36 : 0.2} side={DoubleSide} blending={AdditiveBlending} />
      </mesh>
    </group>
  );
}

function OrbitalNetwork({ reducedMotion, lowPower }: BaseEarthSceneProps) {
  const group = useRef<Group>(null);
  const ringCount = lowPower ? 2 : 3;

  useFrame(({ clock }) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.y = clock.elapsedTime * 0.035;
    group.current.rotation.z = Math.sin(clock.elapsedTime * 0.22) * 0.04;
  });

  return (
    <group ref={group}>
      {Array.from({ length: ringCount }).map((_, index) => (
        <mesh key={index} rotation={[Math.PI / 2.1 + index * 0.32, index * 0.52, index * 0.68]}>
          <torusGeometry args={[EARTH_RADIUS + 0.34 + index * 0.12, 0.0026, 6, lowPower ? 96 : 160]} />
          <meshBasicMaterial
            color={index === 1 ? '#9a7cff' : '#62e6ff'}
            transparent
            opacity={index === 1 ? 0.2 : 0.26}
            blending={AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
}

function StarField({ lowPower, reducedMotion }: BaseEarthSceneProps) {
  const stars = useRef<Points>(null);
  const count = lowPower ? 220 : 560;
  const positions = useMemo(() => {
    const random = createSeededRandom(lowPower ? 1901 : 7109);
    const values = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      const radius = 9 + random() * 12;
      const theta = random() * Math.PI * 2;
      const phi = Math.acos(2 * random() - 1);
      values[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      values[i * 3 + 1] = radius * Math.cos(phi);
      values[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    }
    return values;
  }, [count]);
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    geo.setAttribute('position', new BufferAttribute(positions, 3));
    return geo;
  }, [positions]);
  const material = useMemo(
    () =>
      new PointsMaterial({
        color: '#d9f7ff',
        size: lowPower ? 0.01 : 0.014,
        transparent: true,
        opacity: lowPower ? 0.32 : 0.44,
        blending: AdditiveBlending,
        depthWrite: false
      }),
    [lowPower]
  );

  useFrame(({ clock }) => {
    if (!stars.current || reducedMotion) return;
    stars.current.rotation.y = clock.elapsedTime * 0.006;
    stars.current.rotation.x = Math.sin(clock.elapsedTime * 0.08) * 0.012;
  });

  return <points ref={stars} geometry={geometry} material={material} />;
}

function geoToVector(lat: number, lon: number, radius: number) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);

  return new Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

function createArcCurve(from: GeoPoint, to: GeoPoint) {
  const start = geoToVector(from.lat, from.lon, EARTH_RADIUS + 0.06);
  const end = geoToVector(to.lat, to.lon, EARTH_RADIUS + 0.06);
  const mid = start.clone().add(end).normalize();
  const distance = start.distanceTo(end);
  const altitude = 0.32 + Math.min(0.68, distance * 0.22);
  const controlA = start.clone().lerp(mid.clone().multiplyScalar(EARTH_RADIUS + altitude), 0.42);
  const controlB = end.clone().lerp(mid.clone().multiplyScalar(EARTH_RADIUS + altitude), 0.42);

  return new CatmullRomCurve3([start, controlA, controlB, end]);
}

function createSeededRandom(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
