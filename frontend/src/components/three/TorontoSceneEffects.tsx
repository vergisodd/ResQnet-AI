import { Bloom, EffectComposer, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';

export function TorontoSceneEffects() {
  return (
    <EffectComposer multisampling={0}>
      <Bloom
        intensity={0.72}
        luminanceThreshold={0.42}
        luminanceSmoothing={0.55}
        mipmapBlur
        radius={0.48}
        blendFunction={BlendFunction.ADD}
      />
      <Vignette offset={0.32} darkness={0.46} />
    </EffectComposer>
  );
}
