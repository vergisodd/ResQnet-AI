import { lazy, Suspense, useRef } from 'react';
import { DeferredScene } from './components/dashboard/DeferredScene';
import { InfrastructureWidget } from './components/dashboard/InfrastructureWidget';
import { SkeletonPanel } from './components/dashboard/SkeletonPanel';
import { GlassPanel } from './components/ui/GlassPanel';
import { MetricCard } from './components/ui/MetricCard';
import { infrastructureWidgets, metrics } from './data/dashboard';

const CinematicScrollController = lazy(() =>
  import('./motion/CinematicScrollController').then((module) => ({
    default: module.CinematicScrollController
  }))
);

const TorontoSmartCityCanvas = lazy(() =>
  import('./components/three/TorontoSmartCityCanvas').then((module) => ({
    default: module.TorontoSmartCityCanvas
  }))
);

const GlobalEarthCanvas = lazy(() =>
  import('./components/three/GlobalEarthCanvas').then((module) => ({
    default: module.GlobalEarthCanvas
  }))
);

export function App() {
  const mainRef = useRef<HTMLElement | null>(null);

  return (
    <main id="main-content" ref={mainRef} className="cinematic-root min-h-screen overflow-hidden bg-ink text-white">
      <a href="#dashboard" className="skip-link">
        Skip to dashboard
      </a>
      <Suspense fallback={null}>
        <CinematicScrollController scope={mainRef} />
      </Suspense>
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_15%_10%,rgba(98,230,255,.18),transparent_32rem),radial-gradient(circle_at_82%_22%,rgba(154,124,255,.18),transparent_30rem),radial-gradient(circle_at_78%_82%,rgba(255,176,87,.12),transparent_26rem)]" />

      <header className="sticky top-0 z-20 border-b border-cyan/10 bg-ink/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
          <a href="#dashboard" className="flex items-center gap-3 rounded-ui focus:outline-none focus:ring-2 focus:ring-cyan">
            <span className="grid h-10 w-10 place-items-center rounded-ui bg-cyan font-sora font-black text-ink shadow-glow">RQ</span>
            <span>
              <strong className="block font-sora text-sm font-black">ResQNet AI</strong>
              <span className="text-xs text-slate-400">Crisis command foundation</span>
            </span>
          </a>

          <nav aria-label="Primary dashboard navigation" className="hidden items-center gap-2 md:flex">
            {['Overview', 'Infrastructure', 'Global', 'Briefing'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="rounded-ui px-3 py-2 text-sm font-bold text-slate-300 transition hover:bg-white/10 hover:text-cyan focus:outline-none focus:ring-2 focus:ring-cyan"
              >
                {item}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <section
        id="dashboard"
        aria-labelledby="dashboard-title"
        className="dashboard-scene-section mx-auto min-h-[calc(100svh-4.5rem)] max-w-7xl px-5 py-6 lg:py-8"
      >
        <h1 id="dashboard-title" className="sr-only">
          Toronto smart-response command layer
        </h1>
        <div className="toronto-canvas-shell cinematic-scene-shell relative h-full w-full">
          <DeferredScene
            eager
            fallback={
              <div className="scene-frame scene-frame--toronto grid place-items-center rounded-ui border border-cyan/15 bg-white/[0.055] p-5">
                <SkeletonPanel />
              </div>
            }
          >
            <Suspense
              fallback={
                <div className="scene-frame scene-frame--toronto grid place-items-center rounded-ui border border-cyan/15 bg-white/[0.055] p-5">
                  <SkeletonPanel />
                </div>
              }
            >
              <TorontoSmartCityCanvas />
            </Suspense>
          </DeferredScene>
        </div>
      </section>

      <section id="overview" aria-label="Response metrics" className="overview-grid mx-auto grid max-w-7xl gap-4 px-5 py-10 md:grid-cols-4">
        {metrics.map((metric, index) => (
          <MetricCard key={metric.label} metric={metric} index={index} />
        ))}
      </section>

      <section
        id="infrastructure"
        aria-labelledby="infrastructure-title"
        className="mx-auto grid max-w-7xl gap-8 px-5 py-12 lg:grid-cols-[.8fr_1.2fr]"
      >
        <div className="infrastructure-copy">
          <p className="text-xs font-black uppercase text-cyan">AI infrastructure</p>
          <h2 id="infrastructure-title" className="mt-4 font-sora text-4xl font-black">
            Reusable widgets for the operational dashboard.
          </h2>
          <p className="mt-5 text-slate-400">
            Components are intentionally data-driven, keyboard-safe, and motion-aware so future API binding, 3D layers, and scroll systems can be added without rewriting the foundation.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {infrastructureWidgets.map((widget, index) => (
            <div key={widget.title} className="infrastructure-widget-layer">
              <InfrastructureWidget widget={widget} index={index} />
            </div>
          ))}
        </div>
      </section>

      <section className="transition-bridge mx-auto max-w-7xl px-5 py-6" aria-label="Cinematic transition progress">
        <GlassPanel className="overflow-hidden p-5">
          <div className="grid gap-4 md:grid-cols-[.9fr_1.1fr] md:items-center">
            <div>
              <p className="text-xs font-black uppercase text-cyan">Cinematic transition</p>
              <h2 className="mt-3 font-sora text-3xl font-black">Toronto operations expand into global infrastructure.</h2>
            </div>
            <ol className="transition-steps grid gap-3 sm:grid-cols-4">
              {[
                ['toronto', 'Toronto focus'],
                ['systems', 'Systems scale'],
                ['space', 'Space transition'],
                ['global', 'Global mesh']
              ].map(([step, label]) => (
                <li key={step} className="transition-step rounded-ui border border-cyan/15 bg-white/[0.045] p-3" data-step={step}>
                  <span className="block text-xs font-black uppercase text-cyan">{step}</span>
                  <strong className="mt-2 block text-sm text-white">{label}</strong>
                </li>
              ))}
            </ol>
          </div>
        </GlassPanel>
      </section>

      <section
        id="global"
        aria-labelledby="global-title"
        className="mx-auto grid max-w-7xl gap-8 px-5 py-12 lg:grid-cols-[1.05fr_.95fr] lg:items-center"
      >
        <div className="earth-canvas-shell cinematic-scene-shell order-2 lg:order-1">
          <DeferredScene
            rootMargin="960px"
            fallback={
              <div className="scene-frame scene-frame--earth grid place-items-center rounded-ui border border-cyan/15 bg-white/[0.055] p-5">
                <SkeletonPanel />
              </div>
            }
          >
            <Suspense
              fallback={
                <div className="scene-frame scene-frame--earth grid place-items-center rounded-ui border border-cyan/15 bg-white/[0.055] p-5">
                  <SkeletonPanel />
                </div>
              }
            >
              <GlobalEarthCanvas />
            </Suspense>
          </DeferredScene>
        </div>
        <div className="global-copy order-1 lg:order-2">
          <p className="text-xs font-black uppercase text-cyan">Global infrastructure mesh</p>
          <h2 id="global-title" className="mt-4 font-sora text-4xl font-black md:text-5xl">
            AI-powered response intelligence at planetary scale.
          </h2>
          <p className="mt-5 text-lg leading-8 text-slate-400">
            A cinematic Earth layer visualizes global connection arcs, active city nodes, orbital network elements, and resilient data trails without relying on external model or texture downloads.
          </p>
          <div className="mt-7 grid gap-3 sm:grid-cols-2">
            {[
              ['12', 'global city nodes'],
              ['12', 'active response corridors'],
              ['3', 'orbital network rings'],
              ['0', 'external texture fetches']
            ].map(([value, label]) => (
              <GlassPanel key={label} className="p-4">
                <strong className="block font-sora text-3xl font-black text-cyan">{value}</strong>
                <span className="mt-1 block text-sm font-semibold text-slate-400">{label}</span>
              </GlassPanel>
            ))}
          </div>
        </div>
      </section>

      <section id="briefing" aria-labelledby="briefing-title" className="mx-auto max-w-7xl px-5 pb-16">
        <GlassPanel className="p-6">
          <p className="text-xs font-black uppercase text-amber">Loading states</p>
          <h2 id="briefing-title" className="mt-3 font-sora text-3xl font-black">
            Skeletons preserve layout while the live APIs respond.
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <SkeletonPanel />
            <SkeletonPanel />
            <SkeletonPanel />
          </div>
        </GlassPanel>
      </section>
    </main>
  );
}
