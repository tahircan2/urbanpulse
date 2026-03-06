import { Environment } from './environment';

export const environment: Environment = {
  production: true,
  apiUrl: '/api',
  wsUrl:  '/api/ws',
} as const;
