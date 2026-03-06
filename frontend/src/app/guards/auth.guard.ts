import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) return true;

  // Preserve return URL
  router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
  return false;
};

export const staffGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (auth.isStaffOrAdmin()) return true;

  // If logged in but wrong role, send home; else send to login
  if (auth.isLoggedIn()) {
    router.navigate(['/']);
  } else {
    router.navigate(['/login']);
  }
  return false;
};
