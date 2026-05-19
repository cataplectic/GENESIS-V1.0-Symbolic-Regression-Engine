"""
GENESIS v0.3 — Geliştirilmiş Çalıştırıcı
Normalizasyon olmadan çalışır → okunabilir formüller üretir
v0.3: Sabit Optimizasyonu + Sympy Sadeleştirme
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')   # λ gibi Unicode karakterler için

import os
import re
import itertools
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from gplearn.genetic import SymbolicRegressor
from gplearn.functions import make_function
from sklearn.metrics import mean_squared_error, r2_score
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Korunan fonksiyonlar
def _pdiv(x1, x2):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.abs(x2) > 1e-10, x1 / x2, 1.0)

def _psqrt(x):
    return np.sqrt(np.abs(x))

def _plog(x):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.abs(x) > 1e-10, np.log(np.abs(x)), 0.0)

def _pexp(x):
    return np.exp(np.clip(x, -100, 100))

def _parcsin(x):
    return np.arcsin(np.clip(x, -1.0, 1.0))

pdiv   = make_function(function=_pdiv,   name='div',    arity=2)
psqrt  = make_function(function=_psqrt,  name='sqrt',   arity=1)
plog   = make_function(function=_plog,   name='log',    arity=1)
pexp   = make_function(function=_pexp,   name='exp',    arity=1)
parcsin = make_function(function=_parcsin, name='arcsin', arity=1)

# Standart ve trigonometrik fonksiyon setleri
_FS_STANDARD = ['add', 'sub', 'mul', pdiv, psqrt]
_FS_TRIG     = ['add', 'sub', 'mul', pdiv, psqrt, 'sin', 'cos', parcsin]


# ─── Sabit Optimizasyonu Modülü ──────────────────────────────────────────────

# Scalar (tek sayı) versiyonlar — constant folding için
_FOLD_FUNCS = {
    'mul': lambda a, b: a * b,
    'add': lambda a, b: a + b,
    'sub': lambda a, b: a - b,
    'div': lambda a, b: a / b if abs(b) > 1e-10 else 1.0,
    'sqrt': lambda a: float(np.sqrt(abs(a))),
    'log': lambda a: float(np.log(abs(a))) if abs(a) > 1e-10 else 0.0,
    'exp': lambda a: float(np.exp(np.clip(a, -100, 100))),
}

# Tanınan fizik/matematik sabitleri (değer, etiket)
_NICE_CONSTS = [
    (0.5,                          '0.5'),
    (0.25,                         '0.25'),
    (2.0,                          '2'),
    (np.pi,                        'pi'),
    (np.pi / 2,                    'pi/2'),
    (2 * np.pi,                    '2*pi'),
    (np.sqrt(2),                   'sqrt(2)'),
    (9.81,                         '9.81'),
    (9.81 / 2,                     '4.905'),
    (1.0 / 9.81,                   '1/9.81'),
    (np.sqrt(9.81),                'sqrt(9.81)'),
    (1.0 / np.sqrt(9.81),          '1/sqrt(9.81)'),
    (2 * np.pi / np.sqrt(9.81),    '2*pi/sqrt(9.81)'),
]

_FUNC_CALL_RE = re.compile(r'(mul|add|sub|div|sqrt|log|exp)\(([^()]*)\)')
_NUM_RE = re.compile(r'(?<![A-Za-z_\d])(-?\d*\.?\d+)(?![A-Za-z_\d\.])')


def fold_constants(formula, var_names):
    """
    Yalnızca sayı içeren alt-ağaçları (değişken olmayan) tek sayıya indir.
    Örn: div(2.321, -1.214) → -1.912683...  (bottom-up, iteratif)
    """
    changed = True
    while changed:
        changed = False

        def _fold(m):
            nonlocal changed
            fname, args_str = m.group(1), m.group(2)
            # Herhangi bir değişken varsa dokunma
            if any(re.search(r'\b' + re.escape(v) + r'\b', args_str)
                   for v in var_names):
                return m.group(0)
            try:
                parts = [p.strip() for p in args_str.split(',') if p.strip()]
                nums = [float(p) for p in parts]
                arity_ok = (fname in ('sqrt', 'log', 'exp') and len(nums) == 1) or \
                           (fname in ('mul', 'add', 'sub', 'div') and len(nums) == 2)
                if not arity_ok:
                    return m.group(0)
                val = _FOLD_FUNCS[fname](*nums)
                changed = True
                return f'{val:.10g}'
            except Exception:
                return m.group(0)

        formula = _FUNC_CALL_RE.sub(_fold, formula)
    return formula


def _eval_formula(template, c, X, var_names):
    """Şablonu verilen sabitler ve değişkenlerle vektörsel değerlendir."""
    if np.ndim(X) == 1:
        X = X.reshape(-1, 1)
    env = {
        'mul': np.multiply, 'add': np.add, 'sub': np.subtract,
        'div': lambda a, b: np.where(np.abs(b) > 1e-10, a / b, 1.0),
        'sqrt': lambda a: np.sqrt(np.abs(a)),
        'log': lambda a: np.where(np.abs(a) > 1e-10, np.log(np.abs(a)), 0.0),
        'exp': lambda a: np.exp(np.clip(a, -100, 100)),
    }
    for i, name in enumerate(var_names):
        env[name] = X[:, i]
    expr = template
    # Büyük indeksten küçüğe: __c10__ içindeki __c1__ yanlış eşleşmesin
    for i in range(len(c) - 1, -1, -1):
        expr = expr.replace(f'__c{i}__', repr(float(c[i])))
    return np.asarray(eval(expr, {'__builtins__': None}, env), dtype=float)


def optimize_constants(formula, X, y, var_names, snap_tol=0.001):
    """
    Üç aşamalı sabit optimizasyonu:
      1. Constant folding  — saf-sabit alt-ağaçları tek sayıya indir
      2. Scipy (Nelder-Mead) — kalan sabitleri MSE üzerinde optimize et
      3. Güzel sayı snap  — tanınan fizik/mat sabitine yuvarlama
    Döndürür: (optimize_formül, r2_opt)
    """
    if np.ndim(X) == 1:
        X = X.reshape(-1, 1)

    # 1. Constant folding
    folded = fold_constants(formula, var_names)

    # 2. Sabitleri çıkar, şablon oluştur
    consts = []

    def _extract(m):
        consts.append(float(m.group(1)))
        return f'__c{len(consts) - 1}__'

    template = _NUM_RE.sub(_extract, folded)

    def _r2_from_template(c_vals):
        try:
            yp = _eval_formula(template, c_vals, X, var_names)
            return float(r2_score(y, yp)) if np.all(np.isfinite(yp)) else -np.inf
        except Exception:
            return -np.inf

    # Sabit yoksa direkt değerlendir
    if not consts:
        return folded, round(_r2_from_template([]), 6)

    # Çok fazla sabit → scipy'ı atla (aşırı karmaşık formüller)
    if len(consts) > 25:
        return folded, round(_r2_from_template(consts), 6)

    # 3. Scipy Nelder-Mead optimizasyonu
    def _obj(c):
        try:
            yp = _eval_formula(template, c, X, var_names)
            return float(np.mean((y - yp) ** 2)) if np.all(np.isfinite(yp)) else 1e10
        except Exception:
            return 1e10

    res = minimize(
        _obj, np.array(consts, dtype=float), method='Nelder-Mead',
        options={'maxiter': 50_000, 'xatol': 1e-10, 'fatol': 1e-12, 'adaptive': True},
    )
    c_opt = res.x

    # 4. Tanınan fizik/mat sabitine yuvarlama
    c_final = c_opt.copy()
    for i, val in enumerate(c_opt):
        for nice_val, _ in _NICE_CONSTS:
            if nice_val != 0 and abs(val - nice_val) / abs(nice_val) < snap_tol:
                c_final[i] = nice_val
                break

    # 5. Formülü yeniden oluştur
    out = template
    for i in range(len(c_final) - 1, -1, -1):
        v = c_final[i]
        try:
            iv = int(v)
            s = str(iv) if (v == iv and abs(v) < 1e6) else f'{v:.6g}'
        except (ValueError, OverflowError):
            s = f'{v:.6g}'
        out = out.replace(f'__c{i}__', s)

    return out, round(_r2_from_template(c_final), 6)


# ─── Sympy Sadeleştirme ───────────────────────────────────────────────────────

def gplearn_to_sympy(formula_str, var_names, timeout_sec=8):
    """
    gplearn prefix formülünü → sympy ifadesi + LaTeX.

    eval() ile sympy namespace'inde değerlendirir.
    positive=True varsayımı sqrt(R²)→R gibi sadeleştirmeleri mümkün kılar.
    Zaman aşımı (Windows uyumlu threading) ile korunur.
    """
    import sympy as sp
    import threading

    result = {'expr': None, 'err': None}

    def _worker():
        try:
            syms = {v: sp.Symbol(v, positive=True) for v in var_names}
            ns = {
                '__builtins__': None,
                'mul': lambda a, b: a * b,
                'add': lambda a, b: a + b,
                'sub': lambda a, b: a - b,
                'div': lambda a, b: a / b,
                # Korumalı (protected) operatörler: gplearn negatif girdide
                # mutlak değer alır; sympy'da aynı davranışı taklit ediyoruz.
                'sqrt': lambda a: sp.sqrt(sp.Abs(a)),
                'log':  lambda a: sp.log(sp.Abs(a)),
                'exp':  sp.exp,
                **syms,
            }
            raw_expr = eval(formula_str, ns)
            result['expr'] = sp.simplify(raw_expr)
        except Exception as e:
            result['err'] = str(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)

    import sympy as sp
    if result['expr'] is not None:
        expr = result['expr']
        return str(expr), sp.latex(expr)
    # Zaman aşımı veya hata — ham string döndür
    return formula_str, formula_str


BENCHMARKS = {
    # ── Mevcut 7 benchmark ────────────────────────────────────────────────────
    "ohm": {
        "name": "Ohm Yasası",
        "true_formula": "V = I × R",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_ohm(n),
    },
    "kinetic": {
        "name": "Kinetik Enerji",
        "true_formula": "E = 0.5 × m × v²",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_kinetic(n),
    },
    "freefall": {
        "name": "Serbest Düşme",
        "true_formula": "d = 0.5 × g × t²",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_freefall(n),
    },
    "wave": {
        "name": "Dalga Hızı",
        "true_formula": "v = f × λ",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_wave(n),
    },
    "pendulum": {
        "name": "Sarkaç Periyodu",
        "true_formula": "T = 2π√(L/g)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_pendulum(n),
    },
    "gravity": {
        "name": "Newton Yerçekimi",
        "true_formula": "F = m1×m2/r²",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_gravity(n),
    },
    "capacitor": {
        "name": "Kondansatör Enerjisi",
        "true_formula": "E = 0.5 × C × V²",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_capacitor(n),
    },
    "resistor_parallel": {
        "name": "Paralel Direnç",
        "true_formula": "R = R1×R2/(R1+R2)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_parallel_r(n),
    },
    # ── Temel Mekanik ─────────────────────────────────────────────────────────
    "hooke": {
        "name": "Hooke Yasası",
        "true_formula": "F = k × x",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_hooke(n),
    },
    "momentum": {
        "name": "Momentum",
        "true_formula": "p = m × v",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_momentum(n),
    },
    "work": {
        "name": "Mekanik İş",
        "true_formula": "W = F × d × cos(θ)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_work(n),
        "function_set": _FS_TRIG,
    },
    "centripetal": {
        "name": "Merkezcil Kuvvet",
        "true_formula": "F = m × v² / r",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_centripetal(n),
    },
    "potential_energy": {
        "name": "Yerçekimi Potansiyel Enerjisi",
        "true_formula": "E = m × g × h",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_potential_energy(n),
    },
    # ── Elektrik-Elektronik ───────────────────────────────────────────────────
    "power_vi": {
        "name": "Elektrik Gücü (VI)",
        "true_formula": "P = V × I",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_power_vi(n),
    },
    "power_resistive": {
        "name": "Direnç Gücü",
        "true_formula": "P = I² × R",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_power_resistive(n),
    },
    "series_resistance": {
        "name": "Seri Direnç",
        "true_formula": "R = R1 + R2 + R3",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_series_resistance(n),
    },
    "capacitor_series": {
        "name": "Seri Kondansatör",
        "true_formula": "C = C1×C2/(C1+C2)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_capacitor_series(n),
    },
    "inductor_energy": {
        "name": "İndüktans Enerjisi",
        "true_formula": "E = 0.5 × L × I²",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_inductor_energy(n),
    },
    "resonance_freq": {
        "name": "Rezonans Frekansı",
        "true_formula": "f = 1/(2π√(LC))",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_resonance_freq(n),
    },
    "impedance_rl": {
        "name": "RL Empedansı",
        "true_formula": "Z = √(R² + (ωL)²)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_impedance_rl(n),
    },
    # ── Termodinamik ──────────────────────────────────────────────────────────
    "stefan_boltzmann": {
        "name": "Stefan-Boltzmann",
        "true_formula": "P = σ × A × T⁴",
        "difficulty": "Zor",
        "gen_func": lambda n: _gen_stefan_boltzmann(n),
    },
    "heat_transfer": {
        "name": "Isı Transferi",
        "true_formula": "Q = m × c × ΔT",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_heat_transfer(n),
    },
    "ideal_gas_temp": {
        "name": "İdeal Gaz Sıcaklığı",
        "true_formula": "T = PV/(nR)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_ideal_gas_temp(n),
    },
    # ── Optik ve Dalga ────────────────────────────────────────────────────────
    "snell": {
        "name": "Snell Yasası",
        "true_formula": "θ₂ = arcsin(n₁sin(θ₁)/n₂)",
        "difficulty": "Zor",
        "gen_func": lambda n: _gen_snell(n),
        "function_set": _FS_TRIG,
    },
    "energy_freq": {
        "name": "Planck Enerji-Frekans",
        "true_formula": "E = h × f",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_energy_freq(n),
    },
    "doppler": {
        "name": "Doppler Etkisi",
        "true_formula": "f_obs = f × v/(v+vs)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_doppler(n),
    },
    # ── Yerçekimi ve Astronomi ────────────────────────────────────────────────
    "escape_vel": {
        "name": "Kaçış Hızı",
        "true_formula": "v = √(2GM/r)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_escape_vel(n),
    },
    "orbital_vel": {
        "name": "Yörünge Hızı",
        "true_formula": "v = √(GM/r)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_orbital_vel(n),
    },
    # ── Matematiksel İlişkiler ────────────────────────────────────────────────
    "pythagorean": {
        "name": "Pisagor Teoremi",
        "true_formula": "c = √(a² + b²)",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_pythagorean(n),
    },
    "sphere_volume": {
        "name": "Küre Hacmi",
        "true_formula": "V = (4/3)π r³",
        "difficulty": "Kolay",
        "gen_func": lambda n: _gen_sphere_volume(n),
    },
    "cylinder_surface": {
        "name": "Silindir Yüzey Alanı",
        "true_formula": "A = 2πr(h + r)",
        "difficulty": "Orta",
        "gen_func": lambda n: _gen_cylinder_surface(n),
    },
}

# --- Veri üreticiler (ham, normalize edilmemiş) ---
def _gen_ohm(n):
    I = np.random.uniform(0.1, 10, n)
    R = np.random.uniform(1, 100, n)
    V = I * R
    return np.column_stack([I, R]), V, ["I", "R"]

def _gen_kinetic(n):
    m = np.random.uniform(0.5, 50, n)
    v = np.random.uniform(0.5, 30, n)
    E = 0.5 * m * v**2
    return np.column_stack([m, v]), E, ["m", "v"]

def _gen_freefall(n):
    t = np.random.uniform(0.1, 10, n)
    d = 0.5 * 9.81 * t**2
    return t.reshape(-1, 1), d, ["t"]

def _gen_wave(n):
    f = np.random.uniform(1, 100, n)
    lam = np.random.uniform(0.1, 10, n)
    v = f * lam
    return np.column_stack([f, lam]), v, ["f", "λ"]

def _gen_pendulum(n):
    L = np.random.uniform(0.1, 5, n)
    T = 2 * np.pi * np.sqrt(L / 9.81)
    return L.reshape(-1, 1), T, ["L"]

def _gen_gravity(n):
    m1 = np.random.uniform(1, 100, n)
    m2 = np.random.uniform(1, 100, n)
    r = np.random.uniform(1, 20, n)
    F = m1 * m2 / r**2  # G sabitini çıkardık, ölçek sorununu önlemek için
    return np.column_stack([m1, m2, r]), F, ["m1", "m2", "r"]

def _gen_capacitor(n):
    C = np.random.uniform(0.1, 10, n)
    V = np.random.uniform(1, 50, n)
    E = 0.5 * C * V**2
    return np.column_stack([C, V]), E, ["C", "V"]

def _gen_parallel_r(n):
    R1 = np.random.uniform(10, 1000, n)
    R2 = np.random.uniform(10, 1000, n)
    R = (R1 * R2) / (R1 + R2)
    return np.column_stack([R1, R2]), R, ["R1", "R2"]

# --- Yeni v0.5 veri üreticiler ---

def _gen_hooke(n):
    k = np.random.uniform(10, 500, n)
    x = np.random.uniform(0.01, 0.5, n)
    F = k * x
    return np.column_stack([k, x]), F, ["k", "x"]

def _gen_momentum(n):
    m = np.random.uniform(0.5, 100, n)
    v = np.random.uniform(0.1, 50, n)
    p = m * v
    return np.column_stack([m, v]), p, ["m", "v"]

def _gen_work(n):
    F = np.random.uniform(1, 500, n)
    d = np.random.uniform(0.1, 100, n)
    theta = np.random.uniform(0, np.pi / 3, n)  # 0..60 derece
    W = F * d * np.cos(theta)
    return np.column_stack([F, d, theta]), W, ["F", "d", "theta"]

def _gen_centripetal(n):
    m = np.random.uniform(0.5, 50, n)
    v = np.random.uniform(1, 30, n)
    r = np.random.uniform(0.5, 20, n)
    F = m * v**2 / r
    return np.column_stack([m, v, r]), F, ["m", "v", "r"]

def _gen_potential_energy(n):
    m = np.random.uniform(0.5, 100, n)
    h = np.random.uniform(0.1, 50, n)
    E = m * 9.81 * h
    return np.column_stack([m, h]), E, ["m", "h"]

def _gen_power_vi(n):
    V = np.random.uniform(1, 240, n)
    I = np.random.uniform(0.01, 20, n)
    P = V * I
    return np.column_stack([V, I]), P, ["V", "I"]

def _gen_power_resistive(n):
    I = np.random.uniform(0.01, 20, n)
    R = np.random.uniform(1, 1000, n)
    P = I**2 * R
    return np.column_stack([I, R]), P, ["I", "R"]

def _gen_series_resistance(n):
    R1 = np.random.uniform(10, 500, n)
    R2 = np.random.uniform(10, 500, n)
    R3 = np.random.uniform(10, 500, n)
    R = R1 + R2 + R3
    return np.column_stack([R1, R2, R3]), R, ["R1", "R2", "R3"]

def _gen_capacitor_series(n):
    C1 = np.random.uniform(1e-6, 1e-3, n)
    C2 = np.random.uniform(1e-6, 1e-3, n)
    C = (C1 * C2) / (C1 + C2)
    return np.column_stack([C1, C2]), C, ["C1", "C2"]

def _gen_inductor_energy(n):
    L = np.random.uniform(0.001, 1, n)
    I = np.random.uniform(0.1, 10, n)
    E = 0.5 * L * I**2
    return np.column_stack([L, I]), E, ["L", "I"]

def _gen_resonance_freq(n):
    L = np.random.uniform(0.001, 1, n)
    C = np.random.uniform(1e-6, 1e-3, n)
    f = 1 / (2 * np.pi * np.sqrt(L * C))
    return np.column_stack([L, C]), f, ["L", "C"]

def _gen_impedance_rl(n):
    R = np.random.uniform(1, 1000, n)
    X = np.random.uniform(1, 1000, n)  # reaktans = ωL
    Z = np.sqrt(R**2 + X**2)
    return np.column_stack([R, X]), Z, ["R", "X"]

def _gen_stefan_boltzmann(n):
    T = np.random.uniform(300, 3000, n)
    sigma = 5.67e-8
    P = sigma * T**4
    return T.reshape(-1, 1), P, ["T"]

def _gen_heat_transfer(n):
    k = np.random.uniform(0.1, 400, n)
    A = np.random.uniform(0.01, 10, n)
    dT = np.random.uniform(1, 500, n)
    dx = np.random.uniform(0.001, 0.5, n)
    Q = k * A * dT / dx
    return np.column_stack([k, A, dT, dx]), Q, ["k", "A", "dT", "dx"]

def _gen_ideal_gas_temp(n):
    P = np.random.uniform(1e4, 1e6, n)
    V = np.random.uniform(0.001, 10, n)
    n_mol = np.random.uniform(0.1, 100, n)
    R_gas = 8.314
    T = (P * V) / (n_mol * R_gas)
    return np.column_stack([P, V, n_mol]), T, ["P", "V", "n"]

def _gen_snell(n):
    n1 = np.random.uniform(1.0, 2.5, n)
    theta1 = np.random.uniform(0.05, np.pi / 3, n)
    n2 = np.random.uniform(1.0, 2.5, n)
    # n1*sin(theta1) = n2*sin(theta2) → theta2 = arcsin(n1/n2 * sin(theta1))
    ratio = (n1 / n2) * np.sin(theta1)
    ratio = np.clip(ratio, -1, 1)
    theta2 = np.arcsin(ratio)
    return np.column_stack([n1, theta1, n2]), theta2, ["n1", "theta1", "n2"]

def _gen_energy_freq(n):
    # Normalized units: f in THz, E in 10^-22 J → constant becomes 6.626 (in range)
    f_THz = np.random.uniform(100, 10000, n)           # f in THz
    h_norm = 6.626                                      # h / (1e-22 J * 1e12 Hz) = 6.626
    E_norm = h_norm * f_THz                             # E in units of 1e-34 J*Hz
    return f_THz.reshape(-1, 1), E_norm, ["f_THz"]

def _gen_doppler(n):
    f0 = np.random.uniform(100, 10000, n)
    v_s = np.random.uniform(1, 50, n)   # kaynak hızı (ses < 340 m/s)
    v_sound = 343.0
    f = f0 * v_sound / (v_sound - v_s)
    return np.column_stack([f0, v_s]), f, ["f0", "vs"]

def _gen_escape_vel(n):
    M = np.random.uniform(1e20, 2e30, n)
    r = np.random.uniform(1e6, 1e11, n)
    G = 6.674e-11
    v = np.sqrt(2 * G * M / r)
    return np.column_stack([M, r]), v, ["M", "r"]

def _gen_orbital_vel(n):
    M = np.random.uniform(1e20, 2e30, n)
    r = np.random.uniform(1e6, 1e11, n)
    G = 6.674e-11
    v = np.sqrt(G * M / r)
    return np.column_stack([M, r]), v, ["M", "r"]

def _gen_pythagorean(n):
    a = np.random.uniform(1, 100, n)
    b = np.random.uniform(1, 100, n)
    c = np.sqrt(a**2 + b**2)
    return np.column_stack([a, b]), c, ["a", "b"]

def _gen_sphere_volume(n):
    r = np.random.uniform(0.1, 10, n)
    V = (4 / 3) * np.pi * r**3
    return r.reshape(-1, 1), V, ["r"]

def _gen_cylinder_surface(n):
    r = np.random.uniform(0.1, 10, n)
    h = np.random.uniform(0.1, 20, n)
    A = 2 * np.pi * r * (h + r)
    return np.column_stack([r, h]), A, ["r", "h"]


def discover(X, y, var_names, pop=3000, gens=50, verbose=True, function_set=None):
    """Tek bir keşif çalıştırması."""
    if function_set is None:
        function_set = _FS_STANDARD
    model = SymbolicRegressor(
        population_size=pop,
        generations=gens,
        tournament_size=20,
        stopping_criteria=1e-8,
        p_crossover=0.70,
        p_subtree_mutation=0.10,
        p_hoist_mutation=0.15,       # ↑ hoist prune ağacı kısaltır
        p_point_mutation=0.05,       # toplam = 1.0
        max_samples=0.8,             # ↓ daha agresif generalizasyon
        verbose=1 if verbose else 0,
        parsimony_coefficient=0.003, # ↑ 6× artış — MSE ölçeğinde bloat'a karşı etkili
        random_state=42,
        function_set=function_set,
        metric='mse',
        n_jobs=1,
        init_depth=(2, 4),           # sığ başlangıç; mutation max_depth=8 olur
        const_range=(-10.0, 10.0),  # ↑ geniş sabit aralığı (4.905 doğrudan bulunabilir)
    )
    
    t0 = time.time()
    model.fit(X, y)
    elapsed = time.time() - t0
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    raw = str(model._program)
    display = raw
    for i, name in enumerate(var_names):
        display = display.replace(f"X{i}", name)

    # Sabit optimizasyonu post-processing
    X_2d = X if X.ndim == 2 else X.reshape(-1, 1)
    formula_opt, r2_opt = optimize_constants(display, X_2d, y, var_names)

    # Sympy sadeleştirme (optimize edilmiş formül üzerinde)
    formula_sympy, formula_latex = gplearn_to_sympy(formula_opt, var_names)

    return {
        "formula": display,
        "formula_opt": formula_opt,
        "formula_sympy": formula_sympy,
        "formula_latex": formula_latex,
        "r2": round(r2, 6),
        "r2_opt": r2_opt,
        "rmse": round(float(rmse), 6),
        "complexity": model._program.length_,
        "seconds": round(elapsed, 2),
        "y_true": y.tolist(),
        "y_pred": y_pred.tolist(),
    }


def generate_discovery_report(results_list, output_path="discovery_report.md"):
    """
    Keşif sonuçlarından okunabilir Markdown raporu üretir.

    Args:
        results_list : run_all() veya discover() çağrılarından gelen dict listesi.
                       Her dict'te en az şunlar olmalı:
                       benchmark, true_formula, difficulty, formula_sympy, r2_opt, seconds
        output_path  : Kaydedilecek .md dosyasının yolu
    """
    total = len(results_list)
    perfect = sum(1 for r in results_list if r.get("r2_opt", 0) > 0.99)
    good    = sum(1 for r in results_list if 0.95 < r.get("r2_opt", 0) <= 0.99)
    fail    = total - perfect - good
    avg_r2  = np.mean([r.get("r2_opt", 0) for r in results_list]) if results_list else 0

    lines = []
    lines.append("# GENESIS — Otomatik Fizik Yasası Keşif Raporu")
    lines.append("")
    lines.append(f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Versiyon:** v0.5")
    lines.append("")
    lines.append("## Özet")
    lines.append("")
    lines.append(f"| Metrik | Değer |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Toplam benchmark | {total} |")
    lines.append(f"| Mükemmel keşif (R²>0.99) | {perfect} |")
    lines.append(f"| İyi keşif (0.95<R²≤0.99) | {good} |")
    lines.append(f"| Başarısız (R²≤0.95) | {fail} |")
    lines.append(f"| Ortalama R²(opt) | {avg_r2:.4f} |")
    lines.append("")
    lines.append("## Detaylı Sonuçlar")
    lines.append("")
    lines.append("| # | Yasa | Zorluk | Gerçek Formül | Keşfedilen (Sympy) | R²(opt) | Süre (s) |")
    lines.append("|---|------|--------|---------------|-------------------|---------|----------|")

    for i, r in enumerate(results_list, 1):
        r2 = r.get("r2_opt", r.get("r2", 0))
        marker = "✅" if r2 > 0.99 else "🔶" if r2 > 0.95 else "❌"
        name     = r.get("benchmark", r.get("name", "?"))
        diff     = r.get("difficulty", "?")
        true_f   = r.get("true_formula", "?")
        sympy_f  = r.get("formula_sympy", r.get("formula", "?"))
        secs     = r.get("seconds", 0)
        lines.append(f"| {i} | {marker} {name} | {diff} | `{true_f}` | `{sympy_f}` | {r2:.4f} | {secs:.1f} |")

    lines.append("")
    lines.append("## Zorluk Bazlı Analiz")
    lines.append("")
    difficulty_groups = {}
    for r in results_list:
        d = r.get("difficulty", "Bilinmiyor")
        difficulty_groups.setdefault(d, []).append(r.get("r2_opt", r.get("r2", 0)))

    for diff_level in ["Kolay", "Orta", "Zor", "Bilinmiyor"]:
        if diff_level not in difficulty_groups:
            continue
        vals = difficulty_groups[diff_level]
        avg = np.mean(vals)
        perfect_cnt = sum(1 for v in vals if v > 0.99)
        lines.append(f"**{diff_level}** — {len(vals)} denklem, ortalama R²={avg:.4f}, mükemmel={perfect_cnt}/{len(vals)}")
        lines.append("")

    # Görselleştirmeler bölümü — plots/ klasöründeki grafikler varsa ekle
    plots_dir = os.path.join(os.path.dirname(output_path) or ".", "plots")
    has_plots = os.path.isdir(plots_dir)

    lines.append("## Görselleştirmeler")
    lines.append("")
    if has_plots:
        lines.append("Grafikler `plots/` klasöründe bulunmaktadır.")
        lines.append("")
        lines.append("### Benchmark Doğruluk Skorları")
        lines.append("![Accuracy](plots/accuracy.png)")
        lines.append("")
        lines.append("### Karmaşıklık vs Doğruluk")
        lines.append("![Complexity vs Accuracy](plots/complexity_accuracy.png)")
        lines.append("")
        lines.append("### Zorluk Seviyesine Göre Keşif Süresi")
        lines.append("![Discovery Time](plots/time.png)")
    else:
        lines.append("> Grafik oluşturmak için: `python genesis_viz.py results_v2.json`")
        lines.append("> Üretilen grafikler buraya otomatik eklenir.")
    lines.append("")

    lines.append("---")
    lines.append("*Bu rapor GENESIS tarafından otomatik üretilmiştir.*")

    report_text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n  Rapor kaydedildi → {output_path}")
    return report_text


def run_all(difficulty=None, keys=None, pop=2000, gens=40, output_json="results_v2.json"):
    """
    Benchmark'ları çalıştırır ve sonuçları kaydeder.

    Args:
        difficulty   : None (hepsi) | "Kolay" | "Orta" | "Zor" — zorluk filtresi
        keys         : None (hepsi) veya çalıştırılacak benchmark key listesi
        pop / gens   : gplearn popülasyon ve nesil sayısı
        output_json  : JSON çıktı dosyası
    """
    results = []

    # Çalıştırılacak benchmark'ları belirle
    if keys is not None:
        run_keys = [k for k in keys if k in BENCHMARKS]
    elif difficulty is not None:
        run_keys = [k for k, v in BENCHMARKS.items() if v["difficulty"] == difficulty]
    else:
        run_keys = list(BENCHMARKS.keys())

    print("=" * 70)
    print(f"  GENESIS v0.5 — Fizik Yasası Keşif Motoru")
    if difficulty:
        print(f"  Filtre: difficulty={difficulty}")
    print(f"  Toplam: {len(run_keys)} benchmark")
    print("=" * 70)

    for idx, key in enumerate(run_keys, 1):
        bm = BENCHMARKS[key]
        print(f"\n[{idx}/{len(run_keys)}] >>> HEDEF: {bm['name']}  |  Gerçek: {bm['true_formula']}  |  Zorluk: {bm['difficulty']}")
        print("-" * 70)

        try:
            X, y, vnames = bm["gen_func"](500)
            fs = bm.get("function_set", None)
            r = discover(X, y, vnames, pop=pop, gens=gens, verbose=True, function_set=fs)
            r["benchmark"] = bm["name"]
            r["true_formula"] = bm["true_formula"]
            r["difficulty"] = bm["difficulty"]
            r["key"] = key
        except Exception as e:
            print(f"  HATA: {e}")
            r = {
                "benchmark": bm["name"], "true_formula": bm["true_formula"],
                "difficulty": bm["difficulty"], "key": key,
                "formula": "ERROR", "formula_opt": "ERROR",
                "formula_sympy": "ERROR", "formula_latex": "",
                "r2": 0.0, "r2_opt": 0.0, "rmse": 0.0,
                "complexity": 0, "seconds": 0.0,
                "error": str(e),
            }

        results.append(r)

        improved = r.get("formula_opt", "") != r.get("formula", "")
        print(f"\n  Ham formül  : {r['formula'][:120]}")
        if improved:
            print(f"  Sabit opt.  : {r['formula_opt']}")
        print(f"  Sympy       : {r['formula_sympy']}")
        r2_display = r["r2_opt"] if improved else r["r2"]
        label = "R²(opt)" if improved else "R²"
        print(f"  {label} = {r2_display}  |  RMSE = {r['rmse']}  |  Süre = {r['seconds']}s")

        # Tamamlanan benchmark'ları anında kaydet
        report = {
            "project": "GENESIS",
            "version": "0.5.0",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total": len(results),
                "avg_r2": round(float(np.mean([x["r2_opt"] for x in results])), 4),
                "perfect": sum(1 for x in results if x["r2_opt"] > 0.99),
                "simplified": sum(1 for x in results if x.get("formula_opt", "") != x.get("formula", "")),
            }
        }
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 110)
    print("  SONUÇ TABLOSU")
    print("=" * 110)
    print(f"  {'Yasa':<25} {'Gerçek':<22} {'R²(opt)':<10} {'Sympy Formül'}")
    print("-" * 110)
    for r in results:
        r2_show = r["r2_opt"]
        marker = "✅" if r2_show > 0.99 else "🔶" if r2_show > 0.95 else "❌"
        sympy_f = r["formula_sympy"]
        print(f"  {marker} {r['benchmark']:<23} {r['true_formula']:<22} {r2_show:<10} {sympy_f[:55]}")
    print("=" * 110)
    print(f"  Ortalama R²(opt): {report['summary']['avg_r2']}")
    print(f"  Mükemmel keşif (R²>0.99): {report['summary']['perfect']}/{report['summary']['total']}")
    print(f"  Sabit opt. ile basitleştirilen: {report['summary']['simplified']}/{report['summary']['total']}")
    print(f"\n  Sonuçlar kaydedildi → {output_json}")

    # Markdown raporu oluştur
    report_md_path = output_json.replace(".json", "_report.md")
    generate_discovery_report(results, output_path=report_md_path)

    return report


# ─── CSV Desteği ─────────────────────────────────────────────────────────────

def discover_from_csv(filepath, target_column, max_rows=1000, pop=2000, gens=40, robust=False):
    """
    Kullanıcının kendi CSV dosyasından formül keşfeder.

    Args:
        filepath      : CSV dosyasının yolu
        target_column : Tahmin edilecek sütunun adı (y)
        max_rows      : Kullanılacak maksimum satır sayısı
        pop / gens    : gplearn popülasyon boyutu ve nesil sayısı
    """
    print("=" * 70)
    print("  GENESIS — CSV Keşif Modu")
    print("=" * 70)

    # Veriyi yükle
    df = pd.read_csv(filepath)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df = df[numeric_cols].dropna()

    if target_column not in df.columns:
        avail = ", ".join(df.columns)
        raise ValueError(f"'{target_column}' sütunu bulunamadı. Mevcut sayısal sütunlar: {avail}")

    if len(df) > max_rows:
        df = df.sample(max_rows, random_state=42).reset_index(drop=True)

    feature_cols = [c for c in df.columns if c != target_column]
    if not feature_cols:
        raise ValueError("Girdi değişkeni yok — target_column dışında en az bir sayısal sütun gerekli.")

    X = df[feature_cols].values
    y = df[target_column].values
    var_names = feature_cols

    print(f"\n  Dosya    : {filepath}")
    print(f"  Satır    : {len(df)}")
    print(f"  Girdi    : {var_names}")
    print(f"  Hedef    : {target_column}")
    print("-" * 70)

    if robust:
        result = discover_robust(X, y, var_names, pop=pop, gens=gens, verbose=True)
    else:
        result = discover(X, y, var_names, pop=pop, gens=gens, verbose=True)

    # Ek meta bilgi
    result["source"]    = filepath
    result["target"]    = target_column
    result["n_samples"] = len(df)
    result["variables"] = var_names

    print(f"\n  Ham formül  : {result['formula']}")
    if result["formula_opt"] != result["formula"]:
        print(f"  Sabit opt.  : {result['formula_opt']}")
    print(f"  Sympy       : {result['formula_sympy']}")
    print(f"  R²(opt)     = {result['r2_opt']}  |  RMSE = {result['rmse']}  |  Süre = {result['seconds']}s")

    # Sonucu kaydet
    stem = filepath.rsplit(".", 1)[0]
    out_path = f"{stem}_genesis_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Sonuç kaydedildi → {out_path}")

    return result


# ─── Brute-Force Keşif ───────────────────────────────────────────────────────

def _bf_build_bases(X, var_names):
    """
    Temel fonksiyon sözlüğü: tek/çift değişken güç ve oran terimleri.
    Döner: [(name, values_array), ...]  — sadece finite ve std > 0 olanlar.
    Index 0 her zaman sabit terim (intercept).
    """
    n = X.shape[0]
    bases = [('1', np.ones(n))]

    def _add(name, vals):
        arr = np.asarray(vals, dtype=float)
        if np.all(np.isfinite(arr)) and np.std(arr) > 1e-12:
            bases.append((name, arr))

    # Tek değişken terimleri
    for i, vn in enumerate(var_names):
        xi = X[:, i]
        _add(vn,            xi)
        _add(f'{vn}**2',    xi ** 2)
        _add(f'{vn}**3',    xi ** 3)
        with np.errstate(all='ignore'):
            _add(f'sqrt({vn})', np.where(xi >= 0, np.sqrt(xi), np.nan))
            _add(f'1/{vn}',     np.where(np.abs(xi) > 1e-10, 1.0 / xi, np.nan))
            _add(f'1/{vn}**2',  np.where(np.abs(xi) > 1e-10, 1.0 / xi**2, np.nan))

    # Çift değişken terimleri (i < j, simetrik olanlar bir kez)
    for i, j in itertools.combinations(range(len(var_names)), 2):
        xi, xj = X[:, i], X[:, j]
        ni, nj = var_names[i], var_names[j]
        _add(f'{ni}*{nj}',       xi * xj)
        _add(f'{ni}**2*{nj}',    xi**2 * xj)
        _add(f'{ni}*{nj}**2',    xi * xj**2)
        _add(f'{ni}**2*{nj}**2', xi**2 * xj**2)
        with np.errstate(all='ignore'):
            _add(f'{ni}/{nj}',    np.where(np.abs(xj) > 1e-10, xi / xj, np.nan))
            _add(f'{nj}/{ni}',    np.where(np.abs(xi) > 1e-10, xj / xi, np.nan))
            _add(f'{ni}**2/{nj}', np.where(np.abs(xj) > 1e-10, xi**2 / xj, np.nan))
            _add(f'{ni}/{nj}**2', np.where(np.abs(xj) > 1e-10, xi / xj**2, np.nan))

    return bases


def _bf_coef_str(c):
    """
    Katsayıyı _NICE_CONSTS'a snap yap; snap yoksa 5 basamaklı yaz.
    Döner: '+2*pi' / '-9.81' gibi işaretli string; c≈0 ise None.
    """
    if abs(c) < 1e-12:
        return None
    sign = '+' if c >= 0 else '-'
    ac = abs(c)
    for val, name in _NICE_CONSTS:
        if abs(ac - val) / (val + 1e-12) < 0.005:
            return f'{sign}{name}'
    return f'{c:+.5g}'


def brute_force_discover(X, y, var_names, max_complexity=5):
    """
    Ham kuvvet sembolik regresyon.

    1-2 değişkenli tüm temel fonksiyon kombinasyonlarını dener
    (doğrusal kombinasyon modeli). Sabitleri np.linalg.lstsq ile analitik çözer.

    Temel fonksiyonlar:
      Tek değişken : x, x², x³, sqrt(x), 1/x, 1/x²
      İki değişken : x*y, x²*y, x*y², x²*y², x/y, y/x, x²/y, x/y²

    Args:
        X              : (n, m) veya (n,) girdi
        y              : (n,) hedef
        var_names      : değişken adları
        max_complexity : formüldeki maks terim sayısı (intercept hariç, ≤5 önerilir)

    Returns:
        discover() ile aynı formatlı dict
    """
    t0 = time.time()
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).ravel()
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    var_names = list(var_names)[:X.shape[1]]

    bases   = _bf_build_bases(X, var_names)
    n_bases = len(bases)

    # index 0 = intercept — her kombinasyona otomatik eklenir
    free_idx  = list(range(1, n_bases))
    max_terms = min(max_complexity, len(free_idx))

    best_score = -np.inf
    best_coef  = None
    best_cols  = None

    for size in range(1, max_terms + 1):
        for combo in itertools.combinations(free_idx, size):
            cols = [0] + list(combo)
            A = np.column_stack([bases[i][1] for i in cols])
            try:
                coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
            except Exception:
                continue
            yp = A @ coef
            if not np.all(np.isfinite(yp)):
                continue
            r2 = float(r2_score(y, yp))
            # Parsimony: daha kısa formüle hafif tercih
            if r2 - 0.002 * size > best_score:
                best_score = r2 - 0.002 * size
                best_coef  = coef
                best_cols  = cols

    elapsed = round(time.time() - t0, 2)

    if best_coef is None:
        return {
            'formula': '?', 'formula_opt': '?',
            'formula_sympy': '?', 'formula_latex': '?',
            'r2': -1.0, 'r2_opt': -1.0, 'rmse': float('nan'),
            'complexity': 0, 'seconds': elapsed,
            'y_true': y.tolist(), 'y_pred': [],
        }

    A_best = np.column_stack([bases[i][1] for i in best_cols])
    y_pred = A_best @ best_coef
    r2_val = float(r2_score(y, y_pred))
    rmse   = float(np.sqrt(mean_squared_error(y, y_pred)))

    # Formül string'ini oluştur
    parts = []
    for k, col_idx in enumerate(best_cols):
        c    = best_coef[k]
        name = bases[col_idx][0]
        cs   = _bf_coef_str(c)
        if cs is None:
            continue
        if name == '1':
            parts.append(cs)
        elif abs(abs(c) - 1.0) < 1e-4:
            parts.append(f'{"-" if c < 0 else ""}{name}')
        else:
            parts.append(f'{cs}*{name}')

    formula = ' + '.join(parts).replace('+ -', '- ').replace('+-', '-')
    formula = formula.lstrip(' +') or '0'

    complexity = len(best_cols) - 1  # intercept hariç

    formula_sympy, formula_latex = gplearn_to_sympy(formula, var_names)

    return {
        'formula':       formula,
        'formula_opt':   formula,
        'formula_sympy': formula_sympy,
        'formula_latex': formula_latex,
        'r2':            round(r2_val, 6),
        'r2_opt':        round(r2_val, 6),
        'rmse':          round(rmse, 6),
        'complexity':    complexity,
        'seconds':       elapsed,
        'y_true':        y.tolist(),
        'y_pred':        y_pred.tolist(),
    }


# ─── Robust Keşif (Çok Motorlu Pareto) ──────────────────────────────────────

def discover_robust(X, y, var_names, pop=2000, gens=40, verbose=True):
    """
    Aynı veriyi 3 farklı function_set ile dener; Pareto optimal sonucu döner.

    Motorlar:
      no_div   — ['add', 'sub', 'mul', psqrt]          (bölme yok → overfitting azalır)
      standard — ['add', 'sub', 'mul', pdiv, psqrt]    (varsayılan)
      extended — ['add', 'sub', 'mul', pdiv, psqrt, plog, pexp]  (log/exp gerekirse)

    Pareto seçimi:
      R² > 0.99 olan en basit formül (min complexity)
      Hiçbiri 0.99 geçmezse en yüksek R²
    """
    fs_configs = [
        ("no_div",   ['add', 'sub', 'mul', psqrt]),
        ("standard", _FS_STANDARD),
        ("extended", ['add', 'sub', 'mul', pdiv, psqrt, plog, pexp]),
    ]

    results = []
    for name, fs in fs_configs:
        if verbose:
            print(f"\n  ── Motor: {name} ──")
        r = discover(X, y, var_names, pop=pop, gens=gens,
                     verbose=verbose, function_set=fs)
        r["engine"] = name
        results.append(r)

    good = [r for r in results if r["r2_opt"] > 0.99]
    best = min(good, key=lambda r: r["complexity"]) if good \
        else max(results, key=lambda r: r["r2_opt"])

    best["all_results"] = [
        {"engine": r["engine"], "r2_opt": r["r2_opt"],
         "complexity": r["complexity"], "formula_sympy": r["formula_sympy"]}
        for r in results
    ]

    if verbose:
        print(f"\n  === PARETO SEÇİMİ ===")
        for r in results:
            marker = "→" if r["engine"] == best["engine"] else " "
            print(f"  {marker} {r['engine']:10s}: R²={r['r2_opt']:.6f}  "
                  f"karmaşıklık={r['complexity']:3d}  "
                  f"formül={str(r['formula_sympy'])[:60]}")

    return best


if __name__ == "__main__":
    args = sys.argv[1:]
    robust = "--robust" in args
    if robust:
        args = [a for a in args if a != "--robust"]

    if len(args) == 2:
        # CSV modu:  python genesis_v2.py data.csv target [--robust]
        discover_from_csv(args[0], args[1], robust=robust)
    else:
        # Benchmark modu:  python genesis_v2.py
        run_all()
