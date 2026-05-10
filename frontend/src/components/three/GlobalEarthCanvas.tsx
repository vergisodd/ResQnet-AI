import { AdaptiveDpr, AdaptiveEvents, PerformanceMonitor } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Suspense, useState } from 'react';
import { useRenderProfile, type RenderQuality } from '../../hooks/useRenderProfile';
import { GlobalEarthScene } from './GlobalEarthScene';

export function GlobalEarthCanvas() {
  const [adaptiveQuality, setAdaptiveQuality] = useState<RenderQuality>('high');
  const renderProfile = useRenderProfile(adaptiveQuality);

  return (
    <div
      className="scene-frame scene-frame--earth relative overflow-hidden rounded-ui border border-cyan/15 bg-[#030711]"
      aria-label="Rotating Earth with global AI infrastructure connections"
      role="img"
    >
      <Canvas
        camera={{ position: [0, 0.35, 6.1], fov: 42, near: 0.1, far: 90 }}
        dpr={renderProfile.dpr}
        gl={{
          antialias: renderProfile.antialias,
          alpha: false,
          depth: true,
          stencil: false,
          preserveDrawingBuffer: false,
          powerPreference: 'high-performance'
        }}
      >
        <color attach="background" args={['#030711']} />
        <fog attach="fog" args={['#030711', 9, 24]} />
        <Suspense fallback={null}>
          <GlobalEarthScene
            lowPower={renderProfile.lowPower}
            reducedMotion={renderProfile.prefersReducedMotion}
            quality={renderProfile.quality}
            postprocessing={renderProfile.postprocessing}
          />
        </Suspense>
        <AdaptiveDpr pixelated />
        <AdaptiveEvents />
        <PerformanceMonitor
          flipflops={2}
          onDecline={() =>
            setAdaptiveQuality((current) => (current === 'high' ? 'balanced' : 'low'))
          }
          onIncline={() => {
            if (!renderProfile.isMobile && !renderProfile.prefersReducedMotion) {
              setAdaptiveQuality('high');
            }
          }}
        />
      </Canvas>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,transparent,rgba(3,7,17,.16)_46%,rgba(3,7,17,.82)_100%)]" />
      <div className="pointer-events-none absolute left-4 top-4 rounded-ui border border-cyan/20 bg-ink/70 px-3 py-2 text-xs font-black uppercase text-cyan backdrop-blur-xl">
        Global infrastructure mesh
      </div>
    </div>
  );
}
