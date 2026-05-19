"""
Stefan-Boltzmann yasası keşfi — discover_robust() testi.

Tek değişken: T (normalize edilmemiş, ham Kelvin).
Hedef:        L = (T / 5778)^4  (R=1 varsayılır)

Beklenti:
  no_div motoru   → T^4 ilişkisini bulur (mul(mul(T,T), mul(T,T)) şeklinde)
  extended motoru → log(4*log(T)) ifadesine yaklaşabilir ama daha karmaşık
  Pareto seçimi   → en basit + R²>0.99 formül seçilir
"""
import numpy as np
from genesis_v2 import discover_robust

np.random.seed(42)
n = 500
T_raw = np.random.uniform(2000, 40000, n)
T_norm = T_raw / 5778                          # [0.35, 6.92]
L = T_norm ** 4                                # gerçek değer
noise = np.random.normal(1.0, 0.02, n)         # %2 gürültü
L_noisy = L * noise

# Normalize T girin — const_range=(-10,10) içinde sabit yok
X = (T_raw / 5778).reshape(-1, 1)             # T_Tsun olarak
y = L_noisy

print("=" * 60)
print("  TEST: Stefan-Boltzmann — L = T_Tsun^4")
print("  Değişken: T_Tsun = T_Kelvin / 5778  (boyutsuz)")
print("=" * 60)

result = discover_robust(X, y, ["T_Tsun"], pop=2000, gens=40, verbose=True)

print("\n" + "=" * 60)
print("  SONUÇ")
print("=" * 60)
print(f"  Final formül : {result['formula_sympy']}")
print(f"  Motor        : {result['engine']}")
print(f"  R²           : {result['r2_opt']:.6f}")
print(f"  Karmaşıklık  : {result['complexity']}")
print(f"\n  Tüm motorlar:")
for r in result.get("all_results", []):
    print(f"    {r['engine']:10s}: R²={r['r2_opt']:.4f}  "
          f"karmaşıklık={r['complexity']:3d}  {str(r['formula_sympy'])[:50]}")
