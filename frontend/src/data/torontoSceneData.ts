export type Vec3 = [number, number, number];

export type CityNode = {
  id: string;
  label: string;
  metric: string;
  position: Vec3;
  tone: 'cyan' | 'blue' | 'violet' | 'amber';
};

export type NetworkPath = {
  id: string;
  color: string;
  points: Vec3[];
};

export type BuildingSpec = {
  position: Vec3;
  scale: Vec3;
  tone: 'glass' | 'cyan' | 'blue';
};

export const cityNodes: CityNode[] = [
  { id: 'union', label: 'Union Station', metric: '97% flow', position: [-1.35, 0.34, 0.92], tone: 'cyan' },
  { id: 'financial', label: 'Financial Core', metric: '14k events', position: [0.44, 0.48, 0.16], tone: 'blue' },
  { id: 'waterfront', label: 'Waterfront Mesh', metric: '0.8s route', position: [1.74, 0.32, 1.38], tone: 'amber' },
  { id: 'north', label: 'North Corridor', metric: '92% sync', position: [-2.12, 0.4, -1.16], tone: 'violet' },
  { id: 'east', label: 'East Exchange', metric: 'active', position: [2.18, 0.35, -0.86], tone: 'cyan' }
];

export const networkPaths: NetworkPath[] = [
  {
    id: 'gardiner',
    color: '#ffb057',
    points: [[-3.9, 0.055, 1.95], [-2.4, 0.055, 1.45], [-0.6, 0.055, 1.05], [1.1, 0.055, 1.22], [3.7, 0.055, 1.7]]
  },
  {
    id: 'yonge',
    color: '#62e6ff',
    points: [[0.1, 0.06, 2.2], [0.15, 0.06, 0.95], [0.1, 0.06, -0.45], [-0.05, 0.06, -2.3]]
  },
  {
    id: 'bloor',
    color: '#3a8bff',
    points: [[-3.5, 0.058, -1.22], [-1.65, 0.058, -1.0], [0.35, 0.058, -1.08], [2.8, 0.058, -0.78]]
  },
  {
    id: 'spadina',
    color: '#9a7cff',
    points: [[-1.75, 0.057, 1.85], [-1.35, 0.057, 0.65], [-1.0, 0.057, -0.45], [-0.82, 0.057, -1.8]]
  },
  {
    id: 'don-valley',
    color: '#62e6ff',
    points: [[2.8, 0.056, 1.75], [2.05, 0.056, 0.65], [1.55, 0.056, -0.42], [1.25, 0.056, -1.82]]
  }
];

export function createBuildingSpecs(isCompact = false) {
  const specs: BuildingSpec[] = [];
  const columns = isCompact ? 11 : 15;
  const rows = isCompact ? 8 : 10;

  for (let x = 0; x < columns; x += 1) {
    for (let z = 0; z < rows; z += 1) {
      const px = (x - (columns - 1) / 2) * 0.48;
      const pz = (z - (rows - 1) / 2) * 0.45;
      const distance = Math.hypot(px * 0.68, pz);

      if ((x + z) % 6 === 0 && distance > 2.4) continue;

      const towerBoost = Math.max(0, 1.8 - distance) * 0.58;
      const wave = Math.sin(x * 1.7 + z * 0.8) * 0.16 + Math.cos(z * 1.3) * 0.08;
      const height = Math.max(0.13, 0.28 + towerBoost + wave);
      const tone = distance < 1.4 ? 'cyan' : (x + z) % 4 === 0 ? 'blue' : 'glass';

      specs.push({
        position: [px, height / 2, pz],
        scale: [0.24 + ((x + z) % 3) * 0.032, height, 0.21 + (z % 3) * 0.032],
        tone
      });
    }
  }

  return specs;
}

export function createDataBarSpecs() {
  return cityNodes.flatMap((node, nodeIndex) =>
    [0, 1, 2].map((offset) => ({
      position: [
        node.position[0] + (offset - 1) * 0.14,
        0.42,
        node.position[2] - 0.24 - nodeIndex * 0.015
      ] as Vec3,
      height: 0.3 + ((nodeIndex + offset) % 3) * 0.18,
      tone: node.tone
    }))
  );
}
