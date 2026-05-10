import type { CSSProperties } from 'react';
import type { Metric } from '../../types/dashboard';
import { toneClass } from '../../utils/tone';
import { GlassPanel } from './GlassPanel';

type MetricCardProps = {
  metric: Metric;
  index: number;
};

export function MetricCard({ metric, index }: MetricCardProps) {
  return (
    <GlassPanel
      as="article"
      style={{ '--reveal-delay': `${index * 55}ms` } as CSSProperties}
      className="metric-card reveal-card group p-5 transition hover:-translate-y-1 hover:border-cyan/35 hover:shadow-glow"
    >
      <p className="text-xs font-bold uppercase text-slate-400">{metric.label}</p>
      <strong className={`mt-4 block font-sora text-4xl font-black ${toneClass(metric.tone)}`}>
        {metric.value}
      </strong>
      <p className="mt-2 text-sm text-slate-400">{metric.detail}</p>
    </GlassPanel>
  );
}
