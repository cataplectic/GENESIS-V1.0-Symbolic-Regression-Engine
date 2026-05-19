# Bu dosya v0.1 referans motorudur. Aktif geliştirme genesis_v2.py üzerindedir.
"""
GENESIS — Physics Law Discovery Engine
=======================================
Fizik yasalarını ham veriden otomatik keşfeden sembolik regresyon motoru.

Bu dosya projenin kalbi. İçinde:
1. Feynman benchmark veri üretici (bilinen fizik denklemleri)
2. Sembolik regresyon motoru (genetik programlama tabanlı)
3. Keşfedilen denklemlerin doğrulama ve raporlama sistemi
"""

import numpy as np
import pandas as pd
from gplearn.genetic import SymbolicRegressor
from gplearn.functions import make_function
from sklearn.metrics import mean_squared_error, r2_score
import warnings
import json
import time
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================
# BÖLÜM 1: FEYNMAN BENCHMARK VERİ SETİ
# ============================================================
# Richard Feynman'ın fizik derslerinden alınan gerçek denklemler.
# AI bunları "bilmeden", sadece ham veriden keşfedecek.

FEYNMAN_BENCHMARKS = {
    "newton_yercekim": {
        "name": "Newton Yerçekimi Yasası",
        "formula_latex": "F = G * m1 * m2 / r^2",
        "formula_str": "G * m1 * m2 / r**2",
        "variables": ["G", "m1", "m2", "r"],
        "variable_ranges": {
            "G": (6.674e-11, 6.674e-11),  # Sabit
            "m1": (1.0, 100.0),
            "m2": (1.0, 100.0),
            "r": (0.5, 10.0)
        },
        "description": "İki kütle arasındaki çekim kuvveti",
        "difficulty": "Orta"
    },
    "sarkaç_periyodu": {
        "name": "Basit Sarkaç Periyodu",
        "formula_latex": "T = 2π√(L/g)",
        "formula_str": "2 * 3.14159 * np.sqrt(L / g)",
        "variables": ["L", "g"],
        "variable_ranges": {
            "L": (0.1, 5.0),
            "g": (9.81, 9.81)  # Sabit
        },
        "description": "Sarkaç salınım periyodu",
        "difficulty": "Kolay"
    },
    "ohm_yasasi": {
        "name": "Ohm Yasası",
        "formula_latex": "V = I × R",
        "formula_str": "I * R",
        "variables": ["I", "R"],
        "variable_ranges": {
            "I": (0.01, 10.0),
            "R": (1.0, 1000.0)
        },
        "description": "Gerilim = Akım × Direnç",
        "difficulty": "Kolay"
    },
    "kinetik_enerji": {
        "name": "Kinetik Enerji",
        "formula_latex": "E = ½mv²",
        "formula_str": "0.5 * m * v**2",
        "variables": ["m", "v"],
        "variable_ranges": {
            "m": (0.1, 100.0),
            "v": (0.1, 50.0)
        },
        "description": "Hareket enerjisi",
        "difficulty": "Kolay"
    },
    "coulomb_yasasi": {
        "name": "Coulomb Yasası",
        "formula_latex": "F = k × q1 × q2 / r²",
        "formula_str": "k * q1 * q2 / r**2",
        "variables": ["k", "q1", "q2", "r"],
        "variable_ranges": {
            "k": (8.99e9, 8.99e9),  # Sabit
            "q1": (1e-6, 1e-3),
            "q2": (1e-6, 1e-3),
            "r": (0.01, 1.0)
        },
        "description": "İki yük arasındaki elektrostatik kuvvet",
        "difficulty": "Orta"
    },
    "ideal_gaz": {
        "name": "İdeal Gaz Yasası (Basınç)",
        "formula_latex": "P = nRT/V",
        "formula_str": "n * R * T / V",
        "variables": ["n", "R", "T", "V"],
        "variable_ranges": {
            "n": (0.1, 10.0),
            "R": (8.314, 8.314),  # Sabit
            "T": (200.0, 500.0),
            "V": (0.001, 0.1)
        },
        "description": "İdeal gaz basıncı",
        "difficulty": "Orta"
    },
    "serbest_dusme": {
        "name": "Serbest Düşme Mesafesi",
        "formula_latex": "d = ½gt²",
        "formula_str": "0.5 * g * t**2",
        "variables": ["g", "t"],
        "variable_ranges": {
            "g": (9.81, 9.81),
            "t": (0.1, 10.0)
        },
        "description": "Serbest düşmede kat edilen mesafe",
        "difficulty": "Kolay"
    },
    "dalga_hizi": {
        "name": "Dalga Hızı",
        "formula_latex": "v = f × λ",
        "formula_str": "f * lam",
        "variables": ["f", "lam"],
        "variable_ranges": {
            "f": (1.0, 1000.0),
            "lam": (0.01, 10.0)
        },
        "description": "Dalga hızı = frekans × dalga boyu",
        "difficulty": "Kolay"
    },
    "kepler_3": {
        "name": "Kepler 3. Yasası",
        "formula_latex": "T² = (4π²/GM) × r³",
        "formula_str": "(4 * 3.14159**2 / (G * M)) * r**3",
        "variables": ["G", "M", "r"],
        "variable_ranges": {
            "G": (6.674e-11, 6.674e-11),
            "M": (1e24, 2e30),
            "r": (1e8, 1e11)
        },
        "description": "Yörünge periyodunun karesi, yarıçapın küpüyle orantılı",
        "difficulty": "Zor"
    },
    "rc_devresi": {
        "name": "RC Devresi Zaman Sabiti Gerilimi",
        "formula_latex": "V(t) = V0 × e^(-t/RC)",
        "formula_str": "V0 * np.exp(-t / (R * C))",
        "variables": ["V0", "R", "C", "t"],
        "variable_ranges": {
            "V0": (1.0, 24.0),
            "R": (100.0, 100000.0),
            "C": (1e-6, 1e-3),
            "t": (0.0001, 0.1)
        },
        "description": "RC devresi boşalma gerilimi — senin müfredatından!",
        "difficulty": "Zor"
    }
}


def generate_data(benchmark_key, n_samples=500, noise_level=0.0):
    """
    Bir fizik denklemi için sentetik veri üretir.
    
    Gerçek dünyada sensörlerden veri toplarsın.
    Burada bilinen formüllerle veri üretip, AI'ın formülü
    yeniden keşfedip keşfedemeyeceğini test ediyoruz.
    
    Args:
        benchmark_key: FEYNMAN_BENCHMARKS'taki denklem anahtarı
        n_samples: Kaç veri noktası üretilecek
        noise_level: Gürültü seviyesi (0.0 = temiz, 0.05 = %5 gürültü)
    
    Returns:
        X: Girdi değişkenleri (numpy array)
        y: Çıktı değerleri (numpy array)
        var_names: Değişken isimleri listesi
    """
    benchmark = FEYNMAN_BENCHMARKS[benchmark_key]
    variables = benchmark["variables"]
    ranges = benchmark["variable_ranges"]
    
    # Her değişken için rastgele değerler üret
    data = {}
    for var in variables:
        low, high = ranges[var]
        if low == high:  # Sabit
            data[var] = np.full(n_samples, low)
        else:
            data[var] = np.random.uniform(low, high, n_samples)
    
    # Formülü hesapla
    local_vars = {**data, "np": np}
    y = eval(benchmark["formula_str"], {"__builtins__": {}}, local_vars)
    
    # Gürültü ekle (gerçek sensör verisini simüle etmek için)
    if noise_level > 0:
        noise = np.random.normal(0, noise_level * np.std(y), n_samples)
        y = y + noise
    
    # Sadece değişen değişkenleri al (sabitler hariç)
    varying_vars = [v for v in variables if ranges[v][0] != ranges[v][1]]
    X = np.column_stack([data[v] for v in varying_vars])
    
    return X, y, varying_vars


# ============================================================
# BÖLÜM 2: SEMBOLİK REGRESYON MOTORU
# ============================================================

class GenesisEngine:
    """
    GENESIS'in kalbi. Veri alır, fizik yasası çıkarır.
    
    Genetik Programlama kullanıyor:
    1. Rastgele matematiksel ifadeler üret (popülasyon)
    2. Her ifadeyi veriye uydur (fitness)
    3. En iyi ifadeleri seç, çaprazla, mutasyona uğrat
    4. Tekrarla — Darwin'in evrim teorisi ama denklemler için
    """
    
    def __init__(self, 
                 population_size=2000,
                 generations=50,
                 tournament_size=20,
                 max_complexity=20,
                 verbose=True):
        """
        Args:
            population_size: Aynı anda kaç farklı denklem denenecek
            generations: Kaç nesil evrim geçirecek
            tournament_size: Seçilim turnuva büyüklüğü
            max_complexity: Denklem karmaşıklığı üst sınırı
            verbose: İlerleme gösterilsin mi
        """
        self.population_size = population_size
        self.generations = generations
        self.verbose = verbose
        
        # Korunan (protected) operatörler — sıfıra bölme vb. hata vermez
        def _protected_div(x1, x2):
            with np.errstate(divide='ignore', invalid='ignore'):
                result = np.where(np.abs(x2) > 1e-10, x1 / x2, 1.0)
            return result
        
        def _protected_sqrt(x):
            return np.sqrt(np.abs(x))
        
        def _protected_log(x):
            with np.errstate(divide='ignore', invalid='ignore'):
                return np.where(np.abs(x) > 1e-10, np.log(np.abs(x)), 0.0)
        
        def _protected_exp(x):
            return np.exp(np.clip(x, -100, 100))
        
        protected_div = make_function(function=_protected_div, name='div', arity=2)
        protected_sqrt = make_function(function=_protected_sqrt, name='sqrt', arity=1)
        protected_log = make_function(function=_protected_log, name='log', arity=1)
        protected_exp = make_function(function=_protected_exp, name='exp', arity=1)
        
        self.model = SymbolicRegressor(
            population_size=population_size,
            generations=generations,
            tournament_size=tournament_size,
            stopping_criteria=1e-10,  # Mükemmel uyum bulursa dur
            p_crossover=0.7,
            p_subtree_mutation=0.1,
            p_hoist_mutation=0.05,
            p_point_mutation=0.1,
            max_samples=0.9,
            verbose=1 if verbose else 0,
            parsimony_coefficient=0.001,  # Basit formülleri tercih et (Occam'ın usturası)
            random_state=42,
            function_set=['add', 'sub', 'mul', protected_div, 
                         protected_sqrt, protected_log, protected_exp,
                         'neg', 'sin', 'cos'],
            metric='mse',
            n_jobs=1
        )
        
        self.results = []
    
    def discover(self, X, y, variable_names=None):
        """
        Ham veriden fizik yasası keşfet.
        
        Args:
            X: Girdi verileri (n_samples × n_features)
            y: Çıktı verileri (n_samples,)
            variable_names: Değişken isimleri (opsiyonel)
        
        Returns:
            dict: Keşfedilen denklem ve metrikler
        """
        start_time = time.time()
        
        if self.verbose:
            print("=" * 60)
            print("🔬 GENESIS — Fizik Yasası Keşfi Başlıyor")
            print("=" * 60)
            print(f"   Veri noktası sayısı : {X.shape[0]}")
            print(f"   Değişken sayısı     : {X.shape[1]}")
            if variable_names:
                print(f"   Değişkenler         : {variable_names}")
            print(f"   Popülasyon          : {self.population_size}")
            print(f"   Nesil sayısı        : {self.generations}")
            print("-" * 60)
            print("   Evrim başlıyor...\n")
        
        # Veriyi normalize et (büyük sayılarla çalışmayı kolaylaştırır)
        X_std = np.std(X, axis=0)
        X_std[X_std == 0] = 1.0
        X_mean = np.mean(X, axis=0)
        y_std = np.std(y) if np.std(y) > 0 else 1.0
        y_mean = np.mean(y)
        
        X_norm = (X - X_mean) / X_std
        y_norm = (y - y_mean) / y_std
        
        # Sembolik regresyon çalıştır
        self.model.fit(X_norm, y_norm)
        
        elapsed = time.time() - start_time
        
        # Sonuçları değerlendir
        y_pred_norm = self.model.predict(X_norm)
        y_pred = y_pred_norm * y_std + y_mean
        
        mse = mean_squared_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y - y_pred) / (np.abs(y) + 1e-10))) * 100
        
        # Keşfedilen formül
        raw_formula = str(self.model._program)
        
        # Değişken isimlerini yerleştir
        display_formula = raw_formula
        if variable_names:
            for i, name in enumerate(variable_names):
                display_formula = display_formula.replace(f"X{i}", name)
        
        result = {
            "formula_raw": raw_formula,
            "formula_display": display_formula,
            "r2_score": round(r2, 6),
            "rmse": rmse,
            "mape": round(mape, 4),
            "complexity": self.model._program.length_,
            "elapsed_seconds": round(elapsed, 2),
            "n_samples": X.shape[0],
            "n_variables": X.shape[1],
            "variable_names": variable_names,
            "timestamp": datetime.now().isoformat(),
            "normalized": True,
            "X_mean": X_mean.tolist(),
            "X_std": X_std.tolist(),
            "y_mean": float(y_mean),
            "y_std": float(y_std)
        }
        
        self.results.append(result)
        
        if self.verbose:
            print("\n" + "=" * 60)
            print("✅ KEŞİF TAMAMLANDI")
            print("=" * 60)
            print(f"   Keşfedilen formül   : {display_formula}")
            print(f"   R² skoru            : {r2:.6f}")
            print(f"   RMSE                : {rmse:.6e}")
            print(f"   MAPE                : {mape:.4f}%")
            print(f"   Karmaşıklık         : {self.model._program.length_}")
            print(f"   Süre                : {elapsed:.2f} saniye")
            print("=" * 60)
        
        return result
    
    def run_benchmark(self, benchmark_key, n_samples=500, noise_level=0.0):
        """
        Tek bir Feynman benchmark denklemini test et.
        """
        benchmark = FEYNMAN_BENCHMARKS[benchmark_key]
        
        if self.verbose:
            print(f"\n{'#' * 60}")
            print(f"# HEDEF: {benchmark['name']}")
            print(f"# Gerçek formül: {benchmark['formula_latex']}")
            print(f"# Zorluk: {benchmark['difficulty']}")
            print(f"{'#' * 60}")
        
        X, y, var_names = generate_data(benchmark_key, n_samples, noise_level)
        result = self.discover(X, y, var_names)
        
        result["benchmark_key"] = benchmark_key
        result["benchmark_name"] = benchmark["name"]
        result["true_formula"] = benchmark["formula_latex"]
        result["difficulty"] = benchmark["difficulty"]
        result["noise_level"] = noise_level
        
        return result
    
    def run_full_benchmark(self, noise_level=0.0, 
                           difficulty_filter=None,
                           n_samples=500):
        """
        Tüm Feynman benchmark'larını çalıştır.
        Bu, GENESIS'in "Nature makalesi" demosunun temelidir.
        """
        all_results = []
        
        for key, benchmark in FEYNMAN_BENCHMARKS.items():
            if difficulty_filter and benchmark["difficulty"] != difficulty_filter:
                continue
            
            result = self.run_benchmark(key, n_samples, noise_level)
            all_results.append(result)
        
        return all_results
    
    def generate_report(self, results, output_path="genesis_report.json"):
        """
        Sonuçları JSON rapor olarak kaydet.
        Bu rapor yatırımcılara ve akademisyenlere gösterilecek.
        """
        report = {
            "project": "GENESIS — Physics Law Discovery Engine",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": len(results),
                "avg_r2": round(np.mean([r["r2_score"] for r in results]), 4),
                "avg_mape": round(np.mean([r["mape"] for r in results]), 4),
                "total_time_seconds": round(sum(r["elapsed_seconds"] for r in results), 2),
                "perfect_discoveries": sum(1 for r in results if r["r2_score"] > 0.99)
            },
            "results": results
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"\n📊 Rapor kaydedildi: {output_path}")
            print(f"   Toplam test: {report['summary']['total_benchmarks']}")
            print(f"   Ortalama R²: {report['summary']['avg_r2']}")
            print(f"   Mükemmel keşif (R²>0.99): {report['summary']['perfect_discoveries']}")
        
        return report


# ============================================================
# BÖLÜM 3: ANA ÇALIŞTIRMA
# ============================================================

if __name__ == "__main__":
    print("""
    ╔═════════════════════════════════════════════════════ ═╗
    ║                                                       ║
    ║   ██████  ███████ ███    ██ ███████ ███████ ██ ███████║
    ║  ██       ██      ████   ██ ██      ██      ██ ██     ║
    ║  ██   ███ █████   ██ ██  ██ █████   ███████ ██ ███████║
    ║  ██    ██ ██      ██  ██ ██ ██           ██ ██      ██║
    ║   ██████  ███████ ██   ████ ███████ ███████ ██ ███████║
    ║                                                       ║
    ║   Physics Law Discovery Engine v0.1.0                 ║
    ║   "Veri girer, fizik yasası çıkar"                    ║
    ╚═════════════════════════════════════════════════════ ═╝
    """)
    
    # Kolay denklemlerle başla (ilk demo)
    engine = GenesisEngine(
        population_size=1000,
        generations=30,
        verbose=True
    )
    
    # Seçili benchmark'ları çalıştır
    test_keys = ["ohm_yasasi", "kinetik_enerji", "serbest_dusme", "dalga_hizi", "sarkaç_periyodu"]
    
    results = []
    for key in test_keys:
        result = engine.run_benchmark(key, n_samples=300, noise_level=0.0)
        results.append(result)
    
    # Rapor üret
    report = engine.generate_report(results, "/home/claude/genesis/genesis_report.json")
    
    print("\n" + "=" * 60)
    print("GENESIS BENCHMARK SONUÇLARI")
    print("=" * 60)
    print(f"{'Denklem':<30} {'Gerçek Formül':<20} {'R²':<12} {'Süre':<8}")
    print("-" * 70)
    for r in results:
        print(f"{r['benchmark_name']:<30} {r['true_formula']:<20} {r['r2_score']:<12.6f} {r['elapsed_seconds']:<8.2f}s")
    print("=" * 60)
