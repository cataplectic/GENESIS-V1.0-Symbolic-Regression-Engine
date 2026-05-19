"""
GENESIS v0.6 — İnteraktif Web Demo
Çalıştırma: streamlit run genesis_app.py
"""

import sys
import os
import json
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# genesis_v2'yi aynı klasörden import et
sys.path.insert(0, os.path.dirname(__file__))
from genesis_v2 import discover, discover_from_csv

# ─── Sayfa Ayarları ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GENESIS — Physics Law Discovery",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    border: 1px solid #333355;
  }
  .metric-value { font-size: 2rem; font-weight: bold; font-family: monospace; }
  .metric-label { font-size: 0.8rem; color: #aaaaaa; font-family: monospace; }
  .formula-box {
    background: #0d1117;
    border-left: 4px solid #00e676;
    border-radius: 6px;
    padding: 14px 20px;
    font-family: monospace;
    font-size: 1.4rem;
    margin: 10px 0;
  }
</style>
""", unsafe_allow_html=True)

# ─── Renk yardımcıları ────────────────────────────────────────────────────────
def r2_color(r2):
    if r2 >= 1.0 - 1e-9: return '#00e676'
    if r2 >= 0.999:       return '#40c4ff'
    if r2 >= 0.99:        return '#ffa726'
    return '#ef5350'

def r2_marker(r2):
    if r2 >= 0.99: return '✅'
    if r2 >= 0.95: return '🔶'
    return '❌'

# ─── Grafik: Gerçek vs Tahmin ──────────────────────────────────────────────────
def scatter_actual_vs_predicted(y_true, y_pred, r2, title="Gerçek vs Tahmin"):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_true, y_pred, c='#40c4ff', alpha=0.55, s=18, edgecolors='none')
    lim_min = min(y_true.min(), y_pred.min())
    lim_max = max(y_true.max(), y_pred.max())
    margin = (lim_max - lim_min) * 0.05
    ax.plot([lim_min - margin, lim_max + margin],
            [lim_min - margin, lim_max + margin],
            'r--', linewidth=1.5, label='y = x (ideal)')
    ax.set_xlim(lim_min - margin, lim_max + margin)
    ax.set_ylim(lim_min - margin, lim_max + margin)
    ax.set_xlabel('Gerçek Değer', fontfamily='monospace', fontsize=10)
    ax.set_ylabel('Tahmin', fontfamily='monospace', fontsize=10)
    ax.set_title(title, fontfamily='monospace', fontsize=11)
    ax.annotate(f'R² = {r2:.5f}', xy=(0.04, 0.92), xycoords='axes fraction',
                fontsize=11, color='#00e676', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e', edgecolor='#00e676'))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    return fig

# ─── JSON yükleyici ────────────────────────────────────────────────────────────
@st.cache_data
def load_results(json_path="results_v2.json"):
    if not os.path.exists(json_path):
        return None
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', data) if isinstance(data, dict) else data
    return results

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ GENESIS v0.6")
    st.markdown("*Physics Law Discovery Engine*")
    st.divider()

    mode = st.radio("Mod", ["📊 Benchmark Sonuçları", "🔬 Kendi Verinle Keşfet"])
    st.divider()

    if mode == "📊 Benchmark Sonuçları":
        difficulty_filter = st.selectbox(
            "Zorluk Filtresi",
            ["Hepsi", "Kolay", "Orta", "Zor"],
        )
        json_path = st.text_input("JSON dosyası", value="results_v2.json")

    st.markdown("---")
    st.markdown(
        "<small style='color:#666'>gplearn + scipy + sympy<br>github.com/genesis-ai</small>",
        unsafe_allow_html=True,
    )

# ─── BENCHMARK MODU ───────────────────────────────────────────────────────────
if mode == "📊 Benchmark Sonuçları":
    st.title("GENESIS — Benchmark Sonuçları")

    results = load_results(json_path)

    if results is None:
        st.warning(f"`{json_path}` bulunamadı. Önce `python genesis_v2.py` çalıştırın.")
        st.stop()

    # Zorluk filtresi
    if difficulty_filter != "Hepsi":
        results = [r for r in results if r.get('difficulty') == difficulty_filter]

    if not results:
        st.info("Bu zorluk seviyesinde sonuç yok.")
        st.stop()

    # Metrik kartları
    total = len(results)
    avg_r2 = np.mean([r.get('r2_opt', r.get('r2', 0)) for r in results])
    perfect = sum(1 for r in results if r.get('r2_opt', r.get('r2', 0)) >= 0.99)
    avg_time = np.mean([r.get('seconds', 0) for r in results])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#40c4ff">{total}</div>
            <div class="metric-label">Toplam Benchmark</div></div>""",
            unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:{r2_color(avg_r2)}">{avg_r2:.4f}</div>
            <div class="metric-label">Ortalama R²</div></div>""",
            unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#00e676">{perfect}/{total}</div>
            <div class="metric-label">Mükemmel Keşif (R²≥0.99)</div></div>""",
            unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ffa726">{avg_time:.1f}s</div>
            <div class="metric-label">Ortalama Süre</div></div>""",
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sonuç tablosu
    st.subheader("Sonuç Tablosu")

    rows = []
    for r in results:
        r2 = r.get('r2_opt', r.get('r2', 0))
        rows.append({
            '':         r2_marker(r2),
            'Yasa':     r.get('benchmark', r.get('name', '?')),
            'Zorluk':   r.get('difficulty', '?'),
            'Gerçek Formül': r.get('true_formula', '?'),
            'Keşfedilen (Sympy)': r.get('formula_sympy', r.get('formula', '?')),
            'R²':       round(r2, 5),
            'Süre (s)': r.get('seconds', 0),
        })

    df = pd.DataFrame(rows)

    def color_r2(val):
        try:
            v = float(val)
        except (ValueError, TypeError):
            return ''
        if v >= 0.99:  return 'color: #00e676'
        if v >= 0.95:  return 'color: #ffa726'
        return 'color: #ef5350'

    styled = df.style.map(color_r2, subset=['R²'])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Detay genişleticisi
    st.subheader("Detay")
    names = [r.get('benchmark', r.get('name', f'#{i}')) for i, r in enumerate(results)]
    selected = st.selectbox("Benchmark seç", names)

    r = next(x for x in results if x.get('benchmark', x.get('name')) == selected)
    with st.expander(f"📌 {selected}", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Zorluk:** {r.get('difficulty', '?')}")
            st.markdown(f"**Gerçek formül:** `{r.get('true_formula', '?')}`")
            st.markdown(f"**Ham formül:**")
            st.code(r.get('formula', '?'), language=None)
            st.markdown(f"**Sabit opt.:**")
            st.code(r.get('formula_opt', r.get('formula', '?')), language=None)
        with col_b:
            st.markdown(f"**Sympy (sadeleştirilmiş):**")
            st.markdown(f'<div class="formula-box">{r.get("formula_sympy","?")}</div>',
                        unsafe_allow_html=True)
            r2_val = r.get('r2_opt', r.get('r2', 0))
            st.metric("R²(opt)", f"{r2_val:.6f}")
            st.metric("RMSE", r.get('rmse', 0))
            st.metric("Karmaşıklık", r.get('complexity', '?'))
            st.metric("Süre", f"{r.get('seconds', 0):.2f} s")

# ─── KENDİ VERİNLE KEŞİF MODU ─────────────────────────────────────────────────
else:
    st.title("GENESIS — Kendi Verinle Keşfet")
    st.markdown("CSV dosyan yükle, hedef sütunu seç ve **Keşfet** butonuna bas.")

    uploaded = st.file_uploader("CSV dosyası yükle", type=["csv"])

    if uploaded is not None:
        df_raw = pd.read_csv(uploaded)
        numeric_cols = df_raw.select_dtypes(include=[np.number]).columns.tolist()
        df_clean = df_raw[numeric_cols].dropna()

        st.markdown(f"**{len(df_clean)} satır, {len(numeric_cols)} sayısal sütun**")
        st.dataframe(df_clean.head(8), use_container_width=True)

        if len(numeric_cols) < 2:
            st.error("En az 2 sayısal sütun gerekli (girdi + hedef).")
            st.stop()

        target_col = st.selectbox("Hedef sütun (y)", numeric_cols)
        feature_cols = [c for c in numeric_cols if c != target_col]

        col_left, col_right = st.columns([1, 3])
        with col_left:
            pop_size = st.number_input("Popülasyon", min_value=500, max_value=5000,
                                       value=2000, step=500)
            gens = st.number_input("Nesil sayısı", min_value=10, max_value=100,
                                   value=30, step=10)

        run_btn = st.button("⚡ Keşfet", type="primary")

        if run_btn:
            X = df_clean[feature_cols].values
            y = df_clean[target_col].values

            if len(df_clean) > 1000:
                idx = np.random.RandomState(42).choice(len(df_clean), 1000, replace=False)
                X, y = X[idx], y[idx]
                st.info("1000'den fazla satır var — rastgele 1000 satır alındı.")

            with st.spinner("Formül aranıyor... (bu birkaç dakika sürebilir)"):
                result = discover(X, y, feature_cols,
                                  pop=int(pop_size), gens=int(gens), verbose=False)

            st.success("Keşif tamamlandı!")

            st.markdown("### Keşfedilen Formül")
            st.markdown(
                f'<div class="formula-box">{result["formula_sympy"]}</div>',
                unsafe_allow_html=True,
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("R²", f"{result['r2_opt']:.5f}")
            m2.metric("RMSE", f"{result['rmse']:.4f}")
            m3.metric("Karmaşıklık", result['complexity'])
            m4.metric("Süre", f"{result['seconds']:.1f} s")

            # Karşılaştırma: ham vs sadeleştirilmiş
            with st.expander("Ham ve optimize formüller"):
                st.code(result['formula'], language=None)
                if result['formula_opt'] != result['formula']:
                    st.markdown("↓ Sabit optimizasyonu sonrası:")
                    st.code(result['formula_opt'], language=None)

            # Scatter: gerçek vs tahmin
            st.markdown("### Gerçek vs Tahmin")

            # Tahmin için eval-tabanlı basit yaklaşım: gplearn model
            # discover() R² zaten hesapladı, tahminleri yeniden üretemeyiz (model döndürmüyor)
            # — numpy eval kullanacağız; başarısız olursa grafik gösterilmez
            try:
                import sympy as sp
                sym_vars = {name: sp.Symbol(name, real=True) for name in feature_cols}
                expr_str = result['formula_sympy']
                expr = sp.sympify(expr_str, locals=sym_vars)
                f_lambda = sp.lambdify(list(sym_vars.values()), expr, 'numpy')
                args = [X[:, i] for i in range(len(feature_cols))]
                y_pred = np.array(f_lambda(*args), dtype=float)
                if not np.any(np.isnan(y_pred)) and not np.any(np.isinf(y_pred)):
                    from sklearn.metrics import r2_score
                    r2_check = r2_score(y, y_pred)
                    fig = scatter_actual_vs_predicted(y, y_pred, r2_check,
                                                      title=f"Gerçek vs Tahmin — {target_col}")
                    st.pyplot(fig)
                else:
                    st.info("Scatter plot için tahmin hesaplanamadı (nan/inf içeriyor).")
            except Exception as e:
                st.info(f"Scatter plot oluşturulamadı: {e}")

            # JSON indir
            result_json = json.dumps({**result, "target": target_col,
                                      "variables": feature_cols}, indent=2, ensure_ascii=False)
            st.download_button("📥 Sonucu İndir (JSON)", result_json,
                               file_name="genesis_result.json", mime="application/json")

    else:
        st.markdown("""
**Başlamak için:**
1. Sol panelden bir CSV dosyası yükle
2. Hedef sütununu seç
3. ⚡ Keşfet butonuna bas

**Örnek:** `datasets/rc_circuit.csv` → hedef: `tau` → keşfedilen: `C*R`
        """)
        st.markdown("---")
        st.markdown("Hazır veri setleri için `datasets/` klasörüne bakın.")
