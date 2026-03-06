export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: 'CITIZEN' | 'STAFF' | 'ADMIN';
  district?: string;
  enabled: boolean;
  createdAt: string;
  incidentCount: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  number: number;
  size: number;
  first: boolean;
  last: boolean;
}

export interface DashboardStats {
  total: number;
  pending: number;
  inProgress: number;   // FIX: was both 'active' and 'inProgress' causing template bug
  resolved: number;
  closed: number;
  critical: number;
  aiProcessed: number;
  agentLogsTotal: number;
  agentSuccessRate: number;
}
