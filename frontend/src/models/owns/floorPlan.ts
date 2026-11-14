import { Audit } from './audit';

export type FloorPlanKind =
  | 'ARCHITECTURAL'
  | 'MEP'
  | 'FIRE_SAFETY'
  | 'SECURITY'
  | 'OTHER';

export const floorPlanKinds: FloorPlanKind[] = [
  'ARCHITECTURAL',
  'MEP',
  'FIRE_SAFETY',
  'SECURITY',
  'OTHER'
];

export interface FloorPlanFile {
  id: number;
  name: string;
  url: string;
  thumbnailUrl?: string;
}

export default interface FloorPlan extends Audit {
  id: number;
  name: string;
  area: number;
  kind?: FloorPlanKind | null;
  revision?: string | null;
  note?: string | null;
  image?: FloorPlanFile | null;
  sourceFile?: FloorPlanFile | null;
  current?: boolean;
  supersededById?: number | null;
  pinCount?: number;
}

export interface PinAsset {
  id: number;
  name: string;
  customId?: string;
  status: string;
  image?: { url: string } | null;
  openWorkOrders?: number;
}

export interface FloorPlanPin {
  id: number;
  x: number;
  y: number;
  asset: PinAsset;
}

export interface PinnableAsset {
  id: number;
  name: string;
  customId?: string;
  status: string;
}

export interface AssetFloorPlanPin {
  floorPlan: {
    id: number;
    name: string;
    kind?: FloorPlanKind | null;
    revision?: string | null;
    locationId: number;
  };
  x: number;
  y: number;
}
