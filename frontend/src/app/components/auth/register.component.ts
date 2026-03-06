import { ChangeDetectionStrategy, Component, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrl: './auth.component.scss',
})
export class RegisterComponent {
  private readonly auth   = inject(AuthService);
  private readonly router = inject(Router);

  name     = '';
  email    = '';
  password = '';
  district = '';

  readonly error   = signal('');
  readonly loading = signal(false);

  readonly districts = [
    'Kadıköy','Beşiktaş','Şişli','Beyoğlu','Fatih','Üsküdar',
    'Bağcılar','Maltepe','Ataşehir','Pendik','Bakırköy','Sarıyer',
  ];

  submit(): void {
    const n = this.name.trim();
    const e = this.email.trim();
    const p = this.password;

    if (!n || !e || !p) {
      this.error.set('Please fill in all required fields');
      return;
    }
    if (p.length < 6) {
      this.error.set('Password must be at least 6 characters');
      return;
    }

    this.loading.set(true);
    this.error.set('');

    this.auth.register({
      name: n, email: e, password: p,
      district: this.district || undefined,
      role: 'CITIZEN',
    }).subscribe({
      next: () => this.router.navigate(['/']),
      error: err => {
        this.error.set(err.error?.message || 'Registration failed. Please try again.');
        this.loading.set(false);
      },
    });
  }
}
