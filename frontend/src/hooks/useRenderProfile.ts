import { useEffect, useMemo, useState } from 'react';
import { useMediaQuery } from './useMediaQuery';

export type RenderQuality = 'high' | 'balanced' | 'low';

export type RenderProfile = {
  quality: RenderQuality;
  lowPower: boolean;
  prefersReducedMotion: boolean;
  isMobile: boolean;
  dpr: [number, number];
  shadows: boolean;
  antialias: boolean;
  postprocessing: boolean;
};

type ClientHints = {
  deviceMemory?: number;
  hardwareConcurrency?: number;
  saveData?: boolean;
  effectiveType?: string;
};

export function useRenderProfile(adaptiveQuality: RenderQuality): RenderProfile {
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const prefersReducedData = useMediaQuery('(prefers-reduced-data: reduce)');
  const isMobile = useMediaQuery('(max-width: 760px)');
  const [clientHints, setClientHints] = useState<ClientHints>({});

  useEffect(() => {
    const nav = navigator as Navigator & {
      deviceMemory?: number;
      connection?: {
        saveData?: boolean;
        effectiveType?: string;
      };
    };

    setClientHints({
      deviceMemory: nav.deviceMemory,
      hardwareConcurrency: nav.hardwareConcurrency,
      saveData: nav.connection?.saveData,
      effectiveType: nav.connection?.effectiveType
    });
  }, []);

  return useMemo(() => {
    const constrainedDevice =
      prefersReducedMotion ||
      prefersReducedData ||
      clientHints.saveData ||
      isMobile ||
      (clientHints.deviceMemory !== undefined && clientHints.deviceMemory <= 4) ||
      (clientHints.hardwareConcurrency !== undefined && clientHints.hardwareConcurrency <= 4) ||
      clientHints.effectiveType === '2g' ||
      clientHints.effectiveType === 'slow-2g';
    const lowPower = adaptiveQuality === 'low' || constrainedDevice;
    const balanced = adaptiveQuality === 'balanced' && !constrainedDevice;
    const quality: RenderQuality = lowPower ? 'low' : balanced ? 'balanced' : 'high';

    return {
      quality,
      lowPower,
      prefersReducedMotion,
      isMobile,
      dpr: lowPower ? [1, 1.15] : balanced ? [1, 1.45] : [1, 1.7],
      shadows: quality === 'high',
      antialias: quality !== 'low',
      postprocessing: quality === 'high'
    };
  }, [adaptiveQuality, clientHints, isMobile, prefersReducedData, prefersReducedMotion]);
}
