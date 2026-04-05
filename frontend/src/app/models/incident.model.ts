export type IncidentCategory =
  | 'TRAFFIC_ACCIDENT'
  | 'ROAD_DAMAGE'
  | 'FLOODING'
  | 'POWER_OUTAGE'
  | 'FIRE_HAZARD'
  | 'VANDALISM'
  | 'NOISE_COMPLAINT'
  | 'OTHER';

export type IncidentStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED';

// FIX: Use number union - this is what backend sends
export type IncidentPriority = 1 | 2 | 3 | 4 | 5;

export interface Incident {
  // FIX: id is number (backend Long), not string
  id: number;
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  priority: IncidentPriority;
  latitude: number;
  longitude: number;
  district: string;
  neighbourhood?: string;
  street?: string;
  reporterName: string;
  photoUrl?: string;
  createdAt: string;   // ISO string from backend - use string not Date to avoid parse issues
  updatedAt: string;
  resolvedAt?: string;
  assignedDepartment?: string;
  agentProcessed: boolean;
  agentNotes?: string;
}

export interface IncidentSubmission {
  title: string;
  description: string;
  category: IncidentCategory;
  priority: IncidentPriority;
  latitude: number;
  longitude: number;
  district: string;
  neighbourhood?: string;
  street?: string;
  reporterName?: string;
  reporterEmail?: string;
}

export const CATEGORY_LABELS: Record<IncidentCategory, string> = {
  TRAFFIC_ACCIDENT: 'Trafik Kazası',
  ROAD_DAMAGE:      'Yol Hasarı',
  FLOODING:         'Su Baskını',
  POWER_OUTAGE:     'Elektrik Kesintisi',
  FIRE_HAZARD:      'Yangın Tehlikesi',
  VANDALISM:        'Vandalizm / Tahribat',
  NOISE_COMPLAINT:  'Gürültü Şikayeti',
  OTHER:            'Diğer',
};

export const CATEGORY_ICONS: Record<IncidentCategory, string> = {
  TRAFFIC_ACCIDENT: 'fa-car-crash',
  ROAD_DAMAGE:      'fa-road',
  FLOODING:         'fa-water',
  POWER_OUTAGE:     'fa-bolt',
  FIRE_HAZARD:      'fa-fire',
  VANDALISM:        'fa-spray-can',
  NOISE_COMPLAINT:  'fa-volume-high',
  OTHER:            'fa-circle-exclamation',
};

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  PENDING:     'Bekliyor',
  IN_PROGRESS: 'İşlemde',
  RESOLVED:    'Çözüldü',
  CLOSED:      'Kapatıldı',
};

export const PRIORITY_LABELS: Record<IncidentPriority, string> = {
  1: '1. Seviye Öncelik',
  2: '2. Seviye Öncelik',
  3: '3. Seviye Öncelik',
  4: '4. Seviye Öncelik',
  5: '5. Seviye Öncelik',
};

export const PRIORITY_CLASSES: Record<IncidentPriority, string> = {
  1: 'badge-cyan',
  2: 'badge-cyan',
  3: 'badge-yellow',
  4: 'badge-orange',
  5: 'badge-red',
};

export const STATUS_CLASSES: Record<IncidentStatus, string> = {
  PENDING:     'badge-yellow',
  IN_PROGRESS: 'badge-orange',
  RESOLVED:    'badge-green',
  CLOSED:      'badge-cyan',
};
