export type Tone = 'cyan' | 'blue' | 'violet' | 'amber' | 'green' | 'critical';

export type Metric = {
  label: string;
  value: string;
  detail: string;
  tone: Tone;
};

export type StatusItem = {
  label: string;
  value: string;
  tone: Tone;
};

export type InfrastructureWidget = {
  title: string;
  description: string;
  signal: string;
  progress: number;
  tone: Tone;
};
