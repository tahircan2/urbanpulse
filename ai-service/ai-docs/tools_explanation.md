# UrbanPulse AI Service: `tools.py` Dosya Analizi ve Eğitim Rehberi

Bu döküman, yapay zekanın "beş duyusu" ve "dış dünyaya açılan kapıları" olan `tools.py` dosyasını her detayıyla öğretmek amacıyla hazırlanmıştır.

---

## 1. Giriş: "Tool" (Araç) Nedir?

Yapay zeka modelleri (LLM), eğitim verileriyle sınırlıdır. Yani bugünün hava durumunu, o anki saati veya veritabanınızdaki diğer ihbarları bilemezler. **Tools (Araçlar)**, yapay zekaya bu güncel bilgilere erişme yeteneği sağlayan fonksiyonlardır.

**Benzetme:** Bir doktora (AI) muayene oluyorsunuz. Doktor bilgili biri ama kan tahlili (Tool) sonuçlarını görmeden kesin bir teşhis koyamaz. `tools.py` doktorun kan tahlili istemesini sağlayan ekipmanlardır.

---

## 2. Satır Satır Analiz

### 2.1. İçe Aktarmalar ve `@tool` Dekoratörü
```python
import json
from langchain_core.tools import tool
```
*   **`@tool`**: Bu bir "dekoratör"dür. Altındaki normal Python fonksiyonunu, LangChain ve LangGraph'ın anlayabileceği özel bir nesneye dönüştürür. Yapay zeka bu sayede "Ben şu an şu aracı kullanmalıyım" diyebilir.

---

### 2.2. Araçların İncelenmesi

#### A. Hava Durumu Aracı (`weather_context_tool`)
```python
@tool
def weather_context_tool(latitude: float, longitude: float) -> str:
    """...Docstring (Yapay zekanın ne zaman kullanacağını anlaması için açıklama)..."""
    from urbanpulse.tools.weather import get_weather_context
    return json.dumps(get_weather_context(latitude, longitude))
```
*   **Ne Yapar?**: Koordinatları alır ve anlık hava durumunu (yağış, rüzgar vb.) getirir.
*   **Neden Önemli?**: Yoğun yağmur varsa bir trafik kazasının veya su baskınının öncelik seviyesi (Priority) AI tarafından artırılır.

#### B. Bölge Risk Aracı (`district_risk_tool`)
*   **Ne Yapar?**: Antalya'daki ilçelerin risk profilini getirir. Örneğin: "Bu bölge bir sanayi bölgesi mi? Kimyasal tehlike var mı?"
*   **Neden Önemli?**: AI, ihbarın geldiği yerin riskli bir bölge olduğunu bilirse daha dikkatli bir planlama yapar.

#### C. Zaman Bağlamı Aracı (`time_context_tool`)
*   **Ne Yapar?**: O anki saatin trafik yoğunluğu (rush hour), okul saati veya resmi tatil olup olmadığını söyler.
*   **Neden Önemli?**: Gece saat 03:00'te olan bir gürültü şikayeti ile öğlen 14:00'te olanın aciliyeti farklıdır.

#### D. Kritik Altyapı Aracı (`infrastructure_tool`)
*   **Ne Yapar?**: İhbarın yakınında (örneğin 500 metre içinde) hastane, okul veya itfaiye istasyonu olup olmadığını bulur.
*   **Neden Önemli?**: Bir yangın ihbarı okulun yanındaysa bu en yüksek önceliğe sahiptir.

#### E. Coğrafi Doğrulama Aracı (`geolocation_tool`)
*   **Ne Yapar?**: Koordinatları adrese (mahalle/sokak) çevirir. 
*   **Neden Önemli?**: Kullanıcı "Muratpaşa'dayım" deyip koordinatları "Konyaaltı" gösteriyorsa AI bu çelişkiyi bu araçla yakalar.

#### F. Benzer İhbar Analizi (`similar_incidents_tool`)
*   **Ne Yapar?**: Son 7 gün içinde aynı bölgede benzer bir ihbar gelip gelmediğine bakar.
*   **Neden Önemli?**: Aynı sokakta 5 kişi "su kesintisi" bildirmişse, bu bireysel bir sorun değil, bir ana boru patlaması olabilir (Sistemsel Sorun).

---

## 3. Kod Yazım Mantığı: Neden `json.dumps`?

Fark ettiysen tüm araçlar `return json.dumps(...)` ile bitiyor.
*   **Neden?**: Yapay zekaya karmaşık Python objeleri göndermek yerine, onun çok daha iyi anladığı ve parse edebildiği temiz bir metin (JSON) gönderiyoruz. Bu, AI'nın veriyi doğru yorumlama şansını artırır.

---

## 4. Araç Listesi (`LANGGRAPH_TOOLS`)
```python
LANGGRAPH_TOOLS = [
    weather_context_tool,
    district_risk_tool,
    ...
]
```
*   Bu liste, `graph.py` veya düğümlere (nodes) toplu halde araçları tanıtmak için kullanılır. "Elimizdeki tüm yetenekler bunlardır" demektir.

---

## 5. Özet: Akış Nasıl Oluyor?

1.  **AI Karar Verir**: "Bu bir yangın ihbarı, çevre bilgisine ihtiyacım var."
2.  **Araç Çağrılır**: `infrastructure_tool` çalışır.
3.  **Veri Gelir**: "Yakında bir huzurevi var" bilgisi JSON olarak döner.
4.  **AI Kararını Günceller**: "Öncelik Seviyesi: 1 (Kritik). Nedeni: Yakında huzurevi bulunması."

---
**Sıradaki Adım**: Araçları da öğrendik! Artık bu araçları kullanan asıl karar vericilere, yani **Düğümlere (Nodes)** geçiyoruz. Hazır olduğunda söyle, ilk işçimiz olan **`classifier.py`** (Sınıflandırıcı) ile devam edelim!
