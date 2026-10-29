# UrbanPulse: LangGraph Pipeline Yapısı ve Çalışma Mantığı

Merhaba! Geliştirdiğimiz projede (UrbanPulse) yer alan **LangGraph Pipeline** yapısının nasıl çalıştığını, hiç bilmeyen birine anlatır gibi adım adım açıklayacağım. Bu belge, hocanın verdiği görevleri (Amacını anlamak ve sınıfta anlatabilmek) tam olarak yerine getirebilmen için hazırlandı.

---

## 1. LangGraph Nedir? Neden Kullanıyoruz?

En basit haliyle **LangGraph**, yapay zeka ajanlarının (LLM) bir dizi adımı (node/düğüm) izleyerek iş yaptığı bir "iş akışı" (workflow) oluşturma aracıdır. 
Eski yapıda (CrewAI) "Sen, sen ve sen sırayla çalışın" diyorduk ancak kontrol bizde değildi. LangGraph ile ise **bir akış şeması (graf)** çiziyoruz:
* "Önce Güvenlik Kontrolü yap."
* "Eğer güvenliyse Sınıflandırıcıya git, değilse Reddet."
* "Sonra Planlamacıya git..."

Bu yapı, state (durum) adı verilen ortak bir hafızayı adım adım birbirlerine aktarmalarını sağlar.

---

## 2. Klasör ve Dosya Yapısı

Projedeki `src/urbanpulse/langgraph_pipeline/` klasörüne baktığımızda şöyle bir yapı görüyoruz:

* `state.py` : Hafıza (Veri Şeması)
* `graph.py` : İş akışının (Akış Şemasının) çizildiği yer
* `runner.py` : Dış dünyadan gelen isteği LangGraph'a veren ve başlatan tetikleyici
* `tools.py` : Yapay zekanın kullanabileceği ekstra araçlar (Alet çantası)
* `nodes/` : Akış şemasındaki her bir kutucuk (Görevli/Ajan)

Şimdi bu dosyaların tam olarak ne yaptıklarına "Bir olay geldiğinde ne oluyor?" senaryosuyla bakalım.

---

## 3. Sistem Nasıl İşliyor? (Adım Adım Kod Referanslarıyla)

Frontend'den veya uygulamadan yeni bir şikayet/olay (örneğin: *"Antalya Muratpaşa'da yolda dev bir çukur var"*) geldiğini düşünelim. 

### Adım 1: Başlangıç ve Hafıza (`runner.py` ve `state.py`)
İlk olarak istek `runner.py` içindeki `run_langgraph_pipeline(incident)` fonksiyonuna gelir. 
Burada bir **Başlangıç Durumu (State)** oluşturulur.

**`state.py` dosyasına bakalım:**
```python
class PipelineState(TypedDict):
    """LangGraph pipeline boyunca akan tipli durum (state)."""
    incident: dict                    # Ham olay verisi
    category: str                     # Sınıflandırıcı çıktısı
    priority: int
    department: str                   # Planlamacı çıktısı
    sla_hours: int
    ...
```
`state.py`, adeta boş bir form kağıdıdır. Olay ilk geldiğinde bu formun sadece "incident" (olay detayı) kısmı doludur. Bu kağıt, ajanlar (düğümler) arasında elden ele dolaşacak ve her ajan kağıttaki kendi ilgili yerini dolduracaktır.

### Adım 2: Akışın Çizilmesi (`graph.py`)
LangGraph'ın asıl büyüsü `graph.py` içindedir. Sayfanın en altına doğru şu kodları görürüz:

```python
graph = StateGraph(PipelineState) # Boş bir grafik (iş akışı) oluştur

# 1. Düğümleri (Ajanları) ekle
graph.add_node("input_guard",  input_guard_node)
graph.add_node("classify",     classify_node)
graph.add_node("plan",         plan_node)
graph.add_node("monitor",      monitor_node)
graph.add_node("output_guard", output_guard_node)
graph.add_node("rejected",     rejected_node)

# 2. Yolları (Edge'leri) çiz
graph.set_entry_point("input_guard") # İlk giriş kapısı
graph.add_conditional_edges("input_guard", route_after_guard, {
    "classify": "classify",
    "rejected": "rejected",
})
graph.add_edge("classify", "plan") # Sınıflandırıcıdan sonra Planlamacıya geç
graph.add_edge("plan", "monitor")  # Planlamacıdan Monitor'e vs...
```
Bu kod resmen bir akış şeması çizer. Başlangıç noktası `input_guard` olarak belirlenmiştir.

### Adım 3: Düğümlerin (Nodes) Çalışması
Klasör içindeki `nodes/` klasöründe her işi yapan ajanlar bulunur.

1. **`input_guard_node` (Güvenlik Kapısı):** Gelen metinde yapay zekayı kandırmaya yönelik kötü niyetli bir şey (Prompt Injection) var mı diye kontrol eder. Güvenliyse yola "classify" ajanından, değilse "rejected" (reddedildi) ajanından devam edilir. (Buna Conditional Edge - Koşullu Yönlendirme denir).

2. **`nodes/classifier.py` (Sınıflandırıcı):** 
Güvenlikten geçen form Sınıflandırıcıya gelir. 
```python
sys_msg = "You are an expert Incident Classifier. Output JSON at the end..."
```
Sınıflandırıcı, olayın ne tür bir olay olduğunu (Örn: `ROAD_DAMAGE`), aciliyet seviyesini (Örn: Priority 4) belirler ve bu bilgileri "form kağıdına" (state) yazar.

3. **`nodes/planner.py` (Planlamacı):**
Form Planlamacıya gelir. Planlamacı şikayetin KATEGORİSİNE bakar ve hangi departmana yönlendirileceğini (`department` : "Fen İşleri") ve ne kadar sürede çözülmesi gerektiğini (`sla_hours` : 48) form kağıdına ekler.

4. **`nodes/monitor.py` (İletişim/Monitör):**
Tüm işler bittikten sonra Monitör ajanı gelir ve tüm bu yapılan işleri tek bir resmi cümlede özetler: 
*"İlgili olay incelenmiş ve çözüm için ilgili birime yönlendirilmiştir."* 

5. **`output_guard_node` (Çıktı Güvenliği):**
Son çıkış kapısı. Üretilen tüm yanıtların güvenli ve kullanıcıya gösterilebilir olduğundan emin olur.

### Adım 4: Veritabanına Yazma (`runner.py`)
Tüm bu işlemler bitip Graf (İş akışı) sonlandığında, içi dolu form kağıdı (Final State) tekrar `runner.py` dosyasına teslim edilir. 
`runner.py` içindeki şu blok, formdaki bilgileri okuyup sistemin kendi veritabanı log nesnesine (`AgentLogCreate`) ve veritabanına dönüştürür.
```python
logs = [
    AgentLogCreate(
        agent_name=AgentName.CLASSIFIER,
        output_summary=f"→ {category.value} P{priority}",
        #...
    ),
   # ...
]
```

---

## 4. Araçların (Tools) Kullanımı

Sistemde `tools.py` adında bir dosya var. Sınıflandırıcı yapay zekası olayın aciliyetini tahmin ederken sadece metne bakmayabilir. 
Örneğin, olayda koordinat var. `tools.py` içindeki:
* `weather_context_tool` (Hava durumunu öğrenir)
* `district_risk_tool` (Bölgenin risk analizini çeker)

gibi fonksiyonları kullanarak olayı daha iyi anlayabilir ve kararlarını daha isabetli verebilir.

---

## 5. LangSmith Nasıl Kullanıldı?

**LangSmith**, LangChain ve LangGraph projelerinde çalışan yapay zekanın "O an ne düşündü, hangi aracı çalıştırdı, ne kadar süre geçti, API'ye ne yolladı?" gibi verilerini adım adım takip etmemizi sağlayan bir **Observability (Gözlemlenebilirlik)** katmanıdır.

Bizim projemizde LangSmith kullanımı **"Implicit" (Örtülü) entegrasyon** ile sağlanmaktadır.
LangGraph oluştururken doğrudan LangChain öğeleri (`ChatOpenAI`, `StateGraph`) kullandığımız için, LangSmith özel bir koda ihtiyaç duymaz. Sistemdeki `.env` veya ortam değişkenlerinde şu ayarların bulunması yeterlidir:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="<senin-api-anahtarin>"
LANGCHAIN_PROJECT="urbanpulse-ai"
```
Bu sayede Python uygulaması çalıştığında, LangGraph arka planda her düğüm (node) geçişini, yapay zekaya gönderilen Prompt'u ve alınan cevabı otomatik olarak internetteki LangSmith Cloud paneline gönderir ve kayıt altına alır. Herhangi ekstra bir kod modülü kullanmadan projenin izlenebilirliği (tracing) sağlanmış olur.

---

## 6. Gelişmiş Teknik Detaylar (Hoca Sorarsa Diye)

Sınıfta "Neden böyle yaptınız?" denirse şu teknik kararları savunabilirsin:

### A. Stateless vs Stateful Tasarım
Şu anki graf yapımız her istekte sıfırdan başlar (**Stateless**). Ancak LangGraph'ın asıl gücü `checkpointer` ekleyerek konuşma geçmişini (hafızayı) veritabanında saklayabilmesidir. Şu anki ihtiyaç tek seferlik rapor analiz olduğu için sistemi hafif (lightweight) tuttuk.

### B. Neden `asyncio.to_thread`? (`runner.py`)
LangGraph'ın `invoke` fonksiyonu genellikle senkron çalışır. FastAPI asenkron (async) bir yapıdadır. Ana iş parçacığını (main thread) yapay zeka işlemleriyle dondurmamak için LangGraph'ı ayrı bir thread'de güvenli bir şekilde çalıştırıyoruz:
```python
final_state = await asyncio.to_thread(compiled_graph.invoke, state)
```

### C. JSON Parsing Sağlamlığı (`graph.py`)
Yapay zekanın her zaman mükemmel JSON döndüreceğinin garantisi yoktur. Bu yüzden `_parse_json` fonksiyonunda hem markdown temizliği yapıyoruz hem de regex benzeri bir mantıkla (`find("{")`) içeriği ayıklıyoruz. Bu, sistemin "çökmesini" engeller.

---

## 7. Sınıf Tartışması İçin İpuçları (Implementation Details)

**Soru:** "Neden CrewAI yerine LangGraph?"
**Cevap:** "CrewAI daha çok ajanların kendi aralarında otonom tartışması üzerine kurulu bir yapı. LangGraph ise kontrolün tamamen yazılımcıda olduğu, adımların kesin çizgilerle belirlendiği bir yapı. Şehir yönetimi gibi hata payı düşük sistemlerde LangGraph kontrol edilebilirliği artırıyor."

**Soru:** "Sistem güvenliğini nasıl sağlıyorsunuz?"
**Cevap:** "Pipeline'ın hem girişinde (`input_guard`) hem çıkışında (`output_guard`) LLM tabanlı güvenlik filtreleri (Guardrails) var. Bu, 'Double-Layer Security' sağlıyor."

**Soru:** "Performans nasıl?"
**Cevap:** "Her node (düğüm) kendi işlemini yapar ve bir sonrakine veriyi aktarır. `runner.py` içinde `time.monotonic()` ile tüm süreci milisaniye bazında ölçüp logluyoruz."

---

Bu döküman ile LangGraph sisteminin hem mimarisini hem de uygulama detaylarını eksiksiz bir şekilde hocana sunabilirsin. Başarılar!
