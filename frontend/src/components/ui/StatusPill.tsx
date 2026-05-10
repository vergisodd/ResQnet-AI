import type { StatusItem } from '../../types/dashboard';
import { toneClass } from '../../utils/tone';

type StatusPillProps = {
  item: StatusItem;
};

export function StatusPill({ item }: StatusPillProps) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-ui border border-cyan/15 bg-white/[0.045] px-3 py-2">
      <span className="text-sm font-semibold text-slate-300">{item.label}</span>
      <span className={`inline-flex items-center gap-2 text-xs font-black uppercase ${toneClass(item.tone)}`}>
        <span className="h-2 w-2 rounded-full bg-current shadow-[0_0_16px_currentColor]" />
        {item.value}
      </span>
    </li>
  );
}
