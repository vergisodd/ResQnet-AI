import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import type { RefObject } from 'react';
import { setSceneTransitionProgress } from './sceneTransitionState';

gsap.registerPlugin(ScrollTrigger, useGSAP);

type CinematicScrollControllerProps = {
  scope: RefObject<HTMLElement | null>;
};

export function CinematicScrollController({ scope }: CinematicScrollControllerProps) {
  useGSAP(
    () => {
      const root = scope.current ?? document.querySelector<HTMLElement>('.cinematic-root');
      if (!root) return undefined;

      const animatedSelectors = [
        '.toronto-canvas-shell',
        '.overview-grid',
        '.infrastructure-copy',
        '.infrastructure-widget-layer',
        '.transition-bridge',
        '.earth-canvas-shell',
        '.global-copy',
        '.transition-step'
      ];
      let lastProgress = -1;

      const updateProgress = (progress: number) => {
        if (Math.abs(progress - lastProgress) < 0.001) return;
        lastProgress = progress;
        setSceneTransitionProgress(progress);
        root.style.setProperty('--scene-progress', progress.toFixed(3));
      };

      const media = gsap.matchMedia();

      media.add(
        {
          all: 'all',
          reducedMotion: '(prefers-reduced-motion: reduce)',
          coarsePointer: '(pointer: coarse)'
        },
        (context) => {
          const dashboard = root.querySelector<HTMLElement>('#dashboard');
          const global = root.querySelector<HTMLElement>('#global');
          if (!dashboard || !global) return undefined;

          if (context.conditions?.reducedMotion) {
            updateProgress(1);
            gsap.set(gsap.utils.toArray<HTMLElement>('.transition-step', root), {
              autoAlpha: 1,
              y: 0,
              clearProps: 'transform'
            });
            return undefined;
          }

          const animatedTargets = gsap.utils.toArray<HTMLElement>(animatedSelectors.join(','), root);
          const stepTargets = gsap.utils.toArray<HTMLElement>('.transition-step', root);

          gsap.set(animatedTargets, { willChange: 'transform, opacity' });
          gsap.set(stepTargets, { autoAlpha: 0.44, y: 8 });
          gsap.set('.transition-step[data-step="toronto"]', { autoAlpha: 1, y: 0 });

          const timeline = gsap.timeline({
            defaults: { ease: 'none', overwrite: 'auto' },
            scrollTrigger: {
              id: 'resqnet-cinematic-transition',
              trigger: dashboard,
              endTrigger: global,
              start: 'top top',
              end: 'center center',
              scrub: context.conditions?.coarsePointer ? 0.65 : 1.05,
              invalidateOnRefresh: true,
              fastScrollEnd: true,
              refreshPriority: 0,
              onUpdate: (self) => updateProgress(self.progress),
              onRefresh: (self) => updateProgress(self.progress)
            }
          });

          timeline
            .addLabel('toronto', 0)
            .to('.toronto-canvas-shell', { y: -74, autoAlpha: 0.72, duration: 0.58 }, 'toronto')
            .to('.overview-grid', { y: -42, autoAlpha: 0.72, duration: 0.46 }, 0.15)
            .addLabel('systems', 0.28)
            .fromTo(
              '.transition-bridge',
              { y: 72, autoAlpha: 0, scale: 0.96 },
              { y: 0, autoAlpha: 1, scale: 1, duration: 0.34 },
              'systems'
            )
            .to('.transition-step[data-step="toronto"]', { autoAlpha: 0.46, y: -8, duration: 0.18 }, 'systems')
            .to('.transition-step[data-step="systems"]', { autoAlpha: 1, y: 0, duration: 0.2 }, 'systems+=0.08')
            .to('.infrastructure-copy', { y: -54, autoAlpha: 0.72, duration: 0.42 }, 0.34)
            .to('.infrastructure-widget-layer', { y: -46, autoAlpha: 0.78, stagger: 0.035, duration: 0.44 }, 0.38)
            .addLabel('space', 0.54)
            .to('.transition-step[data-step="systems"]', { autoAlpha: 0.48, y: -8, duration: 0.18 }, 'space')
            .to('.transition-step[data-step="space"]', { autoAlpha: 1, y: 0, duration: 0.2 }, 'space+=0.06')
            .fromTo(
              '.earth-canvas-shell',
              { y: 90, scale: 0.82, autoAlpha: 0.16 },
              { y: 0, scale: 1, autoAlpha: 1, duration: 0.44 },
              'space'
            )
            .fromTo(
              '.global-copy',
              { y: 82, autoAlpha: 0.18 },
              { y: 0, autoAlpha: 1, duration: 0.42 },
              'space+=0.06'
            )
            .addLabel('global', 0.78)
            .to('.transition-step[data-step="space"]', { autoAlpha: 0.48, y: -8, duration: 0.16 }, 'global')
            .to('.transition-step[data-step="global"]', { autoAlpha: 1, y: 0, duration: 0.2 }, 'global+=0.04')
            .to('.transition-bridge', { y: -38, autoAlpha: 0.62, scale: 0.985, duration: 0.22 }, 0.88);

          const refreshId = window.requestAnimationFrame(() => ScrollTrigger.refresh());

          return () => {
            window.cancelAnimationFrame(refreshId);
            timeline.kill();
            gsap.set(animatedTargets, { clearProps: 'willChange' });
          };
        },
        root
      );

      return () => {
        media.revert();
        setSceneTransitionProgress(0);
        root.style.removeProperty('--scene-progress');
      };
    },
    { scope }
  );

  return null;
}
