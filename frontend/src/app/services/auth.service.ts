import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { ApiResponse } from '../models/api.model';
import { AuthResponse, AuthUser, LoginRequest, RegisterRequest } from '../models/auth.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'up_token';
  private readonly USER_KEY  = 'up_user';

  // FIX: Inject PLATFORM_ID to safely check localStorage (SSR-safe)
  private readonly platformId = inject(PLATFORM_ID);
  private readonly http       = inject(HttpClient);
  private readonly router     = inject(Router);

  // Signal initialized safely - no localStorage access during SSR
  readonly currentUser = signal<AuthUser | null>(this.loadUser());

  login(req: LoginRequest): Observable<ApiResponse<AuthResponse>> {
    return this.http
      .post<ApiResponse<AuthResponse>>(`${environment.apiUrl}/auth/login`, req)
      .pipe(tap(res => { if (res.success) this.saveSession(res.data); }));
  }

  register(req: RegisterRequest): Observable<ApiResponse<AuthResponse>> {
    return this.http
      .post<ApiResponse<AuthResponse>>(`${environment.apiUrl}/auth/register`, req)
      .pipe(tap(res => { if (res.success) this.saveSession(res.data); }));
  }

  logout(): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);
    }
    this.currentUser.set(null);
    this.router.navigate(['/']);
  }

  getToken(): string | null {
    if (!isPlatformBrowser(this.platformId)) return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  isStaffOrAdmin(): boolean {
    const u = this.currentUser();
    return !!u && (u.role === 'STAFF' || u.role === 'ADMIN');
  }

  private saveSession(data: AuthResponse): void {
    const user: AuthUser = {
      userId: data.userId,
      name:   data.name,
      email:  data.email,
      role:   data.role,
      token:  data.token,
    };
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.TOKEN_KEY, data.token);
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
    this.currentUser.set(user);
  }

  private loadUser(): AuthUser | null {
    // FIX: Guard localStorage access for SSR compatibility
    if (!isPlatformBrowser(this.platformId)) return null;
    try {
      const raw = localStorage.getItem(this.USER_KEY);
      if (!raw) return null;
      const user = JSON.parse(raw) as AuthUser;
      // Validate parsed object has required fields
      if (!user.token || !user.email || !user.role) return null;
      return user;
    } catch {
      return null;
    }
  }
}
