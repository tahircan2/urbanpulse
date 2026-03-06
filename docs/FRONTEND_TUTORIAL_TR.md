# UrbanPulse Frontend (Angular): Kapsamlı Başlangıç Rehberi

Merhaba! Harika bir yapay zeka ve Java arka ucu kurduk, ama kullanıcıların bu sistemi görsel olarak kullanabileceği bir yüzü olmazsa bunların hiçbir anlamı kalmaz.

İşte **Frontend (Önyüz)** tam olarak budur. UrbanPulse projesinde Frontend katmanını **Angular** (versiyon 17/18) kullanarak tasarladık. Bu rehberde, bir siteye girdiğinde gördüğün butonların, haritaların ve tabloların arkasında nasıl bir mimari yattığını, hiçbir detay atlamadan, tane tane öğreneceksin.

Çayını kahveni al, modern web geliştirme dünyasına giriş yapıyoruz!

---

## 1. Büyük Resim: Angular Nedir ve Neden Kullanıyoruz?

Eskiden web siteleri (HTML/CSS) çok basitti. Sen bir butona basardın, tarayıcı (Chrome) sunucuya gider, yepyeni bir sayfa yüklerdi. Ekran beyazlar ve yavaşça geri gelirdi.

**Angular** gibi modern framework'ler (çatılar) ise **SPA (Single Page Application - Tek Sayfa Uygulaması)** mantığıyla çalışır.

- Siteye ilk girdiğinde tüm HTML/CSS/JS kodları tek bir seferde bilgisayarına (tarayıcıya) indirilir.
- Artık "Harita" sayfasına tıklarsan sayfa yenilenmez! Angular, ekranın sadece ortasındaki yazıları silip yerine haritayı çizer. Bu yüzden site bir internet sitesi gibi değil, sanki bilgisayarına indirdiğin bir uygulama (Excel, Spotify) gibi ışık hızında hissettirir.

Bizim projemizde Frontend (`frontend` klasörü), Java Backend'ine ve AI servisine **görsel bir vitrin** görevi görür.

---

## 2. Klasör Yapısı: Projede Neler Var?

`frontend/src/app` klasörüne girdiğinde karşına şu yapı çıkar. Bu bizim evimizin odalarıdır:

- **`/components`:** Sitedeki görsel sayfalar (Harita, Login, Dashboard, Raporlama vs.)
- **`/services`:** Arka planda Java ile konuşan işçilerimiz (API İstekleri, WebSocket).
- **`/models`:** Verilerimizin şablonları (Bir "Kaza" veya "Kullanıcı" verisi neye benzer?)
- **`/guards`:** Kapıdaki güvenlik görevlileri (Giriş yapmayanları dashboard'a almayan kodlar).
- **`/interceptors`:** Postacı (Her isteğin içine yolda JWT güvenlik kimliğini yapıştıran kod).
- **`app.routes.ts`:** Evin krokisi (Hangi adrese gidince hangi sayfa açılacak?).

---

## 3. Bileşenler (Components) Mantığı

Angular, **Lego blokları** gibidir. Bütün siteyi tek bir dosyaya yazmak yerine küçük parçalara (Lego) böleriz. Biz bunlara **Component (Bileşen)** diyoruz.

Her Component 3 dosyadan oluşur:

1. **`.ts` (TypeScript):** Kodun beyni. (Tıklanınca ne olacak? Veri nasıl çekilecek?)
2. **`.html`:** Kodun iskeleti. (Buton nerede duracak? Tablo nerede olacak?)
3. **`.scss` (CSS):** Kodun makyajı. (Buton kırmızı mı olsun, gölgesi mi olsun?)

### Projemizdeki Ana Legolar (Components):

1. **`navbar` (Üst Menü):** Her sayfada yukarıda sabit duran menü. Giriş yapanın adını veya "Çıkış Yap" butonunu gösterir.
2. **`home` (Ana Sayfa):** Sitenin vitrini. "UrbanPulse'a hoşgeldiniz" yazısı ve hızlı istatistikler.
3. **`map` (Harita):** `Leaflet` adlı açık kaynaklı bir kütüphane kullanırız. İstanbul haritasını ekrana çizer ve üzerine olayların pinlerini (ikonlarını) koyar.
4. **`report` (İhbar Sayfası):** Vatandaşların "Trafik kazası oldu!" diye form doldurduğu sayfa.
5. **`dashboard` (Yönetim Paneli):** Sadece belediye personeli (STAFF/ADMIN) görebilir. Gelen ihbarları, yapay zekanın (AI) atadığı öncelikleri tabloda gösterir. Yetkili kişi buradan onay verebilir veya silebili r.
6. **`auth` (Kayıt/Giriş):** Kullanıcıların sisteme üye olduğu (Login) sayfalar.

Tüm bu Legolar, `app.component.html` içindeki `<router-outlet>` adlı boş bir çerçevenin içine, kullanıcının girdiği URL'ye göre takılıp çıkarılır!

---

## 4. Servisler (Services) ve HTTP Haberleşme Mimarisi

Bileşenler (Components) çok aptaldır; veritabanına bağlanmayı bilmezler, sadece ekranda gösteri yaparlar. Arka plandaki Java (Spring Boot) sunucusu ile konuşma işini **Servislere (Services)** devrettik.

`frontend/src/app/services` klasöründe bu işçiler yaşar:

### A) `auth.service.ts` (Güvenlik ve Kimlik)

Kullanıcı giriş yaptığında Java sunucusuna kullanıcı adı ve şifresini yollar.
Java eğer şifreyi doğru bulursa, bize üzerinde damga/mühür olan bir bilet verir. Bu bilete **JWT (JSON Web Token)** diyoruz. `AuthService` bu bileti alır ve tarayıcının Gizli Kasasına (`localStorage`) saklar. Artık site yenilense bile giriş yapılmış halde kalırız.

### B) `incident.service.ts` (İhbar Dosyası Yöneticisi)

Bu bizim asıl işçimizdir. Bir vatandaş kaza bildirdiğinde (Report sayfasında), veriyi alır ve Java'ya HTTP POST isteği atar (`http://localhost:8080/api/incidents`).
Aynı şekilde, harita sayfası açıldığında "Bana İstanbul'daki tüm kazaları getir" diye Java'ya HTTP GET isteği atıp ekranı doldurur.

**_ÖNEMLİ ASENKRON DETAY (Observables):_**
Python'daki `async / await` yapısının Angular'daki karşılığı **RxJS Observables**'dır.
Frontend Java'dan veriyi isterken Java'nın yanıt vermesi internet hızına bağlı olarak 1-2 saniye sürebilir. Tarayıcı donmasın diye Angular'da veriye `.subscribe()` (Abone ol) deriz. Yani _"Sen veriyi iste, ben donmayıp diğer tuşlara basmaya devam edeyim. Cevap geldiğinde bana haber ver"_ demiş oluruz.

### C) `websocket.service.ts` (Canlı Yayın - Gerçek Zamanlılık)

Eski tip sitelerde, yeni bir ihbar geldiğini görmek için sayfayı sürekli F5 (Yenile) yapmak zorundaydın.
**WebSocket**, sunucu ile senin bilgisayarın (tarayıcı) arasına çekilmiş **canlı bir telefon hattıdır.**
Bir vatandaş rapor formunu gönderip Java'ya yolladığında, Java tüm açık olan Dashboard ekranlarına bu telefon hattından "Hey! Yeni veri geldi!" diye bir sinyal fırlatır. `websocket.service.ts` bu sinyali duyar ve ekranı hiç sayfa yenilemeden (sessizce) yeni verilerle doldurur. Sistem sanki canlı bir WhatsApp sohbeti gibi ışık hızında çalışır.

---

## 5. Güvenlik Mekanizmaları (Guards & Interceptors)

Sistemimizde kimse elini kolunu sallayarak Belediyenin Yönetim Paneline (Dashboard) girememeli. Bunu iki bekçiyle sağlıyoruz:

### 1) AuthGuard (`guards`) - "Kapıdaki Bodyguard"

Bir ziyaretçi tarayıcı çubuğuna zorla `localhost:4200/dashboard` yazarsa, Angular ayağa kalkıp kapıdaki Bodyguard'a (AuthGuard) sorar: _"Bu adamın cebinde bilet (JWT) var mı?"_. Eğer yoksa adamı anında `Login` sayfasına geri tekmeler.

### 2) Interceptor (`interceptors`) - "Postacı"

Biletin (JWT) olsa bile, Java'dan gizli bir veri isterken (örn: tüm kaza detayları) bu bileti zarfın içine koyman gerekir. Her API isteğinde kodu kopyala-yapıştır yapıp bileti eklemek çok pis bir yöntemdir.
**Interceptor**, tüm giden HTTP isteklerini (mektupları) havada yakalar, gizlice cebindeki JWT biletini (Token) mektuba iliştirir ve yola öyle devam ettirir. Java arka uç bu sayede senin kim olduğunu anlar.

---

## 6. Özetleyecek Olursak Tüm İşleyiş (Akış):

Ahmet (Vatandaş) yolda bir mermer kırıntısı görür ve bunun tehlikeli olduğunu düşünür:

1. Ahmet tarayıcıdan siteye girer (`home` componenti açılır).
2. "İhbar Et" butonuna basar (`app.routes` sayfayı `report` componentine değiştirir).
3. Ahmet formu doldurur, haritada yeri tıklar ve Gönder der.
4. `report.component.ts` veriyi alır ve `incident.service.ts`'ye verir.
5. Servis Java'ya (Backend) bir `HTTP POST` fırlatır ve Ahmet'e ekranda (Teşekkürler, işlem alındı) uyarısı çıkartır.
6. Ahmet'in işi bitmiştir. Arka planda Java ve Python (Yapay Zeka) kendi aralarında çalışıp kararı verir.
7. Java karar bittiğinde `WebSocket` üzerinden bir radyo frekansı yayınlar.
8. Masasında oturan Belediye Memuru Ayşe Hanımın açık olan `dashboard` sayfası (`websocket.service.ts` sayesinde) bu frekansı alır yakalar ve Ayşe Hanım parmağını bile oynatmadan ekrana Ahmet'in ihbarı "P5 Aciliyet - İtfaiye Gönderilmeli" şeklinde kırmızı renkli otomatik olarak düşer!

**İşte UrbanPulse Frontend mimarisi böyle kusursuz bir uyum ve canlılıkla çalışmaktadır!** Angular'ın gücü, bileşen mantığı ve servislerin ayrılığı sayesinde kodumuz hem çok temiz (Clean Code) hem de gelecekte büyütülmeye (Örn: Mobil uygulama yapmaya) tamamen hazırdır.

Sıralı okumak istersen, kodlarını incelemeye `app.routes.ts` (yol haritası) ve `dashboard/dashboard.component.ts` üzerinden başlayabilirsin.

Başarılar!

- Mentorun.
