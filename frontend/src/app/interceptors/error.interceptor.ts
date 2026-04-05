import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

// FIX: Prevent redirect loop - track if we're already on a public route
const PUBLIC_PATHS = ['/auth/login', '/auth/register'];

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const auth   = inject(AuthService);

  return next(req).pipe(
    catchError(err => {
      // Only force logout on 401/403 for non-auth endpoints
      if ((err.status === 401 || err.status === 403) && !PUBLIC_PATHS.some(p => req.url.includes(p))) {
        auth.triggerSessionExpired();
      }
      return throwError(() => err);
    })
  );
};
