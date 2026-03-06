import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import {
  provideRouter,
  withViewTransitions,
  withPreloading,
  PreloadAllModules,
  withRouterConfig,
} from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import { routes } from './app.routes';
import { jwtInterceptor } from './interceptors/jwt.interceptor';
import { errorInterceptor } from './interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    /*
      PERFORMANCE:
      - provideZoneChangeDetection({ eventCoalescing: true }) — coalesces multiple
        change detection cycles triggered in the same microtask into one.
      - withFetch() — uses native fetch instead of XHR (faster, streams, HTTP/2).
      - provideAnimationsAsync() — lazy-loads animation module, faster initial paint.
      - withPreloading(PreloadAllModules) — after app loads, silently preloads all
        lazy routes so navigation feels instant.
      - withViewTransitions() — browser View Transitions API for smooth page changes.
      - withRouterConfig({ onSameUrlNavigation: 'ignore' }) — skip re-renders on
        same URL navigation.
    */
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(
      routes,
      withViewTransitions({
        skipInitialTransition: true,
      }),
      withPreloading(PreloadAllModules),
      withRouterConfig({ onSameUrlNavigation: 'ignore' }),
    ),
    provideAnimationsAsync(),
    provideHttpClient(
      withFetch(),
      withInterceptors([jwtInterceptor, errorInterceptor]),
    ),
  ],
};
