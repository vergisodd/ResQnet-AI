# ResQNet Dashboard Frontend Foundation

This is a React + TypeScript + TailwindCSS + GSAP / React Three Fiber scaffold for the next ResQNet AI dashboard UI layer.

It is intentionally frontend-only:

- No backend routes are changed.
- No database logic is changed.
- No FastAPI server architecture is changed.
- The live `/dashboard/` route is still served from `static/dashboard/`.

## Structure

```text
src/
  App.tsx
  components/
    dashboard/
      InfrastructureWidget.tsx
      SkeletonPanel.tsx
    ui/
      GlassPanel.tsx
      MetricCard.tsx
      StatusPill.tsx
  data/
    dashboard.ts
  types/
    dashboard.ts
  utils/
    tone.ts
```

## Intent

This foundation defines reusable UI pieces for:

- dark cinematic dashboard layouts
- glassmorphism cards
- metric cards
- AI infrastructure widgets
- status indicators
- skeleton loading states
- accessible CSS/GSAP microinteractions

## Toronto 3D Scene

The Toronto smart-city scene lives in:

```text
src/components/three/
  TorontoSmartCityCanvas.tsx
  TorontoSmartCityScene.tsx
src/data/
  torontoSceneData.ts
```

It uses React Three Fiber for the scene graph, Drei for adaptive performance helpers, and `@react-three/postprocessing` for controlled bloom/vignette polish.

Performance choices:

- instanced city buildings
- instanced floating data bars
- lightweight line geometry for network paths
- point cloud particles without textures
- adaptive DPR and event handling
- reduced-motion and mobile quality fallback
- hardware, reduced-data, and save-data render profiling
- native Three line primitives for lighter network paths
- postprocessing disabled on low-power paths

Earth visualization and GSAP timelines are included in the cinematic production shell.

## Global Earth Visualization

The global infrastructure Earth scene lives in:

```text
src/components/three/
  GlobalEarthCanvas.tsx
  GlobalEarthScene.tsx
src/data/
  globalNetworkData.ts
```

It uses procedural globe shading rather than external image textures. That keeps the scene reliable in offline/demo environments and avoids large texture memory costs.

Scene elements:

- rotating procedural Earth sphere
- additive atmosphere shell
- global city nodes
- arced network connections
- animated data pulses along arcs
- orbital network rings
- subtle star field
- controlled bloom, depth of field, and vignette on high-quality paths

Performance choices:

- no remote texture/model loading
- memoized geometries, materials, and path curves
- single point cloud for stars
- compact point cloud for surface activity
- adaptive DPR and adaptive pointer events
- postprocessing disabled on mobile/reduced-motion/low-power paths
- postprocessing effects lazy-loaded as high-quality-only chunks
- lazy-loaded `GlobalEarthCanvas` chunk separate from the main UI shell
- viewport-deferred Earth canvas mounting to protect first-load Core Web Vitals

## Cinematic Scroll Transition

The scroll-driven transition system lives in:

```text
src/motion/
  CinematicScrollController.tsx
  sceneTransitionState.ts
```

GSAP ScrollTrigger controls DOM choreography between the Toronto scene and the Earth scene. R3F scenes read `sceneTransition.progress` inside `useFrame`, which avoids React rerenders during scroll while still allowing camera and scene interpolation.

Motion choices:

- transforms and opacity only for DOM animation
- `scrub` timeline for smooth mouse-wheel progress
- scoped GSAP selectors with automatic cleanup
- GSAP React lifecycle cleanup and media-query-aware timelines
- reduced-motion fallback disables choreography
- shared progress drives Toronto zoom-out and Earth zoom-in
- no API/backend coupling

## Production Optimization Notes

- The initial application shell avoids Three, GSAP, and postprocessing modulepreload hints so cinematic code loads only when React renders the relevant lazy boundary.
- Framer Motion was removed from the runtime bundle; UI reveal and progress motion now use compositor-friendly CSS transforms with reduced-motion support.
- WebGL quality progressively degrades from high to balanced to low by disabling postprocessing first, then reducing DPR, shadows, geometry segments, and particle counts.
