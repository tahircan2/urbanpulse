# UrbanPulse Backend (Spring Boot): Kapsamlı Başlangıç Rehberi

Merhaba! Frontend (Angular) cephesinde olan biteni ve Yapay Zeka (AI) servisimizin nasıl çalıştığını daha önce konuşmuştuk. Şimdi sıra geldi tüm bu sistemin kalbine inmeye.

**Backend (Arka Uç)**, tüm verilerin toplandığı, güvenliğin sağlandığı ve iş kurallarının (Business Logic) işletildiği büyük merkezdir. UrbanPulse projesinde backend'i dünyanın en popüler, en kurumsal ve en sağlam framework'ü olan **Java Spring Boot 3** ile yazdık.

Sistemi hiç bilmeyen birine anlatır gibi hazırladığım bu rehberde, bir ihbarın veritabanına nasıl yazıldığını, kapıdaki güvenlik görevlilerini (Security) ve projeyi oluşturan katmanları blok blok inceleyeceğiz.

Kahven hazırsa, sunucu odasına (Backend'e) giriyoruz!

---

## 1. Büyük Resim: Spring Boot Ne Yapar?

Diyelim ki bir vatandaş Angular (Frontend) üzerinden form doldurdu ve "Kaza var!" diyerek gönderdi. Frontend bu veriyi alıp bir mektuba (HTTP Request) koyar ve bizim sunucumuza (Örn: `http://localhost:8080/api/incidents`) yollar.

Spring Boot (Java) sunucusu tam bu adreste 7/24 uyanık bekleyen bir memurdur.

1. Mektubu alır.
2. Kapıdaki güvenlik kontrolünden geçirir ("Bu mektubu atan kişi sisteme üye mi?").
3. Mektuptaki bilgileri (Enlem, Boylam, Açıklama) Java objesine (Nesneye) çevirir.
4. Çekmecesini (MySQL Veritabanı) açar ve bunları bir tabloya düzenlice yazar.
5. AI Servisine (Python'a) telefon açar ("Yeni kaza var, al incele").
6. Frontend'e dönüp "Mektubun ulaştı, teşekkürler" (200 OK) cevabını atar.

İşte Spring Boot, tüm bu trafiği düzenleyen inanılmaz yetenekli bir orkestra şefidir.

---

## 2. Klasör Yapısı (Katmanlı Mimari)

`backend/src/main/java/com/urbanpulse` klasörüne girdiğinde karşına klasörler çıkacak. Spring Boot projelerinde kodlar tek bir dosyaya yazılmaz. **"Katmanlı Mimari" (Layered Architecture)** kullanılır. Her katmanın sadece tek bir görevi vardır.

Burayı bir restoran gibi düşünelim:

1. **`controller/` (Garsonlar):** Müşteriden (Frontend) siparişi alır, içeriye (Servise) iletir ve hazır olan yemeği müşteriye sunar.
2. **`service/` (Aşçılar):** Bütün işin (Logicin) döndüğü yerdir. Yemeği yapar, kuralları işletir.
3. **`repository/` (Kiler Sorumlusu):** Tek görevi veritabanı (MySQL) rafından domatesi (Veriyi) alıp aşçıya vermektir. Aşçı asla gidip raftan kendi bir şey almaz.
4. **`entity/` (Kalıplar/Kutular):** Veritabanımızdaki tabloların (Kullanıcılar, İhbarlar) Java sınıfı olarak karşılığıdır.
5. **`dto/` (Sefertası):** DTO (Data Transfer Object). Verileri Frontend'e gönderirken tüm veriyi yollamak yerine (örn: adamın şifresi de gitmesin diye) paketlediğimiz sefertasıdır.
6. **`security/` (Güvenlik Görevlisi):** Restoranın kapısında durur, giren çıkanın (JWT - Bilet) kontrolünü yapar.
7. **`config/`:** Restoranın açılış ayarlarıdır (Örn: WebSocket ayarları, şifreleme ayarları).

---

## 3. Spring Boot'un Sihri: Dependency Injection (Bağımlılık Enjeksiyonu)

Java kodlarını okurken sürekli sınıf adlarının tepesinde **`@RestController`**, **`@Service`**, **`@Autowired`**, **`@RequiredArgsConstructor`** gibi `@` (At / Annotation) işaretleri göreceksin. Bunlar nedir?

Java'da normalde bir sınıfı kullanmak için `new SinifAdi()` yazman gerekir. Binlerce istek gelen bir sunucuda sürekli `new` demek hafızayı (RAM) şişirir.
Spring Boot der ki: _"Sen uğraşma. Sen sınıfın tepesine `@Service` yaz, uygulamanın başında ben o sınıftan SADECE 1 TANE (Singleton) üretirim. Nerede ihtiyacın olursa oraya onu ben Enjekte Ederim (Inject)."_

İşte sınıfların (Garson, Aşçı, Kilerci) birbirini `new` anahtar kelimesi olmadan, otomatik olarak tanımasına ve kullanmasına **IoC (Inversion of Control)** ve **Dependency Injection** denir. Kodun çok temiz kalmasını sağlar.

---

## 4. Adım Adım Akış: Bir İhbar Nasıl Veritabanına Yazılır?

Gelin Kod Okuyalım. Bir kazanın sisteme geliş serüveni:

### Adım 1: Controller (Garson Siparişi Alır)

`IncidentController.java` dosyası, dışarıdan gelen istekleri dinler.
Üstünde `@PostMapping("/incidents")` yazar. Bu şu demektir: Kim dışarıdan bu adrese tıklarsa, buradaki kodu çalıştır.
Gelen veriyi (DTO) alır ve hiçbir iş yapmadan hemen arkadaki `IncidentService`'e (Aşçıya) paslar.

### Adım 2: Service (Aşçı Yemeği Yapar)

`IncidentService.java` projenin beynidir. Sınıfın üstünde `@Transactional` yazar. Bu çok kritiktir!

- **Transactional:** "Buradaki işlemleri yaparken elektrik kesilirse veya hata çıkarsa, veritabanına yazdığın yarım yamalak şeyleri geri al (Rollback), sistemi bozma!" demektir.

Servis, gelen veriyi alır, saati/tarihi ekler, başlangıç statüsünü `PENDING` (Bekliyor) yapar ve Kilerciye (`IncidentRepository`) gönderir.

### Adım 3: Repository (Kiler / Veritabanı İşlemleri)

`IncidentRepository.java` dosyasına girersen bomboş bir dosya (Interface) görürsün! Neden?
Çünkü biz **Spring Data JPA** kullanıyoruz. Eski usül `SELECT * FROM incidents WHERE id=5` gibi uzun SQL kodları yazmak artık tarih oldu.
Spring Boot'a sadece `interface IncidentRepository extends JpaRepository` deriz ve Spring arkada veritabanına ekleme, silme, güncelleme için gerekli binlerce satır SQL kodunu bizim yerimize kendisi saniyeler içinde anında oluşturur. Biz sadece `repository.save(kaza)` deriz ve MySQL'e kaydedilir.

### Adım 4: Yapay Zekayı Dürtmek (Eşzamanlı Olmayan / Async İşlem)

Kaza veritabanına kaydoldu, ama iş bitmedi. Yapay zekaya (Python) haber vermemiz lazım.
`IncidentService` hemen `AiPipelineService.triggerAiPipeline(kaza)` fonksiyonunu çağırır.
Burası **Asenkron** çalışır (tıpkı Python'da anlattığım gibi). Java durup Python'un cevabını beklemez! İsteği fırlatır ve anında Frontend'e dönüp cevabı yollar "Kaza Kaydedildi".

### Adım 5: Python İşi Bitirip Geri Döner (Callback)

Python (AI) dakikalarca düşünüp kararı verdiğinde, kendi başına inisiyatif alıp Spring Boot'un farklı bir kapısını tıklatır: `AgentCallbackController`.
Buradan giren sonuçlar;

1. Veritabanındaki eski Olayı (Incident) bulur ve durumunu günceller (Örn: Aciliyet P5 oldu).
2. Olan biteni yapay zekanın seyir defterine (`AgentLog`) kaydeder.
3. Son olarak, operatörlere canlı yayın yapar...

---

## 5. Canlı Yayın: WebSocket Mantığı (Haberci)

Eğer Python Java'ya sonucu ilettiyse, Belediye yetkilisinin Dashboard (Yönetici Paneli) açıkken ekranını F5 ile yenilemesine gerek kalmadan yeni kaza ekranına nasıl pat diye düşüyor?

İşte `websocket/IncidentWebSocketPublisher.java` burada devreye girer.
Spring Boot'taki WebSocket sistemi bir Radyo İstasyonuna benzer (Bizim projede bu radyo kanalının adı `/topic/incidents`'dir).
Java veritabanını güncellediği an, bu radyo frekansından anons geçer: _"Dikkat yeni veri var!"_
Aboneler (Yani o an sitesi açık olan Angular Frontend'ler) bu radyo kanalını canlı olarak dinledikleri için, veri anında ekranlarında belirir.

---

## 6. Güvenlik (Spring Security ve JWT)

`security/` klasöründeki kodlar sistemimizin kalesidir. Kapıdaki kod (`JwtAuthFilter.java`) her gelen mektubu açıp bakar.

- Gelen adamın mektubunda (Header) JWT yazan dijital bir bilet var mı?
- Bilet sahte mi?
- Biletin süresi dolmuş mu?

Eğer bu bilet doğruysa adamın kimliğini sisteme kaydeder (`SecurityContext`). Ancak daha da önemlisi, metodların tepesindeki **Authoriziation (Yetkilendirme)** ayarlarıdır.

Örneğin, `/dashboard` verilerini çeken metodun üstünde kontrol bulunur. Biletin olsa bile eğer rolün `CITIZEN` (Vatandaş) ise Java sana veriyi vermez, 403 Forbidden (Yasak) hatası fırlatır. Veriyi sadece `STAFF` veya `ADMIN` görebilir.

---

## Özetle

UrbanPulse Backend mimarisi, büyük kurumsal bankaların veya e-ticaret sitelerinin kullandığı profesyonel mimariyle birebir aynıdır:

1. **Katmanlıdır:** Herkes (Garson, Aşçı, Kilerci) kendi işini yapar, kod temiz kalır.
2. **Güvenlidir:** JWT ve Spring Security ile kapılar korunur.
3. **Zekidir:** AI servisimizle HTTP ve Webhook üzerinden, bekleme/kilitlenme yapmadan asenkron konuşur.
4. **Gerçek Zamanlıdır:** WebSocket ile ekranlar sayfa yenilenmeden güncellenir.

Projeyi incelerken `controller` klasöründen başlayarak bir isteğin izini `service` ve `repository`'e doğru sürersen, bu mimarinin ne kadar şiir gibi aktığını kendin de göreceksin!

Başarılar dilerim!

- Mentorun.
