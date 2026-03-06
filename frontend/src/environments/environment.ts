export interface Environment {
  production: boolean;
  apiUrl: string;
  wsUrl: string;
}

export const environment: Environment = {
  production: false,
  apiUrl: 'http://localhost:8080/api',
  wsUrl:  'http://localhost:8080/api/ws',
} as const;
