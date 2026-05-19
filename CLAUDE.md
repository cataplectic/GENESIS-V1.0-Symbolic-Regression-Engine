# GENESIS — Physics Law Discovery Engine

## Proje Ne Yapıyor?
Ham sayısal veriden fizik/mühendislik yasalarını otomatik keşfeden sembolik regresyon motoru.
Veri giriyor → matematiksel formül çıkıyor. İnsan müdahalesi yok.

## Teknoloji
- Python 3.10+
- gplearn — genetik programlama tabanlı sembolik regresyon
- numpy, pandas, scikit-learn, matplotlib
- scipy — sabit optimizasyonu (Nelder-Mead)
- sympy — cebirsel sadeleştirme
- streamlit — interaktif web demo

## Proje Yapısı

```
genesis-ai/
├── README.md              ← GitHub vitrini — v1.0 final
├── CLAUDE.md              ← Bu dosya. Proje rehberi.
├── requirements.txt       ← pip bağımlılıkları
├── .gitignore             ← Python + IDE + üretilen dosyalar
│
├── genesis_v2.py          ← ANA MOTOR (v1.0)
├── genesis_viz.py         ← Grafik üretici
├── genesis_app.py         ← Streamlit web demo
├── genesis_gui.py         ← Masaüstü uygulama (PyQt6)
├── genesis_engine.py      ← v0.1 referans motoru (aktif değil)
├── genesis_dashboard.jsx  ← Eski React panel (arşiv)
├── blog_post.md           ← Blog yazısı taslağı
│
├── datasets/
│   ├── README.md
│   ├── rc_circuit.csv          ← tau = R*C
│   ├── projectile.csv          ← range = v0²sin(2θ)/g
│   ├── planetary_orbits.csv    ← T = a^(3/2)
│   ├── beam_deflection.csv     ← delta = FL³/3EI
│   ├── led_iv_curve.csv        ← Shockley (zor)
│   ├── stars.csv               ← L = R²·T_Tsun⁴ (Stefan-Boltzmann, R²=0.996)
│   ├── materials_strength.csv  ← beton dayanımı (açık uçlu)
│   ├── planet_data.csv         ← exoplanet, Kepler + ek
│   ├── battery_degradation.csv ← Arrhenius degradasyon (açık uçlu)
│   ├── airfoil.csv             ← NASA ses gürültüsü (log ölçeği)
│   ├── concrete.csv            ← UCI beton (R²=0.74)
│   ├── ccpp.csv                ← güç santrali (R²=0.85)
│   └── yacht.csv               ← yat hidrodinamiği (R²=0.995, Froude)
├── download_datasets.py        ← 5 yeni veri seti indirici/üretici
│
├── plots/                 ← genesis_viz.py çıktısı (gitignore'da)
│   ├── accuracy.png
│   ├── complexity_accuracy.png
│   └── time.png
│
├── example_data.csv       ← RC devre, 100 satır, %2 gürültü
├── results_v2.json        ← Son benchmark sonuçları
└── discovery_report.md    ← Otomatik Markdown raporu
```

## Mevcut Durum (v1.0)

### Benchmark Sonuçları
- **16 Kolay** benchmark çalıştırıldı: **16/16 R²≥0.999** ✅
- Ortalama R²: 1.0000, ortalama süre: 18.2s
- **13 Orta** ve **2 Zor** benchmark tanımlı ama çalıştırılmadı (~60 dk)
- Planck Enerji-Frekans: ölçek düzeltmesi yapıldı (f_THz, sabit=6.626 ∈ (-10,10))

### Temiz Sympy Çıktıları (Birebir Formül)
`I*R`, `f*λ`, `k*x`, `m*v`, `I**2*R`, `R1+R2+R3`, `A*dT*k/dx`, `sqrt(a**2+b**2)`,
`R1*R2/(R1+R2)`, `0.5*C*V**2` (kondansatör)

### Karmaşık Ama Doğru Formüller (gplearn bloat)
Kinetik Enerji (R²=0.99998), İndüktans Enerjisi (R²=0.99966),
Serbest Düşme, Küre Hacmi, Planck — yapı doğru, sympy sadeleştiremedi

## genesis_v2.py — Fonksiyon Referansı

### Temel API
```python
discover(X, y, var_names, pop=3000, gens=50, verbose=True, function_set=None)
# → dict: formula, formula_opt, formula_sympy, formula_latex, r2, r2_opt, rmse, complexity, seconds

discover_from_csv(filepath, target_column, max_rows=1000, pop=2000, gens=40, robust=False)
# → dict (yukarıdakine ek: source, target, n_samples, variables)
# robust=True → discover_robust() çağırır (3 motorla Pareto seçimi)

discover_robust(X, y, var_names, pop=2000, gens=40, verbose=True)
# → discover() ile aynı formatlı dict + "engine", "all_results" alanları
# 3 function_set: no_div, standard, extended
# Pareto seçimi: R² > 0.99 → min complexity; yoksa max R²
# Stefan-Boltzmann testi: no_div → T_Tsun**4 (R²=0.9992, karmaşıklık=7) ✅

run_all(difficulty=None, keys=None, pop=2000, gens=40, output_json="results_v2.json")
# difficulty="Kolay"/"Orta"/"Zor" filtresi veya keys=["ohm","hooke"] listesi
# Her benchmark sonrası incremental JSON save
# Biten tüm sonuçlar için discovery_report.md otomatik üretilir

generate_discovery_report(results_list, output_path="discovery_report.md")
# plots/ varsa grafik referansları eklenir
```

### Sabitler ve Yapılandırma
```python
_FS_STANDARD = ['add', 'sub', 'mul', pdiv, psqrt]
_FS_TRIG     = [..., 'sin', 'cos', parcsin]       # work, snell için

# discover() gplearn parametreleri:
parsimony_coefficient = 0.003   # Occam's razor baskısı
p_crossover           = 0.70
p_subtree_mutation    = 0.10
p_hoist_mutation      = 0.15   # ağaç kısaltıcı — bloat kontrolü
p_point_mutation      = 0.05
init_depth            = (2, 4)
const_range           = (-10.0, 10.0)
```

### Benchmark Kategorileri (31 Toplam)
| Kategori | Sayı | Key'ler |
|---|---|---|
| Kolay | 16 | ohm, kinetic, freefall, wave, capacitor, hooke, momentum, potential_energy, power_vi, power_resistive, series_resistance, inductor_energy, heat_transfer, energy_freq, pythagorean, sphere_volume |
| Orta | 13 | pendulum, gravity, resistor_parallel, work, centripetal, capacitor_series, resonance_freq, impedance_rl, ideal_gas_temp, doppler, escape_vel, orbital_vel, cylinder_surface |
| Zor | 2 | stefan_boltzmann, snell |

## genesis_gui.py — Masaüstü Uygulama (PyQt6)

```bash
python genesis_gui.py   # → 1280×840 pencere
```

**Sekmeler:**
- **Keşif** — Benchmark/CSV seç, motor ayarları, Başlat → formül + scatter + metrikler
- **Benchmark Tablosu** — results_v2.json'dan yükle; çift tıkla detay; "Tümünü Çalıştır"
- **Hakkında** — Proje açıklaması, kullanım, teknoloji

**Thread mimarisi:**
- `DiscoveryWorker(QThread)` — discover() çağrısı; `finished(dict)` / `error(str)` sinyalleri
- `RunAllWorker(QThread)` — sıralı benchmark çalıştırıcı; `row_done(key, result)` her satır için
- Durdur butonu: `worker.terminate()`

**Teknik notlar:**
- `pyqtgraph` ile Gerçek vs Tahmin scatter; yoksa placeholder label
- Scatter için sympy lambdify kullanılır; hata olursa plot atlanır
- Her keşif sonucu otomatik results_v2.json'a eklenir; serileştirilemez ndarray alanlar temizlenir
- QSS ile tam koyu tema: BG=#1a1a2e, PANEL=#16213e, ACCENT=#0f3460

## genesis_viz.py — Grafik Referansı

```python
plot_accuracy_bar(json, output="plots/accuracy.png")
# Yatay bar, X=[0.94,1.002], renk: yeşil/mavi/turuncu/kırmızı

plot_complexity_vs_accuracy(json, output="plots/complexity_accuracy.png")
# Scatter, sol üst = ideal bölge (yeşil bg)

plot_discovery_time(json, output="plots/time.png")
# Zorluk gruplu bar (Kolay=yeşil, Orta=turuncu, Zor=kırmızı)

generate_all_plots(json_path, plots_dir="plots")  # 3'ünü birden üretir
# CLI: python genesis_viz.py results_v2.json
```

## genesis_app.py — Streamlit

```bash
streamlit run genesis_app.py   # → http://localhost:8501
```

**Benchmark modu:** 4 metrik kartı + styled DataFrame (R² renk) + expander detay  
**CSV modu:** file_uploader → hedef seç → discover() → scatter plot + JSON indir

## Çalıştırma Komutları

```bash
# Kolay benchmark'lar (~5 dk)
python -c "import genesis_v2 as g; g.run_all(difficulty='Kolay')"

# Orta benchmark'lar (~25 dk) — çalıştırılmadı
python -c "import genesis_v2 as g; g.run_all(difficulty='Orta')"

# Zor benchmark'lar (~10 dk) — çalıştırılmadı
python -c "import genesis_v2 as g; g.run_all(difficulty='Zor')"

# Grafikler
python genesis_viz.py results_v2.json

# Web demo
streamlit run genesis_app.py

# CSV keşif
python genesis_v2.py datasets/rc_circuit.csv tau
python genesis_v2.py datasets/planetary_orbits.csv T_years
```

## Bilinen Sorunlar (v1.0)

1. **Karesel formlar (½mv², ½LI²)** — gplearn bloat. Sympy doğruluğu yüksek ama formül karmaşık.
   → Çözüm: PySR geçişi (Julia tabanlı, daha güçlü)

2. **Ölçek sorunları** — Çok küçük sabitler (Planck: 6.626e-34) const_range dışında kalır.
   → Düzeltme: normalize edilmiş birimler kullan (energy_freq: f_THz, h_norm=6.626)

3. **Orta/Zor benchmark'lar test edilmedi** — 15 benchmark çalıştırılmayı bekliyor.

4. **Pareto Front yok** — Karmaşıklık vs doğruluk eğrisi (tek formül yerine).

5. **LED IV curve** — Üstel büyüme standart function set ile zorlu.

6. **Airfoil ses gürültüsü (dB)** — Log ölçeği. Standart function set ile R²=-0.53. Çözüm: `log/exp` içeren custom function_set kullan.

7. **Stars veri seti** — T'yi ham Kelvin olarak saklama; `const_range=(-10,10)` 5778'i kapsayamaz. Çözüm: T_Tsun = T/5778 normalize sütunu kullan (v1.1'de düzeltildi).

## Katkıda Bulunurken

- Yeni benchmark: `BENCHMARKS` dict + `_gen_xxx(n)` fonksiyonu ekle
- Ölçek kontrolü: sabit değerleri const_range=(-10,10) içinde kalmalı — gerekirse birimler normalize et
- Testler: `python -c "import genesis_v2 as g; g.run_all(keys=['yeni_key'])"` ile izole test
- Grafikler: `python genesis_viz.py results_v2.json` ile doğrula
- Streamlit: `streamlit run genesis_app.py` ile UI'ı kontrol et

## Versiyon Geçmişi

| Versiyon | Tarih | Öne Çıkan |
|---|---|---|
| v0.1 | — | genesis_engine.py, 10 Feynman benchmark |
| v0.2 | — | 7 benchmark, normalizasyon kaldırıldı |
| v0.3 | — | fold_constants, scipy, sympy, parsimony=0.003 |
| v0.4 | — | CSV desteği, CLI, README, example_data.csv |
| v0.5 | — | 31 benchmark, run_all(difficulty), generate_discovery_report() |
| v0.6 | — | genesis_viz.py, genesis_app.py (Streamlit), datasets/5CSV |
| **v1.0** | **2026-05-19** | **requirements.txt, .gitignore, blog_post.md, 16 Kolay R²=1.0** |
| **v1.1** | **2026-05-19** | **genesis_gui.py (PyQt6), brute_force_discover(), 8→13 dataset, stars/yacht/ccpp/concrete/airfoil** |
| **v1.2** | **2026-05-20** | **discover_robust() (3-motor Pareto), --robust CLI flag, GUI robust checkbox, test_stefan.py** |
