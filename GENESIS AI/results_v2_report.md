# GENESIS — Otomatik Fizik Yasası Keşif Raporu

**Tarih:** 2026-05-17 21:55
**Versiyon:** v0.5

## Özet

| Metrik | Değer |
|--------|-------|
| Toplam benchmark | 5 |
| Mükemmel keşif (R²>0.99) | 5 |
| İyi keşif (0.95<R²≤0.99) | 0 |
| Başarısız (R²≤0.95) | 0 |
| Ortalama R²(opt) | 1.0000 |

## Detaylı Sonuçlar

| # | Yasa | Zorluk | Gerçek Formül | Keşfedilen (Sympy) | R²(opt) | Süre (s) |
|---|------|--------|---------------|-------------------|---------|----------|
| 1 | ✅ Hooke Yasası | Kolay | `F = k × x` | `k*x` | 1.0000 | 0.7 |
| 2 | ✅ Momentum | Kolay | `p = m × v` | `m*v` | 1.0000 | 0.6 |
| 3 | ✅ Seri Direnç | Kolay | `R = R1 + R2 + R3` | `R1 + R2 + R3` | 1.0000 | 1.2 |
| 4 | ✅ Pisagor Teoremi | Kolay | `c = √(a² + b²)` | `sqrt(a**2 + b**2)` | 1.0000 | 24.7 |
| 5 | ✅ Elektrik Gücü (VI) | Kolay | `P = V × I` | `I*V` | 1.0000 | 1.7 |

## Zorluk Bazlı Analiz

**Kolay** — 5 denklem, ortalama R²=1.0000, mükemmel=5/5

---
*Bu rapor GENESIS tarafından otomatik üretilmiştir.*