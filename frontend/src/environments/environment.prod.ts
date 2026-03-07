import { Environment } from './environment';

export const environment: Environment = {
  production: true,
  apiUrl: '/api',
  wsUrl:  'wss://urbanpulse-production.up.railway.app/api/ws',
} as const;
