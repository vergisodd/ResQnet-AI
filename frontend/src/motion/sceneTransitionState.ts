export type SceneTransitionState = {
  progress: number;
  velocity: number;
};

export const sceneTransition: SceneTransitionState = {
  progress: 0,
  velocity: 0
};

export function setSceneTransitionProgress(value: number) {
  const progress = clamp01(value);
  sceneTransition.velocity = progress - sceneTransition.progress;
  sceneTransition.progress = progress;
}

export function smoothstep(edge0: number, edge1: number, value: number) {
  const x = clamp01((value - edge0) / (edge1 - edge0));
  return x * x * (3 - 2 * x);
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value));
}
