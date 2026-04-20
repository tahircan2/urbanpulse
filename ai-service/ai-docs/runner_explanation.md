# UrbanPulse AI Service: `runner.py` Dosya Analizi ve Eğitim Rehberi

Bu döküman, `ai-service` içerisindeki LangGraph pipeline'ının "orkestra şefi" olan `runner.py` dosyasını satır satır ve mantıksal bloklar halinde öğretmek amacıyla hazırlanmıştır.

---

## 1. Giriş: `runner.py` Nedir?

Bu dosya, dış dünyadan (FastAPI) gelen bir "olay" (Incident) verisini alır, onu LangGraph'ın anlayacağı bir dile çevirir, yapay zeka sürecini başlatır ve işlem bittiğinde sonuçları tekrar düzenleyip geri gönderir. 

**Basitçe:** Veriyi paketler, işlenmesi için fabrikaya (Graph) gönderir ve gelen bitmiş ürünü etiketleyip müşteriye (API) sunar.

---

## 2. Satır Satır Analiz

### 2.1. İçe Aktarmalar (Imports)
```python
from __future__ import annotations
import asyncio
import time
```
*   **`from __future__ import annotations`**: Python'ın eski versiyonlarında tip ipuçlarını (Type Hints) daha esnek kullanmamızı sağlar.
*   **`import asyncio`**: Python'ın asenkron (eşzamanlı olmayan) işlemlerini yönetmek için kullanılır. Pipeline'ımız "beklemeli" (I/O bound) işlemler yaptığı için bu şarttır.
*   **`import time`**: İşlemin ne kadar sürdüğünü (milisaniye cinsinden) ölçmek için kullanılır.

```python
from urbanpulse.core.logging import get_logger
from urbanpulse.models import (...)
from urbanpulse.services.validator import check_content_consistency
from urbanpulse.langgraph_pipeline.graph import compiled_graph
from urbanpulse.langgraph_pipeline.state import PipelineState
```
*   **`get_logger`**: Sistemdeki olayları (hata, başarı, başlangıç) takip etmemizi sağlayan günlükleme sistemidir.
*   **`urbanpulse.models`**: Veri yapılarını (IncidentDTO, PipelineResult vb.) tanımlayan sınıflardır. Kodun tip güvenliğini sağlar.
*   **`check_content_consistency`**: Verilen ihbar içeriğinin mantıklı olup olmadığını kontrol eden bir yardımcı fonksiyondur.
*   **`compiled_graph`**: `graph.py`'da tanımlanan ve "derlenen" (çalışmaya hazır hale getirilen) AI düğümleridir.
*   **`PipelineState`**: Graph içinde dolaşacak olan "durum" (state) yapısının şablonudur.

---

### 2.2. Logger Tanımlama
```python
logger = get_logger(__name__)
```
*   Dosya bazlı bir logger nesnesi oluşturur. Bu sayede loglarda hangi dosyanın mesaj yazdığını görebiliriz.

---

### 2.3. `run_langgraph_pipeline` Fonksiyonu
Bu fonksiyon, tüm sürecin kalbidir.

```python
async def run_langgraph_pipeline(incident: IncidentDTO) -> PipelineResult:
```
*   **Girdi (`incident`)**: Kullanıcının gönderdiği ihbar verisidir.
*   **Çıktı (`PipelineResult`)**: AI sürecinden sonra oluşan nihai sonuçtur.
*   **`async`**: Bu fonksiyonun ağ üzerinden bir şeyler bekleyebileceğini (LLM çağrısı gibi) belirtir.

#### Başlangıç Hazırlıkları
```python
log = logger.bind(incident_id=incident.id)
log.info("langgraph_pipeline_start", title=incident.title)
t0 = int(time.monotonic() * 1000)
```
*   **`logger.bind`**: Bu işlem boyunca atılacak her logun yanına otomatik olarak `incident_id` bilgisini ekler. Takip kolaylığı sağlar.
*   **`t0`**: İşlem başladığı anki zamanı milisaniye olarak kaydeder.

#### İçerik Tutarlılık Kontrolü
```python
consistency = check_content_consistency(incident)
warning = consistency["warning"] if not consistency["consistent"] else ""
```
*   İhbarın içinde çelişkili veya eksik bilgi olup olmadığını kontrol eder. Eğer bir sorun varsa bunu bir "uyarı" (warning) olarak sisteme ekler.

---

### 2.4. Durum (State) Oluşturma
Burası en kritik kısımlardan biridir. LangGraph, düğümler arasında veri taşımak için bir "State" (Durum) objesi kullanır.

```python
state: PipelineState = {
    "incident":             incident.model_dump(), # Veriyi ham Python sözlüğüne çevirir
    "consistency_warning":  warning,              # Yukarıdaki uyarıyı ekler
    "input_safe":           True,                 # Varsayılan olarak güvenli kabul eder
    "input_reason":         "",
    "category":             incident.category.value, # Mevcut kategoriyi alır
    "priority":             incident.priority,       # Mevcut önceliği alır
    ...
    "messages":             [],                   # LLM mesaj geçmişi (şimdilik boş)
}
```
*   **Neden böyle yazıldı?**: AI modellerinin (Düğümlerin) her birine hangi verilerin gitmesi gerektiğini ve hangi verilerin onlardan geri alınacağını önceden tanımlıyoruz.

---

### 2.5. Graph'ın Çalıştırılması
```python
try:
    final_state = await asyncio.to_thread(compiled_graph.invoke, state)
    elapsed_ms = int(time.monotonic() * 1000) - t0
```
*   **`asyncio.to_thread`**: LangGraph'ın `invoke` metodu bazen senkron (synchronous) çalışabilir. Ana asenkron akışı (loop) kitlememek için onu ayrı bir "iş parçacığında" (thread) çalıştırıp sonucunu bekliyoruz.
*   **`compiled_graph.invoke`**: Fabrikayı çalıştırır! Veriyi düğümlerden geçirir (Klasifikasyon, Planlama, İzleme düğümleri).
*   **`elapsed_ms`**: İşlem bittiğinde toplam ne kadar sürdüğünü hesaplar.

---

### 2.6. Sonuçların Değerlendirilmesi

#### Reddedilme (Rejection) Durumu
```python
if not final_state.get("success", False) and "error" in final_state:
    return PipelineResult(
        ...
        assigned_department=final_state.get("department", "System Rejected"),
        success=False,
        error=final_state.get("error"),
    )
```
*   Eğer AI (örneğin güvenlik filtresi) bu ihbarı tehlikeli veya geçersiz bulup reddettiyse, süreci burada keser ve "Başarısız" sonucu döner.

#### Verilerin Ayrıştırılması (Parsing)
```python
try:
    category = IncidentCategory(final_state["category"])
except:
    category = incident.category # Hata olursa eski kategoriyi koru
```
*   AI'dan gelen kategori metnini (`str`), bizim sistemimizdeki resmi `IncidentCategory` tipine çevirmeye çalışır. Bu sayede veritabanına düzgün kaydedilir.

---

### 2.7. Agent Loglarının Oluşturulması
Dashboard ekranında gördüğünüz "Classifier şunu yaptı", "Planner buraya yönlendirdi" gibi detaylı bilgiler burada oluşturulur.

```python
logs = [
    AgentLogCreate(
        agent_name=AgentName.CLASSIFIER,
        action=AgentAction.CLASSIFY,
        output_summary=f"→ {category.value} P{priority}",
        ...
    ),
    # ... Diğer agentlar: PLANNER ve MONITOR ...
]
```
*   **Önemli**: LangGraph tüm işlemi tek bir "pipeline" olarak yaptığı halde, kullanıcı dostu olması için sonucu 3 farklı ajan yapıyormuş gibi loglara bölüyoruz.

---

### 2.8. Final Çıktı (PipelineResult)
```python
return PipelineResult(
    incident_id=incident.id,
    classified_category=category,
    classified_priority=priority,
    assigned_department=final_state.get("department", "General Services"),
    sla_hours=final_state.get("sla_hours", 24),
    agent_logs=logs,
    success=True,
)
```
*   Bu obje, bu dosyanın dış dünyaya cevabıdır. API bu cevabı alır ve kullanıcının ekranına yansıtır.

---

### 2.9. Hata Yönetimi (Exception Handling)
```python
except Exception as exc:
    log.error("langgraph_pipeline_error", error=str(exc))
    return PipelineResult(...)
```
*   Eğer kodun herhangi bir yerinde (LLM bağlantısı kesilirse, JSON hatası olursa vb.) beklenmedik bir hata çıkarsa, program çökmez. Bunun yerine hatayı loglar ve kullanıcıya "Pipeline hatası" mesajıyla güvenli bir şekilde döner.

---

## 3. Özet Akış Şeması

1.  **Başla**: FastAPI `run_langgraph_pipeline` fonksiyonunu çağırır.
2.  **Kontrol**: İhbar verisi temizlenir ve doğrulanır.
3.  **State Hazırla**: Pipeline'ın kullanacağı tüm değişkenler bir sözlüğe (State) konur.
4.  **Graph Invoke**: LangGraph bu state'i alır; onu sırasıyla Güvenlik, Sınıflandırma, Planlama ve İzleme duraklarına uğratır.
5.  **State Güncelle**: Her durak (node) state üzerindeki bilgileri günceller.
6.  **Logla**: Biten işlemden her ajan için ayrı bir "günlük" (log) çıkarılır.
7.  **Bitir**: Sonuç `PipelineResult` olarak API'ya teslim edilir.

---
**Sıradaki Adım**: Hazır olduğunda bana söyle, `state.py` dosyasını da aynı bu şekilde, her detayıyla inceleyelim!
