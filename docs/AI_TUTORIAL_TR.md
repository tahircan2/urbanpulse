# UrbanPulse Yapay Zeka (AI) Servisi: Kapsamlı Başlangıç Rehberi

Merhaba! Bu belge, UrbanPulse projesindeki Yapay Zeka (AI) katmanının nasıl çalıştığını, sıfırdan başlayan birisine anlatır gibi, adım adım ve hiçbir detayı atlamadan anlatmak için hazırlanmıştır. Kendini bir stajyer veya öğrenci gibi düşün, ben de sana bu yenilikçi sistemin mimarisini çizen mentorun olarak her şeyi tane tane anlatacağım.

Bu projede sadece bir "ChatGPT'ye soru sor, cevap al" mantığı yok. Burada gerçek bir **"Agentic Workflow" (Ajan İş Akışı)** var. Yani yapay zeka kendi başına karar alıyor, internetten veri çekiyor, kendi içinde tartışıyor ve en son sisteme (Java Backend'e) kararı iletiyor.

Arkanı yasla, çayını veya kahveni al. Başlıyoruz!

---

## 1. Büyük Resim: AI Servisi Projede Nerede Duruyor?

Öncelikle projemizin mimarisine dışarıdan bir bakalım:

1. **Frontend (Angular):** Vatandaşların girip harita üzerinden "Şurada kaza oldu, burada su patladı" diye ihbar (Incident) oluşturdukları yer.
2. **Backend (Spring Boot / Java):** Bu ihbarları alıp veritabanına (MySQL) kaydeden ana sunucumuz.
3. **AI Service (Python / FastAPI):** İşte bizim beynimiz burası! Java, yeni bir ihbar geldiğinde Python'a "Al bu vakayı incele" der. Python düşünür, taşınır, verileri toplar ve Java'ya "Bu olaya X departmanı baksın, aciliyeti de Y'dir" diye döner.

Peki Python servisi kendi içinde nasıl çalışıyor? İşte burada devreye 4 temel kavram giriyor:

1. **Asenkron Programlama (Async/Await)**
2. **HTTP İstekleri (HTTP Requests & Webhooks)**
3. **LangGraph (Ajanların birbirine bağlanması)**
4. **Tool Calling (Ajanların dış dünya aletlerini kullanması)**

Şimdi bunları tek tek ve çok basitçe inceleyelim.

---

## 2. Asenkron Programlama (Async / Await) Nedir?

Python kodlarını açtığında hemen hemen her fonksiyonun başında `async def` ve içinde `await` göreceksin. Bu ne demek?

**Günlük hayattan bir örnek:**

- **Senkron (Normal) Çalışma:** Kafeye gittin, kasada kahve siparişi verdin. Kasiyer kahveyi hazırlamaya başladı. Arkanda 10 kişi sıra bekliyor ama kasiyer senin kahven bitene kadar diğerlerinin siparişini almıyor. Sonuç? Herkes sinirli, sistem yavaş.
- **Asenkron (Async) Çalışma:** Kasiyere siparişi verdin. Kasiyer (Python), kahve makinesinin (İnternet/API) düğmesine bastı ve ona "Kahve bitene kadar bekle (`await`)" dedi. Ancak Kasiyer kahve makinesinin başında kilitlenip kalmadı! Hemen arkadaki müşterinin siparişini almaya geçti. Kahve makinesi işi bitirdiğinde Kasiyer'e seslendi, Kasiyer de kahveyi sana teslim etti. Sonuç? Aynı anda onlarca sipariş işlendi, sistem uçuyor!

Python kodlarındaki `async def` şunu söyler: _"Bu fonksiyon uzun sürebilir, beklerken sistemi kilitleme."_
`await` ise şunu söyler: _"Ben burada OpenAI'den veya hava durumu sitesinden cevap bekliyorum. Cevap gelene kadar sen git başka kodları/ihbarları çalıştır."_

Bu sayede AI servisimiz aynı anda 100 tane kaza bildirimini çökmeden ve birbirini beklemeden aynı anda inceleyebilir.

---

## 3. LangGraph, Pipeline ve Ajanlar (Agents)

Projenin en sihirli kısmı `app/agents` klasörüdür. Burada **LangGraph** framework'ünü kullanıyoruz.

**LangGraph Nedir? Neden Düz Kod Yazmadık?**
Çünkü yapay zekaya kocaman bir görev verip "Al bunu yap" demek çok tehlikelidir; hata yapar (halüsinasyon görür). Bunun yerine işi **küçük uzmanlıklara** bölüyoruz. Tıpkı bir fabrikadaki üretim bandı (Pipeline) gibi. LangGraph, bu üretim bandını Python koduyla çizmemizi sağlar.

Üretim bandımız (Pipeline) `app/agents/pipeline.py` dosyasında şu şekilde tanımlı:
`Başlangıç -> Classifier -> Planner -> Monitor -> Bitiş`

Her bir ajan (Node), gelen veriyi bir çantanın (State) içinde alır. Kendi üzerine düşen görevi yapar, bulgularını çantaya ekler ve çantayı banttaki bir sonraki ajana gönderir.

### Ajan 1: Classifier (Sınıflandırıcı) - `classifier.py`

- **Görevi:** Gelen metni okumak ve "Bu ne olayı?" (Kategori) ile "Ne kadar acil?" (Öncelik 1'den 5'e) sorularına cevap bulmak.
- **Mantığı:** Prompt'unda (Sisteme verdiğimiz yapay zeka talimatı) çok katı bir kural vardır: _"Kullanıcıya körü körüne güvenme!"_ Örneğin kullanıcı olaya "Trafik Kazası" demiş ve önem derecesine "Az Önemli (P1)" demiş olabilir. Ama açıklamada "Araba yanıyor, içinde insan var!" yazıyorsa, Classifier ajanı derhal aciliyeti "Kritik (P5)" seviyesine çeker ve kategoriyi "Yangın (FIRE_HAZARD)" olarak ezer (Override eder).
- **Araç kullanımı:** Bu kararı verirken araçlara başvurur. Mesela sel riski olan bir yer mi? Hava yağmurlu mu? Bunları kontrol eder.

### Ajan 2: Planner (Planlayıcı) - `planner.py`

- **Görevi:** Classifier'ın karar kıldığı aciliyet ve kategori bilgisini okuyup, _"Bunu hangi Belediye Birimine sevk etmeliyim?"_ ve _"En geç kaç saatte çözülmeli (SLA)?"_ kararlarını vermek.
- **Mantığı:** Gürültü şikayetiyse çevre zabıtasına, sel ise İSKİ'ye, kazaysa Trafik'e yönlendirir. Ayrıca `patterns` (Örüntü) aracını kullanarak sorar: "Burada sürekli kaza mı oluyor?". Eğer çok kaza oluyorsa, olayın geçici değil sistemsel bir sorun olduğunu anlar ve not düşer. Ayrıca hafta sonları veya tatillerde ekiplerin yavaş çalışabileceğini hesaba katarak süreleri (SLA) esnetir.

### Ajan 3: Monitor (Gözetmen) - `monitor.py`

- **Görevi:** Sistemdeki tüm işlemler bittikten sonra olan biteni incelemek, yönetici için kısacık pürüzsüz bir özet (Summary) cümlesi çıkarmak ve iletişimi sağlamaktır.
- **Mantığı:** Süreci diller: "P5 yangın tespit edildi, İtfaiye atandı." Veya eğer gelen olay aylardır çözülmemiş eski bir olaysa "ESCALATE" (Acil Durum İlan Et) kararı alıp gerekli yerlere elektronik posta ve telefon bildirimi atılmasını emreder.

---

## 4. Araçlar (Tools) ve Tool-Calling Loop Mantığı

Bir yapay zeka modelinin (OpenAI GPT-4) dış dünyadan haberi yoktur. Geçen seneki bilgilerle eğitilmiştir ve şimdiki saati veya hava durumunu bilmez, internete giremez. Onlara göz, kulak ve el vermek için **Tools** (Araçlar) yazarız. `app/tools` klasörünün amacı tam olarak budur. Pense, tornavida gibi düşünebilirsin.

### Model Bu Araçları Nasıl Kullanır? (Loop Mantığı)

Ajanların (örn: `classifier.py`) içinde çok kritik bir "while / for" döngüsü (loop) vardır. Mantık şöyle işler:

1. **Python:** "Sayın OpenAI, elimde bir kaza var. Sana şu 5 tane aracı (Tool) seçme hakkı veriyorum. Kullanmak ister misin?" diyerek API'ye mesaj atar.
2. **OpenAI:** Gelen mesaja bakar ve metin (cevap) üretmek yerine Python'a şunu döner: _"Cevap vermek için henüz erken. Acilen `get_location_context` (Adres Bul) isimli aracın çalıştırılmasına ve bana sonucunun verilmesine karar verdim!"_
3. **Python (Döngü içi):** OpenAI'nin metin üretmediğini, bir araç çağırdığını (ToolCall) anlar. Derhal döngüye girer, OpenAI'ın istediği fonksiyonu kendi içinde (Python makinesinde) gerçek dünyada çalıştırır. (Örn: Nominatim sunucusuna bağlanır, adresi bulur, ilçeyi alır).
4. **Python:** Bulduğu ilçe sonucunu bir metne çevirir ve OpenAI'a tekrar yollar: _"Al bakalım istediğin aracın sonucu buydu."_
5. **OpenAI:** Yeni veriyi alır, okur ve _"Hımm güzel, peki bir de `get_weather` aracını çalıştır"_ diyebilir VEYA _"Tamam, tüm veriyi topladım, artık sana nihai kararı JSON olarak veriyorum"_ der.

İşte modelin araç seçmesi -> bizim çalıştırmamız -> ona geri vermemiz döngüsüne **Tool-Calling Loop** denir. Bu akıllı sistemin (Agentic AI) kalbidir!

### Araçlarımızın (Tools) Kod Yapıları ve Mantıkları:

- **`weather.py` (Hava Durumu):** İçinde httpx `Client` barındırır. Açık ve ücretsiz olan `Open-Meteo API` sunucusuna HTTP GET isteği (request) atar. Havadaki yağış miktarını okur, fırtına varsa AI'a "Önceliği 1 veya 2 puan artır!" tavsiyesi döner.
- **`infrastructure.py` (Altyapı Riskleri):** Belirtilen enlem ve boylamın 500 metre çapında Okul, Hastane veya Benzin İstasyonu var mı diye `Overpass API` (OpenStreetMap) sunucusuna sorgu atar. Varsa, kazanın bu yerleri etkileyebileceği ihtimaline karşı AI için çok kritik bir uyarı (auto_escalate=True) oluşturur.
- **`geocoding.py` (Adres Çözümleme):** Nominatim API'sine gider, koordinatı mahalle ve ilçe ismine çevirir. Kaza yerinin tam olarak nerede olduğunu AI'a metin olarak söyler.
- **`risk_profile.py` ve `time_context.py`:** Bu ikisi internete (dış API'ye) gitmez! Tamamen yerel, beynin içindeki mantıksal hesaplamalardır. Örneğin `time_context`, sadece sunucunun o anki saatine bakar: Akşam mı? Resmi tatil mi? Eğer gece yarısıysa ve şikayet gürültüyse; aciliyeti yükseltir. `risk_profile` ise içindeki statik veri dosyasından semtlerin özelliklerini (Kağıthane = Sel yatağı, Fatih = Eski binalar, vs.) AI'a anlatır.
- **`patterns.py` (Örüntü Bulucu):** Çok eşsiz bir araçtır. Dışarıdaki bir siteye değil, **bizim kendi asıl sistemimize (Spring Boot - Java)** HTTP isteği (GET) atar! "Şu ilçede, şu kategoride son 7 günde kaç olay yaşandı?" diye sorar. Eğer aynı mahallede sürekli su patlıyorsa, AI bunu algılar ve olayın sistemsel (kronik) bir kriz olduğuna karar verir.

---

## 5. Sistemlerin Haberleşmesi (HTTP Webhook & Callback Mantığı)

Gelelim en can alıcı noktaya: Spring Boot (Java) ile Python nasıl konuşuyor? Neden tek bir kod içinde değiller?

Yapay zeka işlemleri (özellikle LLM dedikleri OpenAI bekleme süreleri) çok zaman alır. 5-10 saniye sürebilir. Eğer Java bu kadar beklerse, sisteme giren diğer vatandaşlar siteyi donmuş gibi görür. Biz **Webhook (Kanca) / Callback (Geri Arama)** mimarisi kurduk.

**Adım Adım Haberleşme Serüveni:**

1. **Frontend:** Vatandaş "Gönder" butonuna basar.
2. **Spring Boot (Java):** İsteği alır. Hemen veritabanına PENDING (Bekliyor) olarak yazar ve vatandaşa "İhbarınız alındı" mesajını döndürüp işini bitirir. Vatandaş hiç beklemez!
3. **Spring Boot (Async Tetikleme):** Java arka planda sessizce Python sunucusuna (FastAPI'nin `/api/pipeline/process` ucuna) bir HTTP POST isteği atar. İçine de kazanın sadece id ve başlık bilgilerini koyar.
4. **Python AI (FastAPI):** Mesajı aldığı an saniyesinde Java'ya "200 OK - Aldım, sen işine bak" cevabı döner. Java yoluna devam eder.
5. **Python Pipeline'ı:** Python kendi kendine, Java'dan bağımsız biçimde asenkron olarak çalışmaya başlar. Önce Classifier çalışır, sonra Planner çalışır vb. AI tüm süreci inceler. (Burası 15 saniye sürse bile Java'yı hiç bağlamaz).
6. **Telefon ve E-Mail (Notifications):** Python işi bitirmeden hemen önce, `app/tools/notifications.py` üzerinden SendGrid'e kancayı takıp vatandaşa mail, yetkilinin cebine "Pushover" kütüphanesiyle bildirim atar.
7. **Büyük Final (Callback):** Python son kararlarını toparlar: "Bu olay trafik kazası, önceliği P1, İSKİ gitmeli, süre 2 saat!" şeklinde bir JSON oluşturur. Ve Python, asıl efendi olan Java'nın `/api/incidents/{id}/agent-result` adresine (Webhook/Callback Endpoint) HTTP POST ile asıl sonucu postalayıp işini bitirir.
8. **Spring Boot WebSocket ile Bitiş:** Java sonucu aldığı gibi veritabanındaki "PENDING" durumunu günceller ve tüm bağlı operatörlere WebSocket (Canlı bağlantı) aracılığıyla "Ekranınızı yenilemeyin, Aha da yeni kaza geldi!" sinyali basar.

İşte tam olarak bu yapıya Event-Driven Microservice (Olay Güdümlü Mikroservis) mimarisi diyoruz!

---

## 6. Özetle Zihninde Tutman Gerekenler

- **AI tamamen bağımsız bir karar otomasyonudur.** Sadece "bunu yap, sunu yaz" diye yardım eden bir chatbot değildir. Verileri analiz eder, departman atar ve kural koyar.
- **LangGraph** kodu spagettiden kurtarır. İşi Classifier, Planner ve Monitor adında 3 mühendise bölüştürmüş bir şirkettir.
- **Tools**, o 3 mühendisin ellerindeki akıllı telefonlardır. İstedikleri zaman internete veya veri tabanına bakmalarını sağlar.
- **Async & Callback Mimarisi**, sistemin saniyede binlerce isteği hiç kilitlenmeden, hiç çökmeden bir fabrika gibi yağ gibi akmasını sağlayan yegane sihrimizdir.

İşte projedeki şaheser bu mekanizmanın saat gibi tıkır tıkır çalışmasından ibarettir! Kodlarda dolaşırkan bu rehberi her zaman hatırla. Başarılar dilerim!
