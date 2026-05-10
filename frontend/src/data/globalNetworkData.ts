export type GeoPoint = {
  id: string;
  label: string;
  lat: number;
  lon: number;
  tone: 'cyan' | 'blue' | 'violet' | 'amber';
};

export type GlobalConnection = {
  id: string;
  from: string;
  to: string;
  tone: 'cyan' | 'blue' | 'violet' | 'amber';
};

export const globalNodes: GeoPoint[] = [
  { id: 'toronto', label: 'Toronto', lat: 43.6532, lon: -79.3832, tone: 'cyan' },
  { id: 'new-york', label: 'New York', lat: 40.7128, lon: -74.006, tone: 'blue' },
  { id: 'london', label: 'London', lat: 51.5072, lon: -0.1276, tone: 'violet' },
  { id: 'lagos', label: 'Lagos', lat: 6.5244, lon: 3.3792, tone: 'amber' },
  { id: 'dubai', label: 'Dubai', lat: 25.2048, lon: 55.2708, tone: 'cyan' },
  { id: 'mumbai', label: 'Mumbai', lat: 19.076, lon: 72.8777, tone: 'blue' },
  { id: 'singapore', label: 'Singapore', lat: 1.3521, lon: 103.8198, tone: 'cyan' },
  { id: 'tokyo', label: 'Tokyo', lat: 35.6762, lon: 139.6503, tone: 'violet' },
  { id: 'sydney', label: 'Sydney', lat: -33.8688, lon: 151.2093, tone: 'amber' },
  { id: 'sao-paulo', label: 'Sao Paulo', lat: -23.5558, lon: -46.6396, tone: 'blue' },
  { id: 'mexico-city', label: 'Mexico City', lat: 19.4326, lon: -99.1332, tone: 'amber' },
  { id: 'vancouver', label: 'Vancouver', lat: 49.2827, lon: -123.1207, tone: 'cyan' }
];

export const globalConnections: GlobalConnection[] = [
  { id: 'toronto-london', from: 'toronto', to: 'london', tone: 'cyan' },
  { id: 'toronto-new-york', from: 'toronto', to: 'new-york', tone: 'blue' },
  { id: 'toronto-vancouver', from: 'toronto', to: 'vancouver', tone: 'cyan' },
  { id: 'london-dubai', from: 'london', to: 'dubai', tone: 'violet' },
  { id: 'dubai-mumbai', from: 'dubai', to: 'mumbai', tone: 'cyan' },
  { id: 'mumbai-singapore', from: 'mumbai', to: 'singapore', tone: 'blue' },
  { id: 'singapore-tokyo', from: 'singapore', to: 'tokyo', tone: 'cyan' },
  { id: 'tokyo-sydney', from: 'tokyo', to: 'sydney', tone: 'violet' },
  { id: 'new-york-mexico', from: 'new-york', to: 'mexico-city', tone: 'amber' },
  { id: 'mexico-sao-paulo', from: 'mexico-city', to: 'sao-paulo', tone: 'blue' },
  { id: 'london-lagos', from: 'london', to: 'lagos', tone: 'amber' },
  { id: 'lagos-dubai', from: 'lagos', to: 'dubai', tone: 'cyan' }
];

export const toneColors = {
  cyan: '#62e6ff',
  blue: '#3a8bff',
  violet: '#9a7cff',
  amber: '#ffb057'
} satisfies Record<GeoPoint['tone'], string>;
