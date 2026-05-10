import { AdaptiveDpr, AdaptiveEvents, PerformanceMonitor } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Suspense, useState } from 'react';
import { useRenderProfile, type RenderQuality } from '../../hooks/useRenderProfile';
import { TorontoSmartCityScene } from './TorontoSmartCityScene';

export function TorontoSmartCityCanvas() {
  const [adaptiveQuality, setAdaptiveQuality] = useState<RenderQuality>('high');
  const renderProfile = useRenderProfile(adaptiveQuality);

  return (
    <div
      className="scene-frame scene-frame--toronto relative overflow-hidden rounded-ui border border-cyan/15 bg-[#050b16]"
      aria-label="Toronto-inspired smart city network visualization"
      role="img"
    >
      <Canvas
        camera={{ position: [4.6, 4.1, 6.2], fov: 42, near: 0.1, far: 80 }}
        dpr={renderProfile.dpr}
        gl={{
          antialias: renderProfile.antialias,
          alpha: false,
          depth: true,
          stencil: false,
          preserveDrawingBuffer: false,
          powerPreference: 'high-performance'
        }}
        shadows={renderProfile.shadows}
      >
        <color attach="background" args={['#050b16']} />
        <fog attach="fog" args={['#050b16', 8, 20]} />
        <Suspense fallback={null}>
          <TorontoSmartCityScene
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
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_38%,transparent,rgba(5,11,22,.18)_52%,rgba(5,11,22,.72)_100%)]" />
      <div className="pointer-events-none absolute left-4 top-4 rounded-ui border border-cyan/20 bg-ink/70 px-3 py-2 text-xs font-black uppercase text-cyan backdrop-blur-xl">
        Toronto network model
      </div>
    </div>
  );
}
