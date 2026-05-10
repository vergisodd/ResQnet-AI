import type { InfrastructureWidget, Metric, StatusItem } from '../types/dashboard';

export const metrics: Metric[] = [
  { label: 'Reports Analyzed', value: '14', detail: 'Toronto flood simulation', tone: 'cyan' },
  { label: 'Critical Cases', value: '4', detail: 'needs immediate review', tone: 'critical' },
  { label: 'Units Deployed', value: '10', detail: 'optimized assignments', tone: 'blue' },
  { label: 'Time Saved', value: '55%', detail: 'estimated response lift', tone: 'amber' }
];

export const statuses: StatusItem[] = [
  { label: 'Backend', value: 'Online', tone: 'green' },
  { label: 'AI Routing', value: 'Ready', tone: 'cyan' },
  { label: 'Map Layer', value: 'Standby', tone: 'blue' },
  { label: 'Briefing', value: 'Awaiting Run', tone: 'violet' }
];

export const infrastructureWidgets: InfrastructureWidget[] = [
  {
    title: 'Voice Intake',
    description: 'ElevenLabs post-call payloads normalized into structured decision records.',
    signal: 'conversation_critical_info',
    progress: 82,
    tone: 'cyan'
  },
  {
    title: 'Priority Engine',
    description: 'Urgency, vulnerability, affected people, and mass-care needs scored transparently.',
    signal: 'risk tier active',
    progress: 91,
    tone: 'blue'
  },
  {
    title: 'Resource Optimizer',
    description: 'Greedy assignment matrix balances suitability, capacity, priority, and distance.',
    signal: 'quantum-inspired mode ready',
    progress: 76,
    tone: 'violet'
  },
  {
    title: 'Command Briefing',
    description: 'Coordinator-ready summaries explain deployment actions and remaining constraints.',
    signal: 'planner standby',
    progress: 68,
    tone: 'amber'
  }
];
