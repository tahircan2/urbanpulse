import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-agent-message',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (isSecurityAlert) {
      <div class="agent-message security-alert">
        <div class="am-header"><i class="fas fa-shield-halved"></i> Güvenlik İhlali Tespit Edildi</div>
        <div class="am-content">{{ securityReason }}</div>
      </div>
    } @else {
      <div class="agent-message normal">
        <div class="am-header"><i class="fas fa-robot"></i> AI Processed Output</div>
        <ul class="am-steps">
          @for (step of parsedSteps; track step; let idx = $index) {
            <li>
              <span class="am-step-badge">{{ getStepLabel(idx) }}</span>
              <span class="am-step-text">{{ step }}</span>
            </li>
          }
        </ul>
      </div>
    }
  `,
  styles: [`
    .agent-message {
      border-radius: 8px;
      overflow: hidden;
      font-size: 0.85rem;
      border: 1px solid var(--border-color);
    }
    .am-header {
      padding: 0.6rem 0.8rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .security-alert {
      border-color: #FF4D6D;
      background: rgba(255, 77, 109, 0.05);
    }
    .security-alert .am-header {
      background: #FF4D6D;
      color: #fff;
    }
    .security-alert .am-content {
      padding: 0.8rem;
      color: #FF4D6D;
      font-weight: 600;
      line-height: 1.4;
    }
    
    .normal {
      background: var(--bg-surface);
    }
    .normal .am-header {
      background: rgba(0, 212, 255, 0.08);
      color: #00D4FF;
      border-bottom: 1px solid var(--border-color);
    }
    .am-steps {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .am-steps li {
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: flex-start;
      gap: 0.6rem;
    }
    .am-steps li:last-child {
      border-bottom: none;
    }
    .am-step-badge {
      background: var(--bg-surface-light);
      color: var(--text-muted);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-size: 0.65rem;
      font-weight: 700;
      text-transform: uppercase;
      white-space: nowrap;
      margin-top: 0.1rem;
    }
    .am-step-text {
      color: var(--text-secondary);
      line-height: 1.4;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AgentMessageComponent {
  @Input() set notes(val: string | null | undefined) {
    if (!val) {
      this.isSecurityAlert = false;
      this.parsedSteps = [];
      return;
    }
    this.isSecurityAlert = val.startsWith("Güvenlik İhlali") || val.startsWith("Sistem Güvenlik");
    if (this.isSecurityAlert) {
      this.securityReason = val.replace(/^(Güvenlik İhlali:\s*|Sistem Güvenlik Uyarısı:\s*)/, '');
      this.parsedSteps = [];
    } else {
      this.parsedSteps = val.split(' | ').filter(s => s.trim().length > 0);
    }
  }

  isSecurityAlert = false;
  securityReason = '';
  parsedSteps: string[] = [];

  getStepLabel(index: number): string {
    const labels = ['Karar', 'Eylem', 'Özet'];
    return labels[index] || 'Detay';
  }
}
