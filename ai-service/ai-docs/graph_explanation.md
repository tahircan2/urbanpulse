# UrbanPulse AI Service: `graph.py` Dosya Analizi ve Eğitim Rehberi

Bu döküman, LangGraph pipeline'ının "beyni ve sinir sistemi" olan `graph.py` dosyasını her yönüyle öğretmek amacıyla hazırlanmıştır.

---

## 1. Giriş: `graph.py` Dosyasının Görevi Nedir?

Bu dosya, `runner.py`'daki orkestra şefinin yöneteceği "orkestra üyelerini" (düğümleri) bir araya getirir ve hangi müzisyenden sonra hangisinin çalacağını (kenarları/edges) belirler. 

**Basitçe:** Bir akış diyagramı çizer ve bu diyagramı çalıştırılabilir bir yazılıma dönüştürür.

---

## 2. Satır Satır Analiz

### 2.1. Yardımcı Fonksiyonlar

#### LLM Hazırlığı (`_get_llm`)
```python
def _get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.langgraph_model,
        temperature=0,
        max_tokens=256,
    )
```
*   **`temperature=0`**: Yapay zekanın "yaratıcı" değil, "tutarlı ve mantıklı" olmasını sağlar. Aynı girdi için her seferinde aynı çıktıyı almak isteriz.
*   **`max_tokens=256`**: Cevapların kısa ve öz (JSON formatında) kalmasını zorunlu kılar.

#### JSON Ayıklayıcı (`_parse_json`)
*   Yapay zeka bazen sadece JSON döndürmek yerine başına sonuna metin ekleyebilir (örneğin: "İşte cevabım: { ... }"). 
*   Bu fonksiyon, metin içindeki `{` ve `}` karakterlerini bularak gerçek veriyi cımbızla çeker.

---

### 2.2. Güvenlik Düğümleri (Guardrails)

#### Giriş Güvenliği (`input_guard_node`)
```python
def input_guard_node(state: PipelineState) -> dict:
```
*   **Görevi**: Kullanıcının gönderdiği ihbarı inceler. 
*   **Kontrol Ettikleri**: "Prompt Injection" (yapay zekayı kandırma girişimleri), aşırı küfür veya kötü niyetli komutlar.
*   **Çıktı**: `input_safe` değişkenini True veya False yapar.

#### Çıkış Güvenliği (`output_guard_node`)
*   **Görevi**: Yapay zekanın ürettiği kararları (kategori, plan, özet) son bir kez kontrol eder. 
*   **Önemli**: Eğer AI yanlışlıkla hassas bir veri sızdırırsa veya uygunsuz bir cevap üretirse, bu düğüm bunu yakalar ve `output_safe=False` yaparak çıktıyı gizler.

---

### 2.3. Karar Mekanizması (Routing)
```python
def route_after_guard(state: PipelineState) -> str:
    return "classify" if state.get("input_safe", True) else "rejected"
```
*   Burası bir yol ayrımıdır. Eğer giriş güvenliyse "classify" (sınıflandırma) durağına git, değilse "rejected" (reddedildi) durağına git der.

---

### 2.4. Grafik Kurulumu (Graph Assembly)

Burası dökümandaki en heyecan verici kısımdır. Diyagram burada çizilir:

```python
graph = StateGraph(PipelineState)
```
*   `StateGraph` objesini oluşturur ve ona "Senin hafızan `PipelineState` şablonuna göredir" der.

#### Düğümlerin Eklenmesi (Nodes)
```python
graph.add_node("input_guard",  input_guard_node)
graph.add_node("classify",     classify_node)
...
```
*   Hangi istasyonların olacağını tanımlar.

#### Bağlantıların Yapılması (Edges)
```python
graph.set_entry_point("input_guard") # Akış buradan başlar
```
*   **Koşullu Bağlantı**: `add_conditional_edges` kullanılarak `input_guard`'dan sonra nereye gidileceği bir fonksiyona (`route_after_guard`) danışılır.
*   **Düz Bağlantı**: `add_edge("classify", "plan")` satırı, sınıflandırma biter bitmez otomatik olarak planlamaya geçilmesini sağlar.
*   **Bitiş**: `END` ise akışın tamamlandığını belirtir.

---

### 2.5. Derleme (Compilation)
```python
compiled_graph = graph.compile()
```
*   Hazırladığımız bu tasarımı "çalıştırılabilir" bir makineye dönüştürür. `runner.py` dosyasında çağırdığımız o meşhur `compiled_graph` işte tam olarak budur.

---

## 3. Akış Şeması Özeti

Görsel olarak akış şöyledir:

1.  **Başlangıç** -> `input_guard` (Güvenlik Kontrolü)
2.  **Yol Ayrımı**:
    *   *Güvenli mi?* Evet -> `classify` -> `plan` -> `monitor` -> `output_guard` -> **BİTİŞ**
    *   *Güvenli mi?* Hayır -> `rejected` -> **BİTİŞ**

---

## 4. Neden LangGraph Kullanıyoruz?

*   **Esneklik**: Herhangi bir aşamada (düğümde) hata olursa veya süreci değiştirmek isterseniz sadece o düğümü güncellemeniz yeterlidir.
*   **Takip Edilebilirlik**: Her düğümün girdisini ve çıktısını ayrı ayrı izleyebilirsiniz.
*   **Güvenlik**: Akışın her adımında (girişte ve çıkışta) bağımsız kontrol noktaları oluşturmamıza olanak sağlar.

---
**Sıradaki Adım**: Pipeline'ın iskeletini de bitirdik! Artık bu düğümlerin içindeki gerçek "zeka" ve "mantık" kısımlarına yani `nodes/` klasöründeki dosyalara geçebiliriz. Hazır olduğunda söyle, ilk olarak `classify_node.py` ile başlayalım!
