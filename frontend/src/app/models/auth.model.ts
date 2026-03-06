export type UserRole = 'CITIZEN' | 'STAFF' | 'ADMIN';

export interface LoginRequest    { email: string; password: string; }
export interface RegisterRequest { name: string; email: string; password: string; role?: UserRole; district?: string; }
export interface AuthResponse    { token: string; type: string; userId: number; name: string; email: string; role: UserRole; }
export interface AuthUser        { userId: number; name: string; email: string; role: UserRole; token: string; }
