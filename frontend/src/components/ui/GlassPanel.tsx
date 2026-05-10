import { createElement, type ElementType, type ReactNode } from 'react';

type GlassPanelProps = {
  as?: ElementType;
  children: ReactNode;
  className?: string;
  [key: string]: unknown;
};

export function GlassPanel({
  as,
  children,
  className = '',
  ...props
}: GlassPanelProps) {
  const Component = as ?? 'section';

  return createElement(
    Component as ElementType,
    {
      className: `rounded-ui border border-cyan/15 bg-white/[0.055] shadow-2xl shadow-black/30 backdrop-blur-xl ${className}`,
      ...props
    },
    children
  );
}
