import type { CSSProperties } from 'react';
import type { InfrastructureWidget as Widget } from '../../types/dashboard';
import { toneClass } from '../../utils/tone';
import { GlassPanel } from '../ui/GlassPanel';

type InfrastructureWidgetProps = {
  widget: Widget;
  index: number;
};

export function InfrastructureWidget({ widget, index }: InfrastructureWidgetProps) {
  return (
    <GlassPanel
      as="article"
      style={
        {
          '--reveal-delay': `${index * 45}ms`,
          '--progress-scale': widget.progress / 100
        } as CSSProperties
      }
      className="reveal-card p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-sora text-base font-bold text-white">{widget.title}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-400">{widget.description}</p>
        </div>
        <span className={`h-3 w-3 shrink-0 rounded-full bg-current shadow-[0_0_22px_currentColor] ${toneClass(widget.tone)}`} />
      </div>
      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-xs font-bold uppercase text-slate-500">
          <span>{widget.signal}</span>
          <span>{widget.progress}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white/10">
          <div className={`widget-progress h-full rounded-full bg-current ${toneClass(widget.tone)}`} />
        </div>
      </div>
    </GlassPanel>
  );
}
