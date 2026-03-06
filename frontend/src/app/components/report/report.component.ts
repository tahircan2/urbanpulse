import { ChangeDetectionStrategy, Component, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  IncidentSubmission, IncidentCategory, IncidentPriority,
  CATEGORY_LABELS, PRIORITY_LABELS,
} from '../../models/incident.model';
import { IncidentService } from '../../services/incident.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './report.component.html',
  styleUrl: './report.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportComponent {
  private readonly incidentService = inject(IncidentService);
  readonly auth = inject(AuthService);

  readonly categories = Object.entries(CATEGORY_LABELS) as [IncidentCategory, string][];
  readonly districts  = [
    'Kadıköy','Beşiktaş','Şişli','Beyoğlu','Fatih','Üsküdar',
    'Bağcılar','Maltepe','Ataşehir','Pendik','Bakırköy','Sarıyer',
  ];

  readonly districtCoords: Record<string, [number, number]> = {
    'Kadıköy':  [40.9902, 29.0208],
    'Beşiktaş': [41.0426, 29.0089],
    'Şişli':    [41.0601, 28.9877],
    'Beyoğlu':  [41.0284, 28.9738],
    'Fatih':    [41.0184, 28.9431],
    'Üsküdar':  [41.0232, 29.0223],
    'Bağcılar': [41.0336, 28.8509],
    'Maltepe':  [40.9238, 29.1309],
    'Ataşehir': [40.9850, 29.1245],
    'Pendik':   [40.8767, 29.2346],
    'Bakırköy': [40.9833, 28.8667],
    'Sarıyer':  [41.1683, 29.0538],
  };

  readonly PRIORITY_LABELS = PRIORITY_LABELS;

  form: IncidentSubmission = this.defaultForm();

  readonly submitting  = signal(false);
  readonly submitted   = signal(false);
  readonly submittedId = signal<number | null>(null);
  readonly error       = signal('');

  submit(): void {
    if (!this.form.title?.trim() || !this.form.description?.trim()) return;
    this.submitting.set(true);
    this.error.set('');

    this.incidentService.submitIncident(this.form).subscribe({
      next: res => {
        this.submitting.set(false);
        if (res.success) {
          this.submitted.set(true);
          this.submittedId.set(res.data.id);
        }
      },
      error: err => {
        this.error.set(err.error?.message || 'Submission failed. Please try again.');
        this.submitting.set(false);
      },
    });
  }

  reset(): void {
    this.submitted.set(false);
    this.submittedId.set(null);
    this.form = this.defaultForm();
  }

  onDistrictChange(district: string): void {
    const coords = this.districtCoords[district];
    if (coords) {
      // Add slight random offset to prevent perfect marker stacking
      const latOffset = (Math.random() - 0.5) * 0.015;
      const lngOffset = (Math.random() - 0.5) * 0.015;
      this.form.latitude = coords[0] + latOffset;
      this.form.longitude = coords[1] + lngOffset;
    }
  }

  // FIX: Explicit number conversion for range input
  setPriority(value: string): void {
    this.form.priority = parseInt(value, 10) as IncidentPriority;
  }

  getPriorityColor(p: number): string {
    if (p >= 5) return 'var(--danger)';
    if (p >= 4) return 'var(--accent2)';
    if (p >= 3) return 'var(--warning)';
    return 'var(--success)';
  }

  private defaultForm(): IncidentSubmission {
    return {
      title:       '',
      description: '',
      category:    'TRAFFIC_ACCIDENT',
      priority:    3 as IncidentPriority,
      latitude:    41.0082,
      longitude:   28.9784,
      district:    'Şişli',
    };
  }
}
