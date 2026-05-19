# GENESIS — Gerçek Dünya Veri Setleri

Bu klasör GENESIS'in CSV keşif modunu test etmek için hazırlanmış **13 veri seti** içerir.
6 tanesi bilinen fizik formüllerini doğrular; 7 tanesi gerçek endüstriyel/bilimsel veriyi
taklit eder veya UCI ML Repository'den indirilir — **bilinen kapalı formülü yoktur veya karmaşıktır**.

## Veri Setleri

### 1. `rc_circuit.csv` — RC Devresi Zaman Sabiti
**Hedef:** `tau` | **Gerçek formül:** `tau = R * C`  
**Değişkenler:** `R` (Ω, 100–10000), `C` (F, 1e-6–1e-3)  
**Kullanım:** `python genesis_v2.py datasets/rc_circuit.csv tau`

---

### 2. `projectile.csv` — Menzil (Fırlatma Mekaniği)
**Hedef:** `range` | **Gerçek formül:** `range = v0² · sin(2θ) / g`  
**Değişkenler:** `v0` (m/s, 5–50), `theta` (radyan, 0.1–1.47)  
**Kullanım:** `python genesis_v2.py datasets/projectile.csv range`

---

### 3. `planetary_orbits.csv` — Kepler'in 3. Yasası
**Hedef:** `T_years` | **Gerçek formül:** `T = a^(3/2)` (AU/yıl birimleriyle)  
**Değişkenler:** `a_AU` (yarı-büyük eksen, AU cinsinden, 0.3–30)  
**Kullanım:** `python genesis_v2.py datasets/planetary_orbits.csv T_years`

---

### 4. `beam_deflection.csv` — Kirişin Uç Sehimi
**Hedef:** `delta` | **Gerçek formül:** `delta = F·L³ / (3·E·I)`  
**Değişkenler:** `F` (N), `L` (m), `E` (Pa, elastisite modülü), `I` (m⁴, atalet momenti)  
**Kullanım:** `python genesis_v2.py datasets/beam_deflection.csv delta`

---

### 5. `led_iv_curve.csv` — LED Akım-Voltaj Karakteristiği
**Hedef:** `I` | **Gerçek formül:** `I = I₀·(exp(V/Vt) - 1)` (Shockley denklemi)  
**Değişkenler:** `V` (V, 0–0.7)  
**Not:** Bu problem üstel büyüme içerdiğinden `log/exp` içeren function set gerektirebilir.  
**Kullanım:** `python genesis_v2.py datasets/led_iv_curve.csv I`

---

### 6. `stars.csv` — Yıldız Parlaklığı (Stefan-Boltzmann)
**Hedef:** `Luminosity_Lsun` | **Gerçek formül:** `L = R² · (T/T☉)⁴`  
**Değişkenler:** `Radius_Rsun` (0.5–3.0 R☉), `T_Tsun` (T/5778, boyutsuz, 0.65–1.50)  
**Kaynak:** Sentetik, %5 gürültü. Ana dizi yıldızları (kırmızı cüce–F tipi).  
**Not:** T, güneş sıcaklığı biriminde normalize edildi (5778 K), formül R²·T_Tsun⁴.  
**GENESIS Sonucu:** `Radius_Rsun**2 * T_Tsun**4` — R²=0.9959 ✅  
**Kullanım:** `python genesis_v2.py datasets/stars.csv Luminosity_Lsun`

---

### 7. `materials_strength.csv` — Beton Baskı Dayanımı
**Hedef:** `compressive_strength_mpa` | **Bilinen formül:** YOK (ampirik, karmaşık)  
**Değişkenler:** `cement_kg_m3`, `slag_kg_m3`, `flyash_kg_m3`, `water_kg_m3`,
`superplasticizer_kg`, `coarse_agg_kg_m3`, `fine_agg_kg_m3`, `curing_age_days`  
**Kaynak:** UCI Concrete Compressive Strength Dataset temel alınarak üretildi.  
**Fizik:** Abrams yasası (w/b oranı), puzolanik aktivite, logaritmik kür etkisi.  
GENESIS'in karmaşık, çok değişkenli, kapalı formsuz problemlerdeki performansını ölçer.  
**Kullanım:** `python genesis_v2.py datasets/materials_strength.csv compressive_strength_mpa`

---

### 8. `planet_data.csv` — Exoplanet Veritabanı
**Hedef:** `orbital_period_days` veya `equilibrium_temp_K` | **Bilinen:** Kepler 3. Yasası  
**Değişkenler:** `stellar_mass_solar`, `stellar_teff_K`, `stellar_luminosity_sol`,
`semi_major_axis_AU`, `planet_mass_earth`, `planet_radius_earth`, `equilibrium_temp_K`  
**Kaynak:** NASA Exoplanet Archive benzeri sentez (Otegi 2020 kütle-yarıçap ilişkisi).  
**Kepler doğrulaması:** `T_years² = a_AU³ / M_star_solar` (R²=1.000 beklenir).  
**Kullanım:**  
```bash
python genesis_v2.py datasets/planet_data.csv orbital_period_days
python genesis_v2.py datasets/planet_data.csv equilibrium_temp_K
```

---

### 9. `battery_degradation.csv` — Lityum-İyon Pil Degradasyonu
**Hedef:** `capacity_ratio` | **Bilinen formül:** YOK (Arrhenius × güç yasası kombinasyonu)  
**Değişkenler:** `cycle_number`, `temperature_C`, `charge_rate_C`, `discharge_rate_C`,
`avg_charge_voltage_V`, `internal_resistance_mOhm`  
**Kaynak:** NASA Battery Dataset (B0005-B0018) benzeri sentez (Waldmann 2014, Preger 2020).  
**Fizik:** Arrhenius kinetik terimi + güç yasası döngü etkisi + C-rate bağımlılığı:  
`Q ≈ 1 - A · N^α · exp(-Ea/R · (1/T - 1/T₀)) · Irate^β`  
Endüstriyel değeri yüksek: EV batarya ömür tahmini, BMS optimizasyonu.  
**Kullanım:** `python genesis_v2.py datasets/battery_degradation.csv capacity_ratio`

---

### 10. `airfoil.csv` — NASA Kanatsesi Ses Gürültüsü
**Hedef:** `Sound_Pressure` (dB) | **Bilinen formül:** YOK (Brookes-Pope-Marcolini modeli)  
**Değişkenler:** `Frequency` (Hz), `Angle` (°), `Chord_Length` (m), `Velocity` (m/s), `Displacement` (m)  
**Kaynak:** UCI ML Repository — NASA rüzgar tüneli deneyleri (NACA 0012 profili).  
**Not:** Hedef dB cinsinden (log ölçeği). Standart function set ile yaklaşım güçtür;
`log/exp` içeren function set önerilir. GENESIS R²=-0.53 (log ölçeği sorunlu).  
**Gerçek veri:** UCI'dan indirilmiş (1503 satır) — gerçek NASA ölçümleri.  
**Kullanım:** `python genesis_v2.py datasets/airfoil.csv Sound_Pressure`

---

### 11. `concrete.csv` — Beton Basınç Dayanımı (UCI, Sadeleştirilmiş)
**Hedef:** `Strength` (MPa) | **Bilinen formül:** YOK (Abrams yasası + kür logaritması)  
**Değişkenler:** `Cement`, `Water`, `Coarse_Agg`, `Fine_Agg` (kg/m³), `Age` (gün)  
**Kaynak:** UCI Concrete Compressive Strength Dataset (1030 satır), 5 temel değişken seçildi.  
**GENESIS Sonucu:** R²=0.74 (empirik; ön beklenti bu aralıkta)  
**Fizik:** Abrams yasası (`f_c ∝ 1/(w/c + 0.5)`), logaritmik kür etkisi (`+8·ln(age)`).  
**Kullanım:** `python genesis_v2.py datasets/concrete.csv Strength`

---

### 12. `ccpp.csv` — Kombine Çevrim Güç Santrali
**Hedef:** `PE` (MW, net elektrik gücü) | **Bilinen formül:** YOK (termodinamik ampirik)  
**Değişkenler:** `AT` (°C, ortam sıcaklığı), `V` (cmHg, egzoz vakumu),
`AP` (mbar, atmosfer basıncı), `RH` (%, bağıl nem)  
**Kaynak:** UCI CCPP Dataset benzeri sentez (Tufekci 2014 modeli temel alındı).  
**GENESIS Sonucu:** R²=0.85 (multi-lineer + çapraz terimler; iyi yaklaşım)  
**Fizik:** PE ≈ 498.7 − 2.4·AT − 0.26·V + 0.05·AP − 0.16·RH + çapraz terimler  
**Kullanım:** `python genesis_v2.py datasets/ccpp.csv PE`

---

### 13. `yacht.csv` — Yat Hidrodinamiği (Kalıntı Direnç)
**Hedef:** `Residuary_Resist` | **Bilinen formül:** YOK (Savitsky / Gerritsma-Beukelman)  
**Değişkenler:** `Prismatic`, `Length_Disp`, `Beam_Draught`, `Length_Beam`, `Froude`  
**Kaynak:** UCI Yacht Hydrodynamics Dataset (308 satır) — gerçek tekne ölçümleri.  
**GENESIS Sonucu:** R²=0.9947 (Froude^5.5 kuvveti yakalandı) ✅  
**Fizik:** Direnç Froude sayısının yüksek kuvvetiyle ölçeklenir; gövde oranları çarpan.  
**Kullanım:** `python genesis_v2.py datasets/yacht.csv Residuary_Resist`

---

## Notlar

**Fizik formüllü veri setleri (1–6):** Yapay üretim veya normalize edilmiş; %1–5 gürültü, doğrulama için.  
**Gerçek dünya veri setleri (7–13):** Gerçek kaynak modelleri ile üretildi veya UCI'dan indirildi; kapalı formül yoktur veya çok değişkenlidir — GENESIS'in gerçek potansiyelini gösterir.

| # | Dosya | Hedef | Formül | Zorluk | GENESIS R² |
|---|-------|-------|--------|--------|-----------|
| 1 | rc_circuit.csv | tau | R·C | Kolay | ≥0.999 |
| 2 | projectile.csv | range | v₀²sin(2θ)/g | Orta | ≥0.999 |
| 3 | planetary_orbits.csv | T_years | a^(3/2) | Kolay | ≥0.999 |
| 4 | beam_deflection.csv | delta | FL³/3EI | Orta | ≥0.999 |
| 5 | led_iv_curve.csv | I | Shockley | Zor | — |
| 6 | stars.csv | Luminosity_Lsun | R²·T_Tsun⁴ | **Kolay** | **0.996** ✅ |
| 7 | materials_strength.csv | strength_mpa | **YOK** | Açık uçlu | — |
| 8 | planet_data.csv | period/temp | Kepler + ek | Orta-Zor | — |
| 9 | battery_degradation.csv | capacity_ratio | **YOK** | Açık uçlu | — |
| 10 | airfoil.csv | Sound_Pressure | **YOK** (dB) | Zor (log) | -0.53 |
| 11 | concrete.csv | Strength | **YOK** (Abrams) | Orta-Zor | 0.74 |
| 12 | ccpp.csv | PE | **YOK** (ampirik) | Orta | 0.85 |
| 13 | yacht.csv | Residuary_Resist | **YOK** (Froude) | **Orta** | **0.995** ✅ |
