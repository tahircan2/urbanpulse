import { ChangeDetectionStrategy, Component, signal, inject, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  IncidentSubmission, IncidentCategory, IncidentPriority,
  CATEGORY_LABELS, PRIORITY_LABELS,
} from '../../models/incident.model';
import { IncidentService } from '../../services/incident.service';
import { AuthService } from '../../services/auth.service';

/** OSM Nominatim reverse-geocoding response shape (subset we need) */
interface NominatimResponse {
  address: {
    municipality?:  string;
    city_district?: string;
    suburb?:        string;
    quarter?:       string;
    county?:        string;
    town?:          string;
    city?:          string;
    road?:          string;
    pedestrian?:    string;
    footway?:       string;
    residential?:   string;
    neighbourhood?: string;
    hamlet?:        string;
    village?:       string;
  };
  display_name: string;
}

/** Parsed address data from Nominatim, ready to fill the form */
export interface ResolvedAddress {
  district:      string | null;
  neighbourhood: string | null;
  street:        string | null;
  displayLabel:  string;   // e.g. "Muratpaşa • Kaleiçi • Cumhuriyet Cad."
}

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
  private readonly cdr = inject(ChangeDetectorRef);
  readonly auth = inject(AuthService);

  readonly categories = Object.entries(CATEGORY_LABELS) as [IncidentCategory, string][];

  /** Antalya Büyükşehir Belediyesi ilçeleri */
  readonly districts = [
    'Muratpaşa', 'Kepez', 'Konyaaltı', 'Alanya', 'Manavgat',
    'Serik', 'Döşemealtı', 'Aksu', 'Kemer', 'Kumluca', 'Kaş', 'Finike', 'Demre',
  ];

  /** Antalya ilçe merkezi koordinatları */
  readonly districtCoords: Record<string, [number, number]> = {
    'Muratpaşa': [36.8841, 30.7056],
    'Kepez':     [37.0017, 30.7133],
    'Konyaaltı': [36.8713, 30.6390],
    'Alanya':    [36.5445, 32.0037],
    'Manavgat':  [36.7862, 31.4340],
    'Serik':     [36.9164, 31.1002],
    'Döşemealtı':[37.0781, 30.5678],
    'Aksu':      [36.9100, 30.8780],
    'Kemer':     [36.5989, 30.5591],
    'Kumluca':   [36.3701, 30.2841],
    'Kaş':       [36.2009, 29.6414],
    'Finike':    [36.2952, 30.1531],
    'Demre':     [36.2455, 29.9831],
  };

  readonly PRIORITY_LABELS = PRIORITY_LABELS;

  form: IncidentSubmission = this.defaultForm();

  readonly submitting  = signal(false);
  readonly submitted   = signal(false);
  readonly submittedId = signal<number | null>(null);
  readonly submittedLat = signal<number>(0);
  readonly submittedLng = signal<number>(0);
  readonly error       = signal('');

  // ── GPS Geolocation states ─────────────────────────────────────────────────

  /** Konum alınıyor spinner */
  readonly geoLocating = signal(false);

  /**
   * GPS kilidi aktif — kullanıcı ilçe/mahalle/cadde'yi manuel değiştiremez.
   * "Konumu Temizle" butonuna basılana kadar kilitli kalır.
   */
  readonly geoLocked  = signal(false);
  readonly geoError   = signal('');

  /** Çözümlenen adres — form doldurulduktan sonra UI chip olarak gösterilir */
  readonly resolvedAddress = signal<ResolvedAddress | null>(null);

  // ── Submit ─────────────────────────────────────────────────────────────────

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
          this.submittedLat.set(res.data.latitude);
          this.submittedLng.set(res.data.longitude);
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
    this.geoLocked.set(false);
    this.geoError.set('');
    this.resolvedAddress.set(null);
    this.form = this.defaultForm();
  }

  /** Kullanıcı GPS kilitliyken ilçeyi seçemez. Kilit kapalıysa koordinatları günceller. */
  onDistrictChange(district: string): void {
    if (this.geoLocked()) return;   // kilitlendiyse yok say
    const coords = this.districtCoords[district];
    if (coords) {
      const latOffset = (Math.random() - 0.5) * 0.015;
      const lngOffset = (Math.random() - 0.5) * 0.015;
      this.form.latitude  = coords[0] + latOffset;
      this.form.longitude = coords[1] + lngOffset;
    }
    this.form.neighbourhood = undefined;
    this.form.street = undefined;
    this.resolvedAddress.set(null);
    this.geoError.set('');
  }

  /** GPS kilidini kaldır — kullanıcı yeniden manuel seçim yapabilir */
  clearLocation(): void {
    this.geoLocked.set(false);
    this.geoError.set('');
    this.resolvedAddress.set(null);
    this.form.neighbourhood = undefined;
    this.form.street = undefined;
    const coords = this.districtCoords[this.form.district];
    if (coords) {
      this.form.latitude  = coords[0];
      this.form.longitude = coords[1];
    }
  }

  // ── GPS + Reverse Geocoding ────────────────────────────────────────────────

  detectMyLocation(): void {
    if (!navigator.geolocation) {
      this.geoError.set('Tarayıcınız konum özelliğini desteklemiyor.');
      return;
    }

    this.geoLocating.set(true);
    this.geoLocked.set(false);
    this.geoError.set('');
    this.resolvedAddress.set(null);

    navigator.geolocation.getCurrentPosition(
      position => this.onGeoSuccess(position),
      error     => this.onGeoError(error),
      { enableHighAccuracy: true, timeout: 12_000, maximumAge: 30_000 },
    );
  }

  private onGeoSuccess(position: GeolocationPosition): void {
    const { latitude, longitude } = position.coords;

    // Koordinatları hemen kaydet
    this.form.latitude  = latitude;
    this.form.longitude = longitude;

    const url =
      `https://nominatim.openstreetmap.org/reverse` +
      `?lat=${latitude}&lon=${longitude}&format=json&accept-language=tr&zoom=18`;

    fetch(url, {
      headers: { 'User-Agent': 'UrbanPulse/3.0 (antalya-smart-city)' },
    })
      .then(r => r.json() as Promise<NominatimResponse>)
      .then(data => {
        const resolved = this.parseNominatimAddress(data);

        // Adres alanlarını formun yeni bir kopyasıyla değiştirerek OnPush'u tetikle
        this.form = {
          ...this.form,
          district: resolved.district || this.form.district,
          neighbourhood: resolved.neighbourhood ?? undefined,
          street: resolved.street ?? undefined
        };

        this.resolvedAddress.set(resolved);
        this.geoLocked.set(true);   // ilçe seçimini kilitle
        this.geoLocating.set(false);
        this.geoError.set('');
        
        // Asenkron fetch dönüşünde View'ın güncellenmesini garantiye al
        this.cdr.markForCheck();
      })
      .catch(() => {
        // Geocoding başarısız — koordinatlar kaydedildi, adres yok
        this.geoLocked.set(true);
        this.geoLocating.set(false);
        this.geoError.set('Adres çözümlenemedi ama koordinatlar kaydedildi.');
        this.resolvedAddress.set({
          district:      this.form.district,
          neighbourhood: null,
          street:        null,
          displayLabel:  `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`,
        });
        this.cdr.markForCheck();
      });
  }

  private onGeoError(error: GeolocationPositionError): void {
    this.geoLocating.set(false);
    this.geoLocked.set(false);

    switch (error.code) {
      case error.PERMISSION_DENIED:
        this.geoError.set('Konum izni reddedildi. Tarayıcı ayarlarından izin verin.');
        break;
      case error.POSITION_UNAVAILABLE:
        this.geoError.set('Konumunuz alınamadı. Lütfen GPSʼin açık olduğunu kontrol edin.');
        break;
      case error.TIMEOUT:
        this.geoError.set('Konum alma zaman aşımına uğradı. Tekrar deneyin.');
        break;
      default:
        this.geoError.set('Konum alınırken bir hata oluştu.');
    }
  }

  /**
   * Nominatim yanıtını parse ederek ilçe, mahalle ve caddeyi döndürür.
   * Birden fazla aday alan denenir; Antalya ilçe listesiyle fuzzy-match yapılır.
   */
  private parseNominatimAddress(data: NominatimResponse): ResolvedAddress {
    const addr = data.address;

    // Aday bölgeler - önce en olası "ilçe" karşılıkları
    const potentialDistricts = [
      addr.town, addr.county, addr.city_district, addr.municipality, addr.city, addr.suburb
    ];

    let district: string | null = null;
    let fallbackRaw: string = '';

    for (const raw of potentialDistricts) {
      if (!raw) continue;
      const match = this.matchAntalyaDistrict(raw);
      if (match) {
        district = match;
        fallbackRaw = raw;
        break;
      }
    }

    if (!district) {
      fallbackRaw = addr.city_district ?? addr.town ?? addr.county ?? addr.suburb ?? '';
    }

    // Mahalle (Eğer suburb ilçe olarak eşleşmediyse mahalledir)
    let neighbourhood = addr.neighbourhood ?? addr.hamlet ?? addr.village ?? null;
    if (!neighbourhood && addr.suburb && addr.suburb !== fallbackRaw) {
      neighbourhood = addr.suburb;
    }
    if (!neighbourhood && addr.quarter && addr.quarter !== fallbackRaw) {
      neighbourhood = addr.quarter;
    }

    // Cadde / sokak
    const street =
      addr.road ?? addr.pedestrian ?? addr.footway ?? addr.residential ?? null;

    // Display label (ilçe • mahalle • cadde formatında)
    const parts = [
      district ?? fallbackRaw,
      neighbourhood,
      street,
    ].filter(Boolean);
    const displayLabel = parts.length > 0 ? parts.join(' • ') : data.display_name;

    return { district, neighbourhood, street, displayLabel };
  }

  /**
   * Ham ilçe stringini Antalya ilçe listesiyle eşleştir.
   * Tam eşleşme → fuzzy contains → null
   */
  private matchAntalyaDistrict(raw: string): string | null {
    if (!raw) return null;
    const rawLower = raw.toLocaleLowerCase('tr-TR').trim();

    const exact = this.districts.find(d => d.toLocaleLowerCase('tr-TR') === rawLower);
    if (exact) return exact;

    const fuzzy = this.districts.find(
      d => d.toLocaleLowerCase('tr-TR').includes(rawLower) || rawLower.includes(d.toLocaleLowerCase('tr-TR')),
    );
    return fuzzy ?? null;
  }

  // ── Priority helpers ───────────────────────────────────────────────────────

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
      latitude:    36.8969,   // Antalya merkez
      longitude:   30.7133,
      district:    'Muratpaşa',
      neighbourhood: undefined,
      street:        undefined,
    };
  }
}
