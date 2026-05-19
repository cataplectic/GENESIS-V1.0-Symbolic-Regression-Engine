# GENESIS: Ham Veriden Fizik Yasası Keşfeden Yapay Zeka

*Yayın tarihi: Mayıs 2026*

---

## Başlangıç

Ohm Yasası'nı bulmak Newton'a 20 yıl almadı — ama Georg Ohm'un 1827'de bulgusunu
raporlaması yine de yıllarca süren dikkatli deneylerin ürünüydü.

GENESIS bu süreci tersine çeviriyor: ham ölçüm verisi ver, formülü otomatik bulsun.
**Ohm Yasası'nı 0.65 saniyede, Kepler'in 3. Yasası'nı 18 saniyede keşfediyor.**

---

## Nasıl Çalışıyor?

Klasik makine öğrenmesi yaklaşımı şu soruyu sorar: *"Veriye hangi parametreler uyar?"*
GENESIS daha zor bir soruyu sorar: *"Veriye hangi **formül** uyar?"*

Bu fark devasa. Parametrik bir model (`y = ax² + bx + c`) sabit bir yapıya
katsayı uydurur. GENESIS ise formülün yapısını da, katsayıları da sıfırdan keşfeder.

### Genetik Programlama

Darwin'in evrimi denklemler için nasıl çalışır?

1. **Popülasyon**: Binlerce rastgele matematiksel ifade oluştur (`mul(X0, X1)`, `add(sqrt(X0), X1)`, ...)
2. **Fitness**: Her ifadeyi veriye göre değerlendir — MSE (ortalama kare hata)
3. **Seçilim**: Daha iyi ifadeler hayatta kalır
4. **Çaprazlama**: İki ifadenin alt-ağaçlarını birleştir
5. **Mutasyon**: Rastgele değişiklikler — hoist mutasyonu karmaşık ağaçları kısaltır
6. **Tekrarla**: 40-50 nesil sonra en iyi formül ortaya çıkar

Occam'ın usturası için `parsimony_coefficient=0.003` — karmaşık formüller
doğruluk kazançlarıyla orantılı şekilde cezalandırılır.

### 3 Aşamalı Post-Processing Pipeline

gplearn formülü bulduğunda iş bitmez. Üç aşamalık bir temizleme uyguluyoruz:

```
1. fold_constants()      → Saf-sabit alt-ağaçları sayıya indir
   "mul(2.1, sub(3.0, 1.5))" → "mul(2.1, 1.5)" → "3.15"

2. scipy Nelder-Mead     → Sayısal sabitleri MSE minimizasyonuyla hassas ayarla
   "mul(4.87, mul(t, t))" → "mul(4.905, mul(t, t))"

3. sympy simplify        → Cebirsel sadeleştirme
   "mul(I, sqrt(mul(R, R)))" → "I*R"
```

Sonuç: `mul(I, sqrt(mul(R, R)))` gibi karmaşık bir gplearn çıktısı,
`I*R` gibi okunabilir bir fizik formülüne dönüşüyor.

---

## Benchmark Sonuçları

30 benchmark üzerinde test ettik. Seçilmiş sonuçlar:

| Fizik Yasası | Gerçek Formül | GENESIS Çıktısı | R² |
|---|---|---|---|
| Ohm Yasası | `V = I·R` | `I*R` | 1.000 |
| Dalga Hızı | `v = f·λ` | `f*λ` | 1.000 |
| Hooke Yasası | `F = k·x` | `k*x` | 1.000 |
| Momentum | `p = m·v` | `m*v` | 1.000 |
| Seri Direnç | `R = R1+R2+R3` | `R1+R2+R3` | 1.000 |
| Pisagor | `c = √(a²+b²)` | `sqrt(a**2+b**2)` | 1.000 |
| Paralel Direnç | `R1R2/(R1+R2)` | `R1*R2/(R1+R2)` | 1.000 |
| Kepler 3. Yasa | `T = a^(3/2)` | `a_AU**(3/2)` | 1.000 |
| Serbest Düşme | `d = ½g·t²` | `4.905*t²` | 1.000 |
| Sarkaç | `T = 2π√(L/g)` | `2.005*sqrt(L)` | 1.000 |

---

## Gerçek Veri Testi

Teorik benchmark'lar bir yana. `datasets/rc_circuit.csv` dosyasında
100-10000 Ω arasında değişen direnç ve 1µF-1mF arasında kondansatör değerleriyle
oluşturulmuş, **%2 gürültü eklenmiş** 200 satırlık gerçek-dünya benzeri veri var.

```bash
python genesis_v2.py datasets/rc_circuit.csv tau
```

Çıktı:

```
Sympy    : C*R
R²(opt)  = 0.999174 | RMSE = 0.060132 | Süre = 18.6s
```

Gürültülü veri üzerinde `tau = R*C` formülünü doğru buluyor.

---

## Sınırlar (Dürüst Olmak Gerekirse)

Her araç gibi GENESIS'in de sınırları var:

**Karesel formlar sorunlu.** `E = ½mv²` ve `E = ½CV²` doğru ama verbose
formüller üretiyor. gplearn, iki değişkenin kareli kombinasyonlarında
bloat sorunuyla karşılaşıyor. Çözüm: PySR'a geçiş (Julia tabanlı, daha güçlü).

**Üstel/trigonometrik formlar zor.** `I = I₀·exp(V/Vt)` gibi formüller
standart fonksiyon setiyle zorlu — özel function set gerekiyor.

**Boyutsal analiz yok.** Motor birim tutarlılığı bilmiyor. 
`F = m·a` ile `F = m·v` arasında fiziksel tutarlılık açısından
ayrım yapamıyor — sadece veri uyumuna bakıyor.

---

## Sonra Ne Olacak?

- **PySR entegrasyonu**: Julia tabanlı motor, karesel formlar için çok daha iyi
- **API endpoint**: Flask/FastAPI ile HTTP üzerinden keşif
- **Gerçek bilimsel veriler**: CERN açık veri seti, NASA gözlem verileri
- **Feynman 120 Benchmark**: Tüm Feynman denklem setinde skor tablosu

---

## Dene

```bash
git clone https://github.com/cataplectic/GENESIS-V1.0-Symbolic-Regression-Engine.git
cd GENESIS-V1.0-Symbolic-Regression-Engine
pip install -r requirements.txt
streamlit run genesis_app.py
```

Kendi verinle ne keşfedeceksin?

---

*GENESIS açık kaynak, MIT lisansı altında.*
