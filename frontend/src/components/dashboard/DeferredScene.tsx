import { useEffect, useRef, useState, type ReactNode } from 'react';

type DeferredSceneProps = {
  children: ReactNode;
  fallback: ReactNode;
  rootMargin?: string;
  eager?: boolean;
};

export function DeferredScene({
  children,
  fallback,
  rootMargin = '720px',
  eager = false
}: DeferredSceneProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [shouldRender, setShouldRender] = useState(eager);

  useEffect(() => {
    if (shouldRender) return undefined;
    const container = containerRef.current;
    if (!container) return undefined;

    if (!('IntersectionObserver' in window)) {
      setShouldRender(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShouldRender(true);
          observer.disconnect();
        }
      },
      { rootMargin }
    );

    observer.observe(container);
    return () => observer.disconnect();
  }, [rootMargin, shouldRender]);

  return <div ref={containerRef}>{shouldRender ? children : fallback}</div>;
}
