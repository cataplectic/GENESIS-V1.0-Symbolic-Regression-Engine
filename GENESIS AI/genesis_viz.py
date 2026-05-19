"""
GENESIS v0.6 -- Benchmark Performans Gorsellestirici
Kullanim: python genesis_viz.py results_v2.json
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import math
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.style.use('dark_background')
MONO = {'fontfamily': 'monospace'}

_DIFFICULTY_ORDER = ["Kolay", "Orta", "Zor"]


def _load_results(json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('results', data) if isinstance(data, dict) else data


def _r2_color(r2):
    if r2 >= 1.0 - 1e-9:
        return '#00e676'   # yeşil — mükemmel
    if r2 >= 0.999:
        return '#40c4ff'   # mavi
    if r2 >= 0.99:
        return '#ffa726'   # turuncu
    return '#ef5350'        # kırmızı


def plot_accuracy_bar(results_json_path, output_path="plots/accuracy.png"):
    """Yatay çubuk grafik — her benchmark için R² skoru."""
    results = _load_results(results_json_path)
    results = [r for r in results if math.isfinite(r.get('r2_opt', 0)) and math.isfinite(r.get('complexity', 0))]
    if not results:
        print(f'  [SKIP] {output_path} — yeterli veri yok (NaN/Inf filtresi sonrasi bos liste)')
        return None

    # R²'ye göre sırala (en düşük üstte → bar chart ters sıra)
    results_sorted = sorted(results, key=lambda r: r.get('r2_opt', r.get('r2', 0)))

    names = []
    scores = []
    colors = []
    for r in results_sorted:
        diff = r.get('difficulty', '')
        label = f"{r.get('benchmark', r.get('name', '?'))}  ({diff})"
        r2 = r.get('r2_opt', r.get('r2', 0))
        names.append(label)
        scores.append(r2)
        colors.append(_r2_color(r2))

    n = len(names)
    fig, ax = plt.subplots(figsize=(12, max(6, n * 0.4 + 2)), dpi=150)

    bars = ax.barh(range(n), scores, color=colors, height=0.6, edgecolor='#333333')

    # Değer etiketleri
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(score - 0.0001, i, f'{score:.4f}',
                va='center', ha='right', fontsize=7.5, **MONO, color='white')

    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=8, **MONO)
    ax.set_xlabel('R² Skoru', **MONO, fontsize=10)
    ax.set_title('GENESIS — Benchmark Accuracy (R² Scores)', **MONO, fontsize=13, pad=14)
    min_score = min(scores) if scores else 0.94
    ax.set_xlim(min(0.94, min_score - 0.01), 1.002)
    ax.axvline(x=0.99, color='#ffa726', linestyle='--', linewidth=0.8, alpha=0.6, label='R²=0.99')
    ax.axvline(x=0.999, color='#40c4ff', linestyle='--', linewidth=0.8, alpha=0.6, label='R²=0.999')
    ax.axvline(x=1.0, color='#00e676', linestyle='--', linewidth=0.8, alpha=0.6, label='R²=1.000')

    # Legend
    legend_patches = [
        mpatches.Patch(color='#00e676', label='R²=1.000 (Mükemmel)'),
        mpatches.Patch(color='#40c4ff', label='R²≥0.999'),
        mpatches.Patch(color='#ffa726', label='R²≥0.99'),
        mpatches.Patch(color='#ef5350', label='R²<0.99'),
    ]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=8,
              facecolor='#1a1a1a', edgecolor='#555555')

    ax.grid(axis='x', alpha=0.2, linewidth=0.5)
    fig.tight_layout()

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  [OK] {output_path}')
    return output_path


def plot_complexity_vs_accuracy(results_json_path, output_path="plots/complexity_accuracy.png"):
    """Scatter plot — formül karmaşıklığı vs R² doğruluğu."""
    results = _load_results(results_json_path)
    results = [r for r in results if math.isfinite(r.get('r2_opt', 0)) and math.isfinite(r.get('complexity', 0))]
    if not results:
        print(f'  [SKIP] {output_path} — yeterli veri yok (NaN/Inf filtresi sonrasi bos liste)')
        return None

    complexities = [r.get('complexity', 0) for r in results]
    r2s          = [r.get('r2_opt', r.get('r2', 0)) for r in results]
    names        = [r.get('benchmark', r.get('name', '?')) for r in results]
    colors       = [_r2_color(v) for v in r2s]

    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

    # İdeal bölge (sol üst) — düşük karmaşıklık + yüksek doğruluk
    max_c = max(complexities) if complexities else 30
    ideal_x = max_c * 0.35
    min_r2 = min(r2s) if r2s else 0.95
    ideal_y = min_r2
    ideal_patch = plt.Rectangle((0, ideal_y), ideal_x, (1.001 - ideal_y),
                                 color='#00e676', alpha=0.08, zorder=0)
    ax.add_patch(ideal_patch)
    ax.text(ideal_x * 0.5, 1.0005, 'Ideal Bolge', ha='center', fontsize=8,
            color='#00e676', alpha=0.7, **MONO)

    ax.scatter(complexities, r2s, c=colors, s=90, zorder=3, edgecolors='white', linewidths=0.4)

    # Nokta etiketleri — kısa isimler (ilk 14 karakter)
    for x, y, name in zip(complexities, r2s, names):
        short = name[:14]
        ax.annotate(short, (x, y), textcoords='offset points', xytext=(5, 3),
                    fontsize=6.5, **MONO, color='#cccccc', alpha=0.85)

    ax.set_xlabel('Formul Karmasikligi (node sayisi)', **MONO, fontsize=10)
    ax.set_ylabel('R² Skoru', **MONO, fontsize=10)
    ax.set_title("Complexity vs Accuracy — Occam's Razor Test", **MONO, fontsize=13, pad=14)
    ylim_low = min_r2 - 0.01
    ylim_high = 1.003
    if math.isfinite(ylim_low) and math.isfinite(ylim_high) and ylim_low < ylim_high:
        ax.set_ylim(ylim_low, ylim_high)
    ax.grid(alpha=0.15, linewidth=0.5)

    legend_patches = [
        mpatches.Patch(color='#00e676', label='R²=1.000'),
        mpatches.Patch(color='#40c4ff', label='R²≥0.999'),
        mpatches.Patch(color='#ffa726', label='R²≥0.99'),
        mpatches.Patch(color='#ef5350', label='R²<0.99'),
    ]
    ax.legend(handles=legend_patches, fontsize=8, facecolor='#1a1a1a', edgecolor='#555555')

    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  [OK] {output_path}')
    return output_path


def plot_discovery_time(results_json_path, output_path="plots/time.png"):
    """Zorluk seviyesine göre gruplandırılmış keşif süresi grafiği."""
    results = _load_results(results_json_path)
    results = [r for r in results if math.isfinite(r.get('r2_opt', 0)) and math.isfinite(r.get('complexity', 0))]
    if not results:
        print(f'  [SKIP] {output_path} — yeterli veri yok (NaN/Inf filtresi sonrasi bos liste)')
        return None

    groups = {d: [] for d in _DIFFICULTY_ORDER}
    for r in results:
        diff = r.get('difficulty', 'Bilinmiyor')
        if diff not in groups:
            groups[diff] = []
        secs = r.get('seconds', 0)
        groups[diff].append({
            'name': r.get('benchmark', r.get('name', '?')),
            'seconds': secs if math.isfinite(secs) else 0,
        })

    # Her grup içinde süreye göre sırala
    for d in groups:
        groups[d].sort(key=lambda x: x['seconds'])

    # Renk paleti per difficulty
    diff_colors = {'Kolay': '#00e676', 'Orta': '#ffa726', 'Zor': '#ef5350'}

    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    x_pos = 0
    tick_positions = []
    tick_labels = []
    group_centers = []
    group_labels = []

    for diff in _DIFFICULTY_ORDER:
        items = groups.get(diff, [])
        if not items:
            continue
        color = diff_colors.get(diff, '#aaaaaa')
        start_x = x_pos
        for item in items:
            bar = ax.bar(x_pos, item['seconds'], color=color, width=0.7,
                         edgecolor='#333333', linewidth=0.5)
            tick_positions.append(x_pos)
            short_name = item['name'][:12]
            tick_labels.append(short_name)
            # Değer etiketi
            ax.text(x_pos, item['seconds'] + 0.3, f"{item['seconds']:.1f}s",
                    ha='center', va='bottom', fontsize=6.5, **MONO, color='white')
            x_pos += 1
        # Grup orta noktası + başlık
        center = (start_x + x_pos - 1) / 2
        group_centers.append(center)
        group_labels.append(diff)
        # Grup ayırıcı
        if x_pos < sum(len(v) for v in groups.values()):
            ax.axvline(x=x_pos - 0.5, color='#555555', linestyle='--', linewidth=0.8, alpha=0.5)
        x_pos += 0.5

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=40, ha='right', fontsize=7.5, **MONO)
    ax.set_ylabel('Keşif Süresi (saniye)', **MONO, fontsize=10)
    ax.set_title('Discovery Time by Difficulty', **MONO, fontsize=13, pad=14)

    # Zorluk grubu etiketleri üstte
    ylim_top = ax.get_ylim()[1]
    if not math.isfinite(ylim_top):
        ylim_top = 1.0
    for center, label in zip(group_centers, group_labels):
        ax.text(center, ylim_top * 0.96, label,
                ha='center', fontsize=10, **MONO,
                color=diff_colors.get(label, 'white'),
                fontweight='bold', alpha=0.85)

    ax.grid(axis='y', alpha=0.15, linewidth=0.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  [OK] {output_path}')
    return output_path


def generate_all_plots(results_json_path, plots_dir="plots"):
    print(f"\nGENESIS Gorsellestirici -- {results_json_path}")
    print("=" * 50)
    plot_accuracy_bar(results_json_path,
                      output_path=os.path.join(plots_dir, "accuracy.png"))
    plot_complexity_vs_accuracy(results_json_path,
                                output_path=os.path.join(plots_dir, "complexity_accuracy.png"))
    plot_discovery_time(results_json_path,
                        output_path=os.path.join(plots_dir, "time.png"))
    print(f"\nTum grafikler -> {plots_dir}/")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "results_v2.json"
    plots_dir = sys.argv[2] if len(sys.argv) > 2 else "plots"
    generate_all_plots(json_path, plots_dir)
