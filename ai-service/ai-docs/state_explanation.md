# UrbanPulse AI Service: `state.py` Dosya Analizi ve Eğitim Rehberi

Bu döküman, LangGraph pipeline'ının "ortak hafızası" olan `state.py` dosyasını her yönüyle öğretmek amacıyla hazırlanmıştır.

---

## 1. Giriş: "State" (Durum) Nedir?

LangGraph ile bir AI pipeline'ı kurduğunuzda, bu pipeline bir dizi "düğümden" (node) oluşur. Veri bir düğümden diğerine geçerken, bu verileri taşıyan merkezi bir objeye ihtiyaç vardır. İşte `PipelineState` bu merkezi objedir.

**Benzetme:** Bir fabrikada montaj hattı hayal edin. Bir bant üzerinde bir kutu ilerliyor. Her istasyon (düğüm) kutuyu açar, içine bir parça ekler veya bir şeyi kontrol eder, sonra kutuyu bantta bir sonraki istasyona gönderir. `state.py` bu "kutunun" içinde neler olabileceğini (şablonunu) tanımlar.

---

## 2. Satır Satır Analiz

### 2.1. İçe Aktarmalar (Imports)
```python
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
```
*   **`TypedDict`**: Python'da normal bir sözlüğün (`dict`) hangi anahtarlara ve ne tipte değerlere sahip olacağını zorunlu kılan bir yapıdır. Hata yapmamızı engeller.
*   **`Annotated`**: Bir tipe ekstra metadata (bilgi) eklememizi sağlar. Burada LangGraph'a "bu alanı nasıl güncelleyeceğini" söylemek için kullanıyoruz.
*   **`Sequence`**: Bir listenin veya sıralı bir yapının (liste, tuple vb.) genel adıdır.
*   **`operator.add`**: İki şeyi toplamak/birleştirmek için kullanılan standart Python fonksiyonudur.
*   **`BaseMessage`**: LangChain'in mesaj yapısıdır (Kullanıcı mesajı, AI cevabı, Sistem mesajı vb.).

---

### 2.2. `PipelineState` Sınıfı
Bu sınıf, pipeline boyunca taşınacak tüm kutucukları (değişkenleri) tanımlar.

#### A. Giriş Verileri (Input)
```python
incident: dict                    # Ham ihbar verisi
consistency_warning: str          # Dağıtıcı/Doğrulayıcı uyarısı
```
*   **`incident`**: Dışarıdan gelen verinin bir kopyasıdır. Tüm düğümler bu veriye bakarak karar verir.
*   **`consistency_warning`**: `runner.py`'da yapılan tutarlılık kontrolünün sonucunu tutar.

#### B. Güvenlik Filtreleri (Guardrails)
```python
input_safe: bool   # Girdi güvenli mi?
input_reason: str  # Reddedildiyse nedeni
```
*   Bu alanlar `input_guard` düğümü tarafından doldurulur. Eğer `input_safe` False ise, süreci durdururuz.

#### C. Sınıflandırma Çıktıları (Classifier)
```python
category: str        # Algılanan kategori
priority: int       # Aciliyet seviyesi
confidence: float   # Yapay zekanın kendine olan güveni (0.0 - 1.0)
reasoning: str      # AI'nın neden bu kararı verdiği
override_reason: str # Eğer manuel bir müdahale gerekirse nedeni
```

#### D. Planlama Çıktıları (Planner)
```python
department: str    # Yönlendirilen belediye birimi
sla_hours: int     # Müdahale edilmesi gereken süre (saat)
action_note: str   # Birime iletilecek özel not
```

#### E. İzleme ve Özet (Monitor)
```python
summary: str       # İhbarın kısa, profesyonel özeti
```

#### F. Çıkış Güvenliği ve Meta Veriler
```python
output_safe: bool  # AI'nın cevabı güvenli mi?
agent_notes: str   # Son kullanıcıya veya operatöre notlar
elapsed_ms: int    # TOPLAM çalışma süresi
success: bool      # İşlem başarılı mı?
error: str         # Hata varsa mesajı
```

---

### 2.3. En Kritik Satır: Mesaj Biriktirme
```python
messages: Annotated[Sequence[BaseMessage], operator.add]
```
Bu satır, yeni başlayanlar için en karmaşık ama en önemli kısımdır.

*   **Nedir?**: Pipeline içinde düğümler LLM (Büyük Dil Modeli) ile konuşurken aralarında bir "sohbet geçmişi" oluşur.
*   **Neden `Annotated` ve `operator.add`?**:
    *   Normalde bir sözlükte aynı anahtara (`messages`) yeni bir değer atarsanız, eskisi silinir.
    *   Ancak burada LangGraph'a şu talimatı veriyoruz: **"Yeni bir mesaj geldiğinde eskini silme, `operator.add` (toplama) yaparak listenin sonuna ekle."**
    *   Böylece tüm düğümler bir önceki düğümün ne konuştuğunu görebilir.

---

## 3. Akış Mantığı (Veri Nasıl Taşınır?)

1.  **Düğüm 1 (Klasifikasyon)**: `state` objesini alır. İçindeki `incident` verisine bakar. Kendi kararını (`category`, `priority`) `state`'e yazar ve objeyi geri döndürür.
2.  **Düğüm 2 (Planlama)**: Güncellenmiş `state` objesini alır. Artık içinde hem `incident` hem de `category` vardır. Bu bilgilere bakarak `department` belirler ve `state`'e ekler.
3.  **Döngü Sonu**: Son düğüm işini bitirdiğinde, başlangıçta boş olan veya sadece `incident` içeren `state` objesi, artık tüm AI sonuçlarıyla dolmuş olur.

---

## 4. Neden Ayrı Bir Dosya?

*   **Tip Güvenliği**: Hangi düğümün hangi veriyi üreteceği bellidir. "Yanlışlıkla `priority` yerine `oncelik` yazdım" hatasını yapmamızı engeller.
*   **Merkezi Yönetim**: Sisteme yeni bir özellik (örneğin: `lokasyon_doğruluğu`) eklemek isterseniz, sadece bu dosyaya bir satır eklersiniz ve tüm pipeline bu yeni alanı tanır.

---
**Sıradaki Adım**: `state.py` dosyasını kavradıysan, şimdi pipeline'ın iskeleti olan `graph.py` dosyasına geçebiliriz. Hazır olduğunda bana bildir!
