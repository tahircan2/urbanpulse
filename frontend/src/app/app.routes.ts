import { Routes } from '@angular/router';
import { authGuard, staffGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/home/home.component').then(m => m.HomeComponent),
    title: 'UrbanPulse — Smart City Platform',
  },
  {
    path: 'map',
    loadComponent: () =>
      import('./components/map/map.component').then(m => m.MapComponent),
    title: 'Live City Map — UrbanPulse',
  },
  {
    path: 'report',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/report/report.component').then(m => m.ReportComponent),
    title: 'Report Incident — UrbanPulse',
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Dashboard — UrbanPulse',
  },
  {
    path: 'about',
    loadComponent: () =>
      import('./components/about/about.component').then(m => m.AboutComponent),
    title: 'About — UrbanPulse',
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./components/auth/login.component').then(m => m.LoginComponent),
    title: 'Sign In — UrbanPulse',
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./components/auth/register.component').then(m => m.RegisterComponent),
    title: 'Create Account — UrbanPulse',
  },
  { path: '**', redirectTo: '', pathMatch: 'full' },
];
