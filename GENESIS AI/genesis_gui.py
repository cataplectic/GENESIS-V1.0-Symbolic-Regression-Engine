"""
GENESIS — Physics Law Discovery Engine
Masaustu Uygulamasi v1.0  |  PyQt6
Calistir: python genesis_gui.py
"""

import sys
import os
import json
import math
import traceback
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QComboBox,
    QRadioButton, QButtonGroup, QFileDialog, QSplitter,
    QFrame, QMessageBox, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextBrowser, QStatusBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# ─── Benchmark listesi (genesis_v2'den kopyalandı) ────────────────────────────

BENCHMARKS = [
    ("ohm",               "Ohm Yasası  (V = I·R)",               "Kolay"),
    ("kinetic",           "Kinetik Enerji  (E = ½mv²)",           "Kolay"),
    ("freefall",          "Serbest Düşme  (d = ½gt²)",            "Kolay"),
    ("wave",              "Dalga Hızı  (v = f·λ)",                "Kolay"),
    ("capacitor",         "Kondansatör Enerjisi  (E = ½CV²)",     "Kolay"),
    ("hooke",             "Hooke Yasası  (F = kx)",               "Kolay"),
    ("momentum",          "Momentum  (p = mv)",                   "Kolay"),
    ("potential_energy",  "Potansiyel Enerji  (E = mgh)",         "Kolay"),
    ("power_vi",          "Elektrik Gücü  (P = VI)",              "Kolay"),
    ("power_resistive",   "Direnç Gücü  (P = I²R)",               "Kolay"),
    ("series_resistance", "Seri Direnç  (R = R1+R2+R3)",          "Kolay"),
    ("inductor_energy",   "İndüktans Enerjisi  (E = ½LI²)",       "Kolay"),
    ("heat_transfer",     "Isı Transferi  (Q = kA·ΔT/Δx)",       "Kolay"),
    ("energy_freq",       "Planck  (E = hf)",                     "Kolay"),
    ("pythagorean",       "Pisagor  (c = √(a²+b²))",             "Kolay"),
    ("sphere_volume",     "Küre Hacmi  (V = 4/3·π·r³)",          "Kolay"),
    ("pendulum",          "Sarkaç  (T = 2π√(L/g))",              "Orta"),
    ("gravity",           "Newton Yerçekimi  (F = Gm₁m₂/r²)",   "Orta"),
    ("resistor_parallel", "Paralel Direnç  (R = R1R2/(R1+R2))",  "Orta"),
    ("work",              "Mekanik İş  (W = F·d·cosθ)",          "Orta"),
    ("centripetal",       "Merkezcil Kuvvet  (F = mv²/r)",       "Orta"),
    ("capacitor_series",  "Seri Kondansatör  (C = C1C2/(C1+C2))","Orta"),
    ("resonance_freq",    "Rezonans Frekansı  (f = 1/2π√LC)",   "Orta"),
    ("impedance_rl",      "RL Empedansı  (Z = √(R²+X²))",       "Orta"),
    ("ideal_gas_temp",    "İdeal Gaz Sıcaklığı  (T = PV/nR)",   "Orta"),
    ("doppler",           "Doppler Etkisi  (f' = f·v/(v-vs))",   "Orta"),
    ("escape_vel",        "Kaçış Hızı  (v = √(2GM/r))",         "Orta"),
    ("orbital_vel",       "Yörünge Hızı  (v = √(GM/r))",        "Orta"),
    ("cylinder_surface",  "Silindir Yüzeyi  (A = 2πr(h+r))",    "Orta"),
    ("stefan_boltzmann",  "Stefan-Boltzmann  (P = σT⁴)",         "Zor"),
    ("snell",             "Snell Yasası  (n₁sinθ₁ = n₂sinθ₂)",  "Zor"),
]

# ─── Sabitler ─────────────────────────────────────────────────────────────────

BG     = "#1a1a2e"
PANEL  = "#16213e"
ACCENT = "#0f3460"
RED    = "#e94560"
TEXT   = "#eaeaea"
GREEN  = "#00b894"
YELLOW = "#fdcb6e"
BLUE   = "#40c4ff"
MONO   = "Consolas, 'Courier New', monospace"

RESULTS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_v2.json")

# ─── Koyu Tema QSS ────────────────────────────────────────────────────────────

QSS = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: {MONO};
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {ACCENT};
    background-color: {PANEL};
}}
QTabBar::tab {{
    background-color: {ACCENT};
    color: {TEXT};
    padding: 8px 24px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
}}
QTabBar::tab:selected {{
    background-color: {RED};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{ background-color: #1a4070; }}
QGroupBox {{
    border: 1px solid {ACCENT};
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    color: {YELLOW};
    font-weight: bold;
    font-size: 11px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}
QPushButton {{
    background-color: {ACCENT};
    color: {TEXT};
    border: none;
    border-radius: 4px;
    padding: 7px 14px;
}}
QPushButton:hover {{ background-color: #1a5090; }}
QPushButton:disabled {{
    background-color: #2a2a44;
    color: #555577;
}}
QPushButton#btn_discover {{
    background-color: {GREEN};
    color: #051a10;
    font-weight: bold;
    font-size: 16px;
    padding: 12px 24px;
    border-radius: 6px;
    min-height: 44px;
}}
QPushButton#btn_discover:hover {{ background-color: #00d9a0; }}
QPushButton#btn_discover:disabled {{
    background-color: #1a4030;
    color: #336644;
}}
QSpinBox, QComboBox {{
    background-color: {ACCENT};
    color: {TEXT};
    border: 1px solid #2a5080;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: {MONO};
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {PANEL};
    color: {TEXT};
    selection-background-color: {RED};
}}
QRadioButton {{ spacing: 8px; }}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 2px solid {ACCENT};
}}
QRadioButton::indicator:checked {{
    background-color: {RED};
    border-color: {RED};
}}
QSplitter::handle {{ background-color: {ACCENT}; width: 2px; }}
QTableWidget {{
    background-color: {PANEL};
    color: {TEXT};
    border: 1px solid {ACCENT};
    gridline-color: #1e2a4e;
    border-radius: 4px;
    font-size: 12px;
}}
QTableWidget::item {{ padding: 4px 8px; }}
QTableWidget::item:selected {{
    background-color: {RED};
    color: white;
}}
QHeaderView::section {{
    background-color: {ACCENT};
    color: {YELLOW};
    padding: 6px 8px;
    border: none;
    font-weight: bold;
    font-size: 12px;
}}
QTextBrowser {{
    background-color: {PANEL};
    color: {TEXT};
    border: 1px solid {ACCENT};
    border-radius: 4px;
    font-size: 13px;
    padding: 8px;
}}
QStatusBar {{
    background-color: {ACCENT};
    color: {TEXT};
    font-size: 12px;
    padding: 3px 8px;
}}
QScrollBar:vertical {{
    background: {BG}; width: 10px; border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT}; border-radius: 5px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {BG}; height: 10px; border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {ACCENT}; border-radius: 5px; min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""

# ─── Yardımcı: JSON okuma/yazma ───────────────────────────────────────────────

def _load_json_results():
    if not os.path.exists(RESULTS_JSON):
        return []
    try:
        with open(RESULTS_JSON, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('results', data) if isinstance(data, dict) else data
    except Exception:
        return []

def _save_json_results(results_list):
    # y_true/y_pred listelerini JSON'a yazıyoruz — boyutu küçültmek için kırp
    clean = []
    for r in results_list:
        row = {}
        for k, v in r.items():
            if k in ('y_true', 'y_pred'):
                arr = v[:50] if isinstance(v, list) else v  # sadece 50 nokta sakla
                row[k] = arr
            elif isinstance(v, (np.ndarray, np.integer, np.floating)):
                row[k] = v.tolist() if hasattr(v, 'tolist') else float(v)
            else:
                row[k] = v
        clean.append(row)
    with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
        json.dump({'results': clean}, f, ensure_ascii=False, indent=2, default=str)

# ─── Yardımcı: metrik kutusu ─────────────────────────────────────────────────

def _metric_box(label_text, value_color):
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setStyleSheet(
        f"background-color: {PANEL}; border: 1px solid {ACCENT}; border-radius: 6px;")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 10, 12, 10)
    lay.setSpacing(2)
    val = QLabel("—")
    val.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val.setStyleSheet(
        f"color: {value_color}; font-size: 20px; font-weight: bold; "
        f"background: transparent; border: none;")
    cap = QLabel(label_text)
    cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
    cap.setStyleSheet("color: #888; font-size: 10px; background: transparent; border: none;")
    lay.addWidget(val)
    lay.addWidget(cap)
    return frame, val

# ─── Scatter Canvas ───────────────────────────────────────────────────────────

class ScatterCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(figsize=(5, 3.2), facecolor=BG)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._init_axes()

    def _init_axes(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=PANEL)
        ax.set_title("Keşif sonrası grafik burada görünecek", color="#555577", fontsize=10)
        ax.set_xlabel("Gerçek (y)",  color=TEXT, fontsize=9)
        ax.set_ylabel("Tahmin (ŷ)", color=TEXT, fontsize=9)
        ax.tick_params(colors=TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(ACCENT)
        self.fig.tight_layout(pad=1.2)
        self.draw()

    def plot(self, y_true, y_pred, r2):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=PANEL)
        ax.scatter(y_true, y_pred, color=GREEN, alpha=0.65, s=18, linewidths=0, zorder=3)
        mn = min(float(np.min(y_true)), float(np.min(y_pred)))
        mx = max(float(np.max(y_true)), float(np.max(y_pred)))
        ax.plot([mn, mx], [mn, mx], color=RED, linewidth=1.4, linestyle='--', zorder=2)
        if r2 >= 1.0 - 1e-6:   rc = GREEN
        elif r2 >= 0.999:        rc = BLUE
        elif r2 >= 0.99:         rc = YELLOW
        else:                    rc = RED
        ax.text(0.04, 0.94, f"R² = {r2:.6f}",
                transform=ax.transAxes, color=rc,
                fontsize=10, fontweight='bold', verticalalignment='top',
                fontfamily='monospace')
        ax.set_xlabel("Gerçek (y)",  color=TEXT, fontsize=9)
        ax.set_ylabel("Tahmin (ŷ)", color=TEXT, fontsize=9)
        ax.set_title("Gerçek vs Tahmin", color=TEXT, fontsize=10)
        ax.tick_params(colors=TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(ACCENT)
        self.fig.tight_layout(pad=1.2)
        self.draw()

# ─── Discovery Worker ─────────────────────────────────────────────────────────

class DiscoveryWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, X, y, var_names, pop, gens, function_set=None, robust=False):
        super().__init__()
        self.X, self.y, self.var_names = X, y, var_names
        self.pop, self.gens            = pop, gens
        self.function_set              = function_set
        self.robust                    = robust
        self._stop                     = False

    def stop(self): self._stop = True

    def run(self):
        try:
            if self.robust:
                from genesis_v2 import discover_robust
                self.progress.emit("Robust mod: 3 motor sırayla çalışıyor...")
                result = discover_robust(self.X, self.y, self.var_names,
                                         pop=self.pop, gens=self.gens,
                                         verbose=False)
            else:
                from genesis_v2 import discover
                self.progress.emit("Evrim başlıyor...")
                result = discover(self.X, self.y, self.var_names,
                                  pop=self.pop, gens=self.gens,
                                  verbose=False, function_set=self.function_set)
            if not self._stop:
                self.finished.emit(result)
        except Exception:
            self.error.emit(traceback.format_exc())

# ─── Benchmark Runner Worker ──────────────────────────────────────────────────

class BenchmarkRunnerWorker(QThread):
    one_finished = pyqtSignal(dict)    # bir benchmark bitti
    all_finished = pyqtSignal()
    error        = pyqtSignal(str)

    def __init__(self, keys, pop=2000, gens=40):
        super().__init__()
        self.keys  = keys
        self.pop   = pop
        self.gens  = gens
        self._stop = False

    def stop(self): self._stop = True

    def run(self):
        try:
            from genesis_v2 import discover, BENCHMARKS as G
            for key in self.keys:
                if self._stop:
                    break
                bm = G.get(key)
                if bm is None:
                    continue
                try:
                    X, y, var_names = bm["gen_func"](500)
                    fs = bm.get("function_set", None)
                    result = discover(X, y, var_names,
                                      pop=self.pop, gens=self.gens,
                                      verbose=False, function_set=fs)
                    result["benchmark"]    = key
                    result["name"]         = bm.get("name", key)
                    result["difficulty"]   = bm.get("difficulty", "")
                    result["true_formula"] = bm.get("true_formula", "")
                    self.one_finished.emit(result)
                except Exception:
                    self.one_finished.emit({
                        "benchmark":  key,
                        "name":       bm.get("name", key),
                        "difficulty": bm.get("difficulty", ""),
                        "r2_opt": float('nan'),
                        "error": traceback.format_exc(),
                    })
            self.all_finished.emit()
        except Exception:
            self.error.emit(traceback.format_exc())

# ─── Yardımcı: tablo satır rengi + sıralama ──────────────────────────────────

def _r2_row_bg(r2):
    if not math.isfinite(r2):
        return "#2a0a0a"
    if r2 >= 0.999:
        return "#0a3d2a"
    if r2 >= 0.99:
        return "#0a2d4a"
    return "#3d2a0a"

def _r2_status(r2):
    if not math.isfinite(r2): return "❌"
    if r2 >= 0.999: return "✅"
    if r2 >= 0.99:  return "🔶"
    return "❌"

class _NumericItem(QTableWidgetItem):
    """Sayısal sıralama için özel item."""
    def __init__(self, value, display):
        super().__init__(display)
        self._val = value

    def __lt__(self, other):
        if isinstance(other, _NumericItem):
            return self._val < other._val
        return super().__lt__(other)

# ─── SEKME 1: Keşif ──────────────────────────────────────────────────────────

class DiscoveryTab(QWidget):
    result_ready  = pyqtSignal(dict)   # GenesisWindow → BenchmarkTableTab
    status_update = pyqtSignal(str)    # GenesisWindow → QStatusBar

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.csv_df   = None
        self.worker   = None
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ══ Sol panel ═══════════════════════════════════════════
        left = QWidget()
        left.setMinimumWidth(300)
        left.setMaximumWidth(420)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(12)

        grp_src = QGroupBox("Veri Kaynağı")
        src_lay = QVBoxLayout(grp_src)
        src_lay.setSpacing(8)

        self.rb_bench = QRadioButton("Benchmark Seç")
        self.rb_csv   = QRadioButton("CSV Yükle")
        self.rb_bench.setChecked(True)
        rg = QButtonGroup(self)
        rg.addButton(self.rb_bench)
        rg.addButton(self.rb_csv)
        src_lay.addWidget(self.rb_bench)

        self.cmb_bench = QComboBox()
        for key, label, diff in BENCHMARKS:
            self.cmb_bench.addItem(f"[{diff}]  {label}", key)
        src_lay.addWidget(self.cmb_bench)

        src_lay.addWidget(self.rb_csv)

        self.csv_widget = QWidget()
        csv_lay = QVBoxLayout(self.csv_widget)
        csv_lay.setContentsMargins(0, 0, 0, 0)
        csv_lay.setSpacing(6)
        self.btn_csv = QPushButton("CSV Dosyası Seç...")
        self.lbl_csv = QLabel("Dosya seçilmedi")
        self.lbl_csv.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        self.lbl_csv.setWordWrap(True)
        tgt_lbl = QLabel("Hedef sütun:")
        tgt_lbl.setStyleSheet("background: transparent; font-size: 11px;")
        self.cmb_target = QComboBox()
        self.cmb_target.setEnabled(False)
        self.cmb_target.addItem("— önce CSV seçin —")
        csv_lay.addWidget(self.btn_csv)
        csv_lay.addWidget(self.lbl_csv)
        csv_lay.addWidget(tgt_lbl)
        csv_lay.addWidget(self.cmb_target)
        src_lay.addWidget(self.csv_widget)
        self.csv_widget.setVisible(False)
        ll.addWidget(grp_src)

        grp_eng = QGroupBox("Motor Ayarları")
        eng_lay = QGridLayout(grp_eng)
        eng_lay.setVerticalSpacing(10)
        eng_lay.setHorizontalSpacing(12)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet("background: transparent;"); return l

        self.spin_pop = QSpinBox()
        self.spin_pop.setRange(500, 5000)
        self.spin_pop.setValue(2000)
        self.spin_pop.setSingleStep(500)
        self.spin_pop.setSuffix("  bireyler")

        self.spin_gens = QSpinBox()
        self.spin_gens.setRange(10, 100)
        self.spin_gens.setValue(40)
        self.spin_gens.setSuffix("  nesil")

        self.chk_robust = QCheckBox("Robust mod  (3 motorla Pareto — daha yavaş)")
        self.chk_robust.setStyleSheet(
            "QCheckBox { background: transparent; color: #c8c8e8; font-size: 11px; }"
            "QCheckBox::indicator:checked { background: #00b894; border: 1px solid #00b894; }"
        )
        self.chk_robust.setToolTip(
            "no_div / standard / extended function_set ile 3 ayrı keşif yapar.\n"
            "R² > 0.99 olanlar arasından en basit formülü seçer (Pareto optimal).\n"
            "Yaklaşık 3× daha uzun sürer."
        )

        eng_lay.addWidget(lbl("Popülasyon:"), 0, 0)
        eng_lay.addWidget(self.spin_pop,      0, 1)
        eng_lay.addWidget(lbl("Nesil:"),      1, 0)
        eng_lay.addWidget(self.spin_gens,     1, 1)
        eng_lay.addWidget(self.chk_robust,    2, 0, 1, 2)
        ll.addWidget(grp_eng)

        self.btn_discover = QPushButton("🔬  Keşfet")
        self.btn_discover.setObjectName("btn_discover")
        ll.addWidget(self.btn_discover)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(
            f"color: {YELLOW}; font-size: 11px; background: transparent;")
        self.lbl_status.setWordWrap(True)
        ll.addWidget(self.lbl_status)
        ll.addStretch()

        # ══ Sağ panel ═══════════════════════════════════════════
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 14, 16, 14)
        rl.setSpacing(10)

        hdr = QLabel("Keşfedilen Formül")
        hdr.setStyleSheet("color: #555577; font-size: 11px; background: transparent;")
        rl.addWidget(hdr)

        self.lbl_formula = QLabel("Henüz keşif yapılmadı")
        self.lbl_formula.setWordWrap(True)
        self.lbl_formula.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_formula.setMinimumHeight(60)
        self.lbl_formula.setStyleSheet(
            f"color: #444466; font-size: 18px; font-weight: bold; "
            f"background: {PANEL}; border: 1px solid {ACCENT}; "
            f"border-radius: 6px; padding: 12px;")
        rl.addWidget(self.lbl_formula)

        met_row = QHBoxLayout()
        met_row.setSpacing(8)
        self.frm_r2,   self.val_r2   = _metric_box("R² Skoru", GREEN)
        self.frm_rmse, self.val_rmse = _metric_box("RMSE",      YELLOW)
        self.frm_time, self.val_time = _metric_box("Süre (s)",  BLUE)
        met_row.addWidget(self.frm_r2)
        met_row.addWidget(self.frm_rmse)
        met_row.addWidget(self.frm_time)
        rl.addLayout(met_row)

        self.canvas = ScatterCanvas()
        rl.addWidget(self.canvas, stretch=1)

        self.lbl_detail = QLabel("")
        self.lbl_detail.setStyleSheet(
            "color: #666688; font-size: 11px; background: transparent;")
        self.lbl_detail.setWordWrap(True)
        rl.addWidget(self.lbl_detail)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([380, 820])
        root.addWidget(splitter)

        self.rb_bench.toggled.connect(self._on_mode)
        self.rb_csv.toggled.connect(self._on_mode)
        self.btn_csv.clicked.connect(self._on_csv_click)
        self.btn_discover.clicked.connect(self._on_discover)

    # ── slot'lar ─────────────────────────────────────────────────

    def _on_mode(self):
        bench = self.rb_bench.isChecked()
        self.cmb_bench.setVisible(bench)
        self.csv_widget.setVisible(not bench)

    def _on_csv_click(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "CSV Dosyası Seç", "", "CSV Dosyaları (*.csv)")
        if not path:
            return
        self.csv_path = path
        self.lbl_csv.setText(os.path.basename(path))
        try:
            df = pd.read_csv(path)
            self.csv_df = df
            nums = df.select_dtypes(include=[np.number]).columns.tolist()
            self.cmb_target.clear()
            if nums:
                self.cmb_target.addItems(nums)
                self.cmb_target.setEnabled(True)
            else:
                self.cmb_target.addItem("Sayısal sütun bulunamadı")
                self.cmb_target.setEnabled(False)
        except Exception as e:
            self.lbl_csv.setText(f"Hata: {e}")

    def _on_discover(self):
        pop  = self.spin_pop.value()
        gens = self.spin_gens.value()

        if self.rb_bench.isChecked():
            key = self.cmb_bench.currentData()
            try:
                from genesis_v2 import BENCHMARKS as G_BENCH
                bm = G_BENCH[key]
            except Exception as e:
                QMessageBox.critical(self, "genesis_v2 yüklenemedi", str(e))
                return
            X, y, var_names = bm["gen_func"](500)
            function_set    = bm.get("function_set", None)
            result_key      = key
            result_name     = bm.get("name", key)
            result_diff     = bm.get("difficulty", "")
            result_true     = bm.get("true_formula", "")
        else:
            if self.csv_df is None:
                QMessageBox.warning(self, "CSV Yok", "Lütfen önce bir CSV dosyası seçin.")
                return
            target = self.cmb_target.currentText()
            df = self.csv_df.select_dtypes(include=[np.number])
            if target not in df.columns:
                QMessageBox.warning(self, "Sütun Yok",
                                    f"'{target}' sütunu sayısal değil veya bulunamadı.")
                return
            y         = df[target].values
            X         = df.drop(columns=[target]).values
            var_names = [c for c in df.columns if c != target]
            function_set = None
            result_key   = os.path.basename(self.csv_path or "csv")
            result_name  = result_key
            result_diff  = "CSV"
            result_true  = ""

        self._pending_meta = {
            "benchmark":    result_key,
            "name":         result_name,
            "difficulty":   result_diff,
            "true_formula": result_true,
        }

        robust = self.chk_robust.isChecked()
        self.worker = DiscoveryWorker(X, y, var_names, pop, gens, function_set, robust=robust)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.progress.connect(lambda msg: self.lbl_status.setText(msg))

        self.btn_discover.setEnabled(False)
        self.btn_discover.setText("Keşfediliyor...")
        mode_str = "robust (3×motor)" if robust else f"pop={pop}, gens={gens}"
        self.lbl_status.setText(f"Evrim başlıyor — {mode_str}")
        self.status_update.emit("Keşfediliyor...")
        self.lbl_formula.setText("Evrim devam ediyor...")
        self.lbl_formula.setStyleSheet(
            f"color: {YELLOW}; font-size: 18px; font-weight: bold; "
            f"background: {PANEL}; border: 1px solid {YELLOW}; "
            f"border-radius: 6px; padding: 12px;")
        self.val_r2.setText("—")
        self.val_rmse.setText("—")
        self.val_time.setText("—")
        self.canvas._init_axes()
        self.worker.start()

    def _on_finished(self, result):
        self.btn_discover.setEnabled(True)
        self.btn_discover.setText("🔬  Keşfet")

        # Meta bilgileri birleştir
        result.update(self._pending_meta)

        formula = (result.get("formula_sympy")
                   or result.get("formula_opt")
                   or result.get("formula", "?"))
        r2   = result.get("r2_opt", result.get("r2", 0)) or 0
        rmse = result.get("rmse", 0) or 0
        secs = result.get("seconds", 0) or 0

        if r2 >= 1.0 - 1e-6:   fc = GREEN
        elif r2 >= 0.999:        fc = BLUE
        elif r2 >= 0.99:         fc = YELLOW
        else:                    fc = RED

        self.lbl_formula.setText(formula)
        self.lbl_formula.setStyleSheet(
            f"color: {fc}; font-size: 18px; font-weight: bold; "
            f"background: {PANEL}; border: 1px solid {fc}; "
            f"border-radius: 6px; padding: 12px;")
        self.val_r2.setText(f"{r2:.6f}")
        self.val_r2.setStyleSheet(
            f"color: {fc}; font-size: 20px; font-weight: bold; "
            f"background: transparent; border: none;")
        self.val_rmse.setText(f"{rmse:.4g}")
        self.val_time.setText(f"{secs:.1f}s")
        self.lbl_detail.setText(
            f"Ham: {result.get('formula', '?')}   |   "
            f"Opt: {result.get('formula_opt', '?')}   |   "
            f"Karmaşıklık: {result.get('complexity', '?')}")
        self.lbl_status.setText("Tamamlandı!")
        self.status_update.emit(f"Keşif tamamlandı — R² = {r2:.6f}")

        # Scatter
        y_true = result.get("y_true")
        y_pred = result.get("y_pred")
        if y_true and y_pred:
            yt = np.array(y_true, dtype=float)
            yp = np.array(y_pred, dtype=float)
            mask = np.isfinite(yt) & np.isfinite(yp)
            if mask.sum() > 1:
                self.canvas.plot(yt[mask], yp[mask], r2)

        # JSON kaydet + diğer sekmeyi güncelle
        self._append_to_json(result)
        self.result_ready.emit(result)

    def _on_error(self, msg):
        self.btn_discover.setEnabled(True)
        self.btn_discover.setText("🔬  Keşfet")
        self.lbl_status.setText("Hata oluştu.")
        self.status_update.emit("Keşif hatası")
        self.lbl_formula.setText("HATA")
        self.lbl_formula.setStyleSheet(
            f"color: {RED}; font-size: 18px; font-weight: bold; "
            f"background: {PANEL}; border: 1px solid {RED}; "
            f"border-radius: 6px; padding: 12px;")
        QMessageBox.critical(self, "Keşif Hatası", msg)

    def _append_to_json(self, result):
        existing = _load_json_results()
        key = result.get("benchmark", "")
        existing = [r for r in existing if r.get("benchmark", "") != key]
        existing.append(result)
        try:
            _save_json_results(existing)
        except Exception:
            pass

# ─── SEKME 2: Benchmark Tablosu ───────────────────────────────────────────────

TABLE_COLS = ["#", "Durum", "Yasa", "Zorluk", "Gerçek Formül", "Keşfedilen (Sympy)", "R²", "Süre(s)"]

class BenchmarkTableTab(QWidget):
    status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._key_to_row = {}     # benchmark key → row index
        self._all_results = {}    # key → result dict
        self._runner = None
        self._run_count = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 8)
        lay.setSpacing(8)

        # ── Araç çubuğu ──────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.btn_load   = QPushButton("📂  Sonuçları Yükle")
        self.btn_run    = QPushButton("▶  Tümünü Çalıştır")
        self.btn_stop   = QPushButton("■  Durdur")
        self.btn_report = QPushButton("💾  Rapor Oluştur")
        self.btn_stop.setEnabled(False)

        self.lbl_stat = QLabel("—")
        self.lbl_stat.setStyleSheet(f"color: {YELLOW}; background: transparent;")

        bar.addWidget(self.btn_load)
        bar.addWidget(self.btn_run)
        bar.addWidget(self.btn_stop)
        bar.addWidget(self.btn_report)
        bar.addStretch()
        bar.addWidget(self.lbl_stat)
        lay.addLayout(bar)

        # ── Tablo ────────────────────────────────────────────────
        self.table = QTableWidget(0, len(TABLE_COLS))
        self.table.setHorizontalHeaderLabels(TABLE_COLS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.verticalHeader().setVisible(False)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # #
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Durum
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Yasa
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Zorluk
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Gerçek
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Keşfedilen
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # R²
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Süre
        lay.addWidget(self.table)

        self.btn_load.clicked.connect(self.load_results)
        self.btn_run.clicked.connect(self._on_run_all)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_report.clicked.connect(self._on_report)

    # ── Sonuç satırı ekle/güncelle ───────────────────────────────

    def add_or_update_row(self, result: dict):
        key = result.get("benchmark", result.get("source", "?"))
        self._all_results[key] = result

        r2   = result.get("r2_opt", result.get("r2", float('nan'))) or 0
        secs = result.get("seconds", 0) or 0

        # Bm adını BENCHMARKS listesinden al, yoksa result'tan
        bm_name = result.get("name", key)
        true_f  = result.get("true_formula", "—")
        found   = (result.get("formula_sympy") or result.get("formula_opt")
                   or result.get("formula", "—"))
        diff    = result.get("difficulty", "—")
        status  = _r2_status(r2)
        bg      = _r2_row_bg(r2)

        self.table.setSortingEnabled(False)

        if key in self._key_to_row:
            row = self._key_to_row[key]
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._key_to_row[key] = row

        # Sütun değerleri
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        name_item = QTableWidgetItem(bm_name)
        diff_item = QTableWidgetItem(diff)
        diff_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        true_item = QTableWidgetItem(true_f)
        found_item = QTableWidgetItem(found)

        r2_item = _NumericItem(r2, f"{r2:.6f}" if math.isfinite(r2) else "—")
        r2_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        time_item = _NumericItem(secs, f"{secs:.1f}")
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        items = [num_item, status_item, name_item, diff_item,
                 true_item, found_item, r2_item, time_item]

        for col, item in enumerate(items):
            item.setBackground(QColor(bg))
            # R² sütununa ayrıca renk
            if col == 6 and math.isfinite(r2):
                if r2 >= 1.0 - 1e-6:   c = GREEN
                elif r2 >= 0.999:        c = BLUE
                elif r2 >= 0.99:         c = YELLOW
                else:                    c = RED
                item.setForeground(QColor(c))
            # Zorluk sütununa renk
            if col == 3:
                dc = {"Kolay": GREEN, "Orta": YELLOW, "Zor": RED}
                item.setForeground(QColor(dc.get(diff, TEXT)))
            self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)
        total = self.table.rowCount()
        ok    = sum(1 for r in self._all_results.values()
                    if math.isfinite(r.get("r2_opt", r.get("r2", float('nan'))) or 0)
                    and (r.get("r2_opt", r.get("r2", 0)) or 0) >= 0.999)
        self.lbl_stat.setText(f"{total} sonuç  |  {ok} × R²≥0.999")

    def load_results(self):
        results = _load_json_results()
        self._key_to_row.clear()
        self.table.setRowCount(0)
        for r in results:
            self.add_or_update_row(r)
        self.status_update.emit(f"{len(results)} benchmark yüklendi")

    # ── Tümünü Çalıştır ──────────────────────────────────────────

    def _on_run_all(self):
        all_keys = [k for k, _, _ in BENCHMARKS]
        self._run_count  = 0
        self._run_total  = len(all_keys)
        self._runner = BenchmarkRunnerWorker(all_keys, pop=2000, gens=40)
        self._runner.one_finished.connect(self._on_one_done)
        self._runner.all_finished.connect(self._on_all_done)
        self._runner.error.connect(lambda m: QMessageBox.critical(self, "Hata", m))
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_run.setText("Çalışıyor...")
        self._runner.start()
        self.status_update.emit("Tüm benchmark'lar çalışıyor...")

    def _on_one_done(self, result):
        self._run_count += 1
        self.add_or_update_row(result)
        self.btn_run.setText(f"Çalışıyor... ({self._run_count}/{self._run_total})")
        # Her bitimde JSON güncelle
        try:
            _save_json_results(list(self._all_results.values()))
        except Exception:
            pass

    def _on_all_done(self):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_run.setText("▶  Tümünü Çalıştır")
        self.status_update.emit(
            f"Tüm benchmark'lar tamamlandı — {self._run_count}/{self._run_total}")

    def _on_stop(self):
        if self._runner and self._runner.isRunning():
            self._runner.stop()
            self._runner.terminate()
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_run.setText("▶  Tümünü Çalıştır")

    def _on_report(self):
        try:
            from genesis_v2 import generate_discovery_report
            results = _load_json_results()
            if not results:
                QMessageBox.warning(self, "Veri Yok",
                                    "Önce sonuçları yükleyin veya benchmark çalıştırın.")
                return
            out = os.path.join(os.path.dirname(RESULTS_JSON), "discovery_report.md")
            generate_discovery_report(results, output_path=out)
            QMessageBox.information(self, "Rapor Oluşturuldu",
                                    f"Rapor kaydedildi:\n{out}")
            self.status_update.emit("Rapor oluşturuldu")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

# ─── SEKME 3: Hakkında ────────────────────────────────────────────────────────

ABOUT_HTML = f"""
<!DOCTYPE html><html><body style="
    background-color:{BG}; color:{TEXT};
    font-family: Consolas, 'Courier New', monospace;
    font-size: 13px; padding: 20px; line-height: 1.6;">

<h1 style="color:{GREEN}; margin-bottom:4px;">GENESIS v1.0</h1>
<h3 style="color:{TEXT}; margin-top:0; font-weight:normal;">
  Physics Law Discovery Engine</h3>

<p>Ham sayısal veriden fizik ve mühendislik yasalarını otomatik keşfeden
sembolik regresyon motoru. Sabit model ailesine parametre uydurmak yerine
<b>formülün yapısını da sıfırdan evrimleştirir</b>.</p>

<p style="color:{GREEN}; font-size:14px; font-weight:bold;">
  Ohm Yasası → 0.68s &nbsp;|&nbsp; Kepler 3. Yasası → 18s
</p>

<h3 style="color:{YELLOW};">Nasıl Çalışıyor?</h3>
<p>Darwin'in evrimi — ama denklemler için:</p>
<pre style="background:{PANEL}; padding:10px; border-radius:4px;
  border-left: 3px solid {GREEN}; overflow-x: auto;">
1. Genetik programlama ile binlerce formül evrimleşir
2. fold_constants()   →  Sabit alt-ağaçları sayıya indirge
3. scipy Nelder-Mead  →  Sabitleri MSE minimizasyonuyla ayarla
4. sympy simplify     →  Cebirsel sadeleştirme (I·√R² → I·R)
</pre>

<h3 style="color:{YELLOW};">Özellikler</h3>
<ul style="padding-left:20px;">
  <li>31 fizik/mühendislik benchmark'ı (Kolay / Orta / Zor)</li>
  <li>CSV dosyası ile kendi verinle keşif</li>
  <li>Sabit optimizasyonu (scipy Nelder-Mead)</li>
  <li>Sympy cebirsel sadeleştirme</li>
  <li>Otomatik Markdown rapor üretimi</li>
  <li>Benchmark sonuçları görselleştirme (genesis_viz.py)</li>
  <li>Streamlit web arayüzü (genesis_app.py)</li>
</ul>

<h3 style="color:{YELLOW};">Benchmark Sonuçları (v1.0 — Kolay Seviye)</h3>
<pre style="background:{PANEL}; padding:10px; border-radius:4px;">
<span style="color:{GREEN};">16/16 Kolay   R² ≥ 0.999   ✅
Ortalama R²  = 1.0000
Ortalama süre = 18.2 saniye</span>
</pre>

<h3 style="color:{YELLOW};">Teknolojiler</h3>
<p>Python 3.10+ &nbsp;|&nbsp; gplearn &nbsp;|&nbsp; numpy &nbsp;|&nbsp;
scipy &nbsp;|&nbsp; sympy &nbsp;|&nbsp; matplotlib &nbsp;|&nbsp;
PyQt6 &nbsp;|&nbsp; pandas</p>

<h3 style="color:{YELLOW};">Geliştirici</h3>
<p>Elektrik-Elektronik Mühendisliği öğrencisi tarafından
sıfır bütçeyle geliştirilmiştir.<br>
MIT Lisansı &copy; 2025</p>

</body></html>
"""

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(ABOUT_HTML)
        lay.addWidget(browser)

# ─── Ana Pencere ──────────────────────────────────────────────────────────────

class GenesisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GENESIS — Physics Law Discovery Engine")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # Sekme widget'larını oluştur
        self.tab_discovery = DiscoveryTab()
        self.tab_benchmark = BenchmarkTableTab()
        self.tab_about     = AboutTab()

        tabs = QTabWidget()
        tabs.addTab(self.tab_discovery, "  ⚡ Keşif  ")
        tabs.addTab(self.tab_benchmark, "  📊 Benchmark Tablosu  ")
        tabs.addTab(self.tab_about,     "  ℹ Hakkında  ")
        self.setCentralWidget(tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır")

        # Çapraz sinyal bağlantıları
        self.tab_discovery.result_ready.connect(self.tab_benchmark.add_or_update_row)
        self.tab_discovery.status_update.connect(self.status_bar.showMessage)
        self.tab_benchmark.status_update.connect(self.status_bar.showMessage)

        # Açılışta mevcut sonuçları yükle
        self.tab_benchmark.load_results()

# ─── Giriş Noktası ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setFont(QFont("Consolas", 10))
    window = GenesisWindow()
    window.show()
    sys.exit(app.exec())
