import { Bloom, DepthOfField, EffectComposer, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';

export function GlobalSceneEffects() {
  return (
    <EffectComposer multisampling={0}>
      <Bloom
        intensity={0.64}
        luminanceThreshold={0.36}
        luminanceSmoothing={0.58}
        mipmapBlur
        radius={0.42}
        blendFunction={BlendFunction.ADD}
      />
      <DepthOfField focusDistance={0.03} focalLength={0.025} bokehScale={0.75} height={420} />
      <Vignette offset={0.34} darkness={0.5} />
    </EffectComposer>
  );
}
