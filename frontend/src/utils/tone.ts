import type { Tone } from '../types/dashboard';

export function toneClass(tone: Tone) {
  const classes: Record<Tone, string> = {
    cyan: 'text-cyan',
    blue: 'text-electric',
    violet: 'text-violet',
    amber: 'text-amber',
    green: 'text-emerald-300',
    critical: 'text-rose-300'
  };

  return classes[tone];
}
