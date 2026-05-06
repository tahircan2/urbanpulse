# UrbanPulse LangGraph Pipeline - Sistem İşleyişi (System Process)

Bu doküman, UrbanPulse AI Service altyapısına yeni bir ihbar (incident) geldiğinde sistemin adım adım nasıl çalıştığını, hangi dosyaların hangi sırayla tetiklendiğini ve verinin nasıl işlendiğini detaylandırmaktadır.

## 1. Verinin Karşılanması ve Hazırlık
- **`api/endpoints.py` (veya `main.py`):** Spring Boot (backend) üzerinden gelen REST API isteği ilk olarak burada karşılanır. Gelen JSON verisi bir `IncidentDTO` nesnesine çevrilir.
- **`runner.py` (`run_langgraph_pipeline`):** LangGraph grafiğinin ana tetikleyicisidir. Bu dosya, gelen ihbarı LangGraph'ın okuyabileceği `PipelineState` (durum sözlüğü) formatına sokar. State içerisine varsayılan boş alanlar (`reasoning`, `action_note`, vb.) eklenir ve ardından grafik `compiled_graph.invoke(state)` metodu ile başlatılır.

## 2. LangGraph Akışı (`graph.py` üzerinden)

Grafik başlatıldığında veri şu düğümlerden (node) sırasıyla geçer:

### Adım 1: Girdi Güvenliği (Input Guard)
- **Dosya:** `nodes/guards.py` -> `input_guard_node`
- Sistem, öncelikle kullanıcının girdiği metinleri (Başlık ve Açıklama) güvenlik kontrolünden geçirir. Sisteme zarar vermeyi amaçlayan "Prompt Injection" (istem enjeksiyonu) veya kasıtlı manipülasyonları tespit eder. *(Not: Kanlı, ölümlü kaza gibi trajik olaylar güvenlik ihlali sayılmaz ve geçişine izin verilir).*
- **Çıktı:** Duruma (state) `input_safe: True/False` değerini yazar.

### Adım 2: Yönlendirme (Routing)
- **Dosya:** `nodes/guards.py` -> `route_after_guard`
- Güvenlik sonucuna bakar. Eğer `input_safe` False ise akışı doğrudan `rejected_node`'a yönlendirerek iptal eder. True ise `classify_node`'a yönlendirir.

### Adım 3: Sınıflandırma Ajanı (Classifier)
- **Dosya:** `nodes/classifier.py` -> `classify_node`
- Görevi olayın türünü (Category) ve önceliğini (Priority) belirlemektir.
- LLM, bu işlemi yaparken `tools.py` içerisindeki harici araçları (hava durumu, ilçe risk durumu, zaman analizi) çağırır.
- Tüm veriyi analiz ettikten sonra kararını verir.
- **Çıktı:** State üzerine `category`, `priority` ve İngilizce, anlaşılır bir gerekçe (`reasoning`) ekler.

### Adım 4: Planlama Ajanı (Planner)
- **Dosya:** `nodes/planner.py` -> `plan_node`
- Classifier ajanı tarafından verilmiş olan kararı (`reasoning`) okuyarak olayı devralır.
- Görevi bu ihbara hangi departmanın (`department`) bakacağını ve ne kadar süre içinde (SLA: `sla_hours`) müdahale edilmesi gerektiğini hesaplamaktır.
- Gerekirse sistemdeki benzer ihbarları (similar_incidents_tool) kontrol ederek olayın sistemik bir kriz mi yoksa tekil bir olay mı olduğunu tespit eder.
- **Çıktı:** State üzerine `department`, `sla_hours` değerlerini yazar. Ayrıca ilgili departmanın sahada tam olarak ne yapması gerektiğini açıklayan somut bir İngilizce eylem planı (`action_note`) ekler.

### Adım 5: Gözetmen Ajan (Monitor)
- **Dosya:** `nodes/monitor.py` -> `monitor_node`
- Classifier ve Planner'ın aldığı tüm kararları, mantığı ve aksiyonları inceler.
- Görevi tüm bu karmaşık AI iş akışını, yöneticilerin (veya harita arayüzündeki kullanıcıların) anlayabileceği "Kullanıcı Dostu" tek bir cümlelik İngilizce özet (`summary`) haline getirmektir.
- **Çıktı:** State üzerine `summary` değerini yazar.

### Adım 6: Çıktı Güvenliği (Output Guard)
- **Dosya:** `nodes/guards.py` -> `output_guard_node`
- Tüm ajanlar işini bitirdikten sonra, üretilen 3 ana metin (`reasoning`, `action_note`, `summary`) " | " sembolü ile birleştirilir.
- Birleştirilen bu metin, `urbanpulse/guardrails/output_guard.py` dosyasına gönderilir. Bu guard, yapay zekanın halüsinasyon görüp görmediğini, iç sisteme ait (prompt leaks) sırları metne döküp dökmediğini kontrol eder.
- **Çıktı:** Eğer her şey normalse, metni aynen bırakır (`output_safe: True`). Tehlikeli bir durum varsa metni gizler ve uyarı yazısı koyar.

## 3. Sonuçların Döndürülmesi ve Loglama
- LangGraph çalışmasını tamamladıktan sonra final durumu (Final State), kendisini çağıran **`runner.py`** dosyasına geri döner.
- `runner.py`, bu ham sözlük (dict) yapısındaki final verilerini okur.
- Geriye bir `PipelineResult` Pydantic modeli oluşturur.
- Ayrıca bu modelin içerisine, Frontend'de (Dashboard) ajanların ne düşündüğünü şeffafça gösterebilmek adına her ajan için (Classifier, Planner, Monitor) `AgentLog` satırları oluşturur.
- İşlenen son JSON yapısı Backend sistemine aktarılır, veri tabanına yazılır ve oradan da Angular Frontend'ine WebSocket veya REST ile iletilerek Harita (Map) üzerinde canlı olarak görüntülenir.
