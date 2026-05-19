import pandas as pd
import numpy as np
import os

os.makedirs("datasets", exist_ok=True)

# ════════════════════════════════════════════
# 1. AIRFOIL SELF-NOISE (NASA - En kolay doğrulama)
# ════════════════════════════════════════════
# Kaynak: UCI ML Repository
# URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00291/airfoil_self_noise.dat

url1 = "https://archive.ics.uci.edu/ml/machine-learning-databases/00291/airfoil_self_noise.dat"
try:
    df1 = pd.read_csv(url1, sep='\t', header=None,
                       names=["Frequency","Angle","Chord_Length","Velocity","Displacement","Sound_Pressure"])
    df1.to_csv("datasets/airfoil.csv", index=False)
    print(f"Airfoil: {df1.shape} kayit, {df1.columns.tolist()}")
except Exception as e:
    print(f"Airfoil URL indirilemedi: {e}")
    print("Sentetik airfoil verisi uretiliyor...")
    # Sentetik: Brookes-Pope-Marcolini modeli benzeri (ampirik, kapali formu yok)
    np.random.seed(42)
    n = 1503
    freq = np.random.choice([200,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000], n)
    angle = np.random.uniform(0, 22.2, n)
    chord = np.random.choice([0.0254, 0.0508, 0.1016, 0.1524, 0.2286, 0.3048], n)
    vel = np.random.choice([31.7, 39.6, 55.5, 71.3], n)
    disp = 10 ** np.random.uniform(-4, -1.5, n)
    # Ampirik yaklasim (gercek formul bilinmiyor - NASA deneysel)
    spl = (
        132.0
        - 10 * np.log10(freq / 1000 + 1e-10)
        - 30 * np.log10(chord + 1e-10)
        + 8 * np.log10(vel / 40 + 1e-10)
        - 5 * np.log10(disp + 1e-10)
        - 0.4 * angle
        + np.random.normal(0, 1.5, n)
    )
    df1 = pd.DataFrame({
        "Frequency": freq,
        "Angle": angle.round(2),
        "Chord_Length": chord,
        "Velocity": vel,
        "Displacement": disp.round(6),
        "Sound_Pressure": spl.round(2)
    })
    df1.to_csv("datasets/airfoil.csv", index=False)
    print(f"Airfoil (sentetik): {df1.shape}")

# ════════════════════════════════════════════
# 2. CONCRETE COMPRESSIVE STRENGTH
# ════════════════════════════════════════════

try:
    url2 = "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls"
    df2 = pd.read_excel(url2)
    df2.columns = ["Cement","Blast_Furnace","Fly_Ash","Water","Superplast",
                   "Coarse_Agg","Fine_Agg","Age","Strength"]
    df2_clean = df2[["Cement","Water","Coarse_Agg","Fine_Agg","Age","Strength"]]
    df2_clean.to_csv("datasets/concrete.csv", index=False)
    print(f"Concrete (UCI): {df2_clean.shape}")
except Exception as e:
    print(f"Concrete URL indirilemedi: {e}")
    print("Sentetik concrete verisi uretiliyor...")
    np.random.seed(7)
    n = 1030
    cement = np.random.uniform(100, 550, n)
    water  = np.random.uniform(120, 250, n)
    coarse = np.random.uniform(700, 1200, n)
    fine   = np.random.uniform(500, 1000, n)
    age    = np.random.choice([3,7,14,28,56,90,180,270,365], n)
    wb = water / cement
    strength = (
        96 / (wb + 0.5)             # Abrams yasasi
        + 8 * np.log(age)           # Logaritmik kur etkisi
        - 0.015 * (coarse + fine)   # Agrega etkisi
        + np.random.normal(0, 3.5, n)
    )
    strength = np.clip(strength, 2, 90)
    df2c = pd.DataFrame({
        "Cement": cement.round(1),
        "Water": water.round(1),
        "Coarse_Agg": coarse.round(1),
        "Fine_Agg": fine.round(1),
        "Age": age,
        "Strength": strength.round(2)
    })
    df2c.to_csv("datasets/concrete.csv", index=False)
    print(f"Concrete (sentetik): {df2c.shape}")

# ════════════════════════════════════════════
# 3. COMBINED CYCLE POWER PLANT
# ════════════════════════════════════════════

try:
    url3 = "https://archive.ics.uci.edu/ml/machine-learning-databases/00294/CCPP.zip"
    import urllib.request, zipfile, io
    response = urllib.request.urlopen(url3, timeout=15)
    z = zipfile.ZipFile(io.BytesIO(response.read()))
    for name in z.namelist():
        if name.endswith('.xlsx') or name.endswith('.xls'):
            df3 = pd.read_excel(z.open(name))
            break
    df3.columns = ["AT","V","AP","RH","PE"]
    df3_sample = df3.sample(2000, random_state=42).reset_index(drop=True)
    df3_sample.to_csv("datasets/ccpp.csv", index=False)
    print(f"CCPP (UCI): {df3_sample.shape}")
except Exception as e:
    print(f"CCPP URL indirilemedi: {e}")
    print("Sentetik CCPP verisi uretiliyor...")
    # Kombine cevrim santrali: AT, V (vakum), AP (basınç), RH (nem) → PE (güç)
    np.random.seed(13)
    n = 2000
    AT = np.random.uniform(1.8, 37.1, n)    # Ortam sicakligi (C)
    V  = np.random.uniform(25.4, 81.6, n)   # Egzoz vakumu (cmHg)
    AP = np.random.uniform(992, 1034, n)    # Atmosfer basinci (mbar)
    RH = np.random.uniform(25.6, 100.2, n)  # Bagil nem (%)
    # Ampirik model (IEEE paper Tufekci 2014 benzeri)
    PE = (
        498.7
        - 2.40 * AT
        - 0.259 * V
        + 0.0507 * AP
        - 0.158 * RH
        + 0.0043 * AT * V
        - 0.0018 * AT**2
        + np.random.normal(0, 2.5, n)
    )
    PE = np.clip(PE, 420, 495)
    df3s = pd.DataFrame({
        "AT": AT.round(2),
        "V":  V.round(2),
        "AP": AP.round(2),
        "RH": RH.round(2),
        "PE": PE.round(2)
    })
    df3s.to_csv("datasets/ccpp.csv", index=False)
    print(f"CCPP (sentetik): {df3s.shape}")

# ════════════════════════════════════════════
# 4. YACHT HYDRODYNAMICS
# ════════════════════════════════════════════

try:
    url4 = "https://archive.ics.uci.edu/ml/machine-learning-databases/00243/yacht_hydrodynamics.data"
    df4 = pd.read_csv(url4, sep=r'\s+', header=None,
                       names=["LongPos","Prismatic","Length_Disp","Beam_Draught",
                              "Length_Beam","Froude","Residuary_Resist"])
    df4_clean = df4.drop(columns=["LongPos"])
    df4_clean.to_csv("datasets/yacht.csv", index=False)
    print(f"Yacht (UCI): {df4_clean.shape}")
except Exception as e:
    print(f"Yacht URL indirilemedi: {e}")
    print("Sentetik yacht verisi uretiliyor...")
    # Savitsky yontemi: direnc Froude sayisinin kuvvet yasasi fonksiyonu
    np.random.seed(99)
    n = 308
    prismatic = np.random.uniform(0.53, 0.60, n)
    ld = np.random.uniform(4.34, 5.14, n)     # L/D orani
    bd = np.random.uniform(2.81, 5.35, n)     # B/D orani
    lb = np.random.uniform(2.73, 4.78, n)     # L/B orani
    froude = np.random.uniform(0.125, 0.450, n)
    # Ampirik direnc modeli (Gerritsma & Beukelman)
    rr = (
        0.08 * (froude ** 5.5)
        * (1 + 3.5 * (prismatic - 0.56))
        * np.exp(-1.2 * bd)
        * np.exp(0.8 * lb)
        + np.random.exponential(0.3, n) * froude**3
    )
    rr = np.clip(rr, 0.01, 50)
    df4s = pd.DataFrame({
        "Prismatic": prismatic.round(3),
        "Length_Disp": ld.round(3),
        "Beam_Draught": bd.round(3),
        "Length_Beam": lb.round(3),
        "Froude": froude.round(3),
        "Residuary_Resist": rr.round(4)
    })
    df4s.to_csv("datasets/yacht.csv", index=False)
    print(f"Yacht (sentetik): {df4s.shape}")

# ════════════════════════════════════════════
# 5. STAR LUMINOSITY (Stefan-Boltzmann doğrulaması)
# ════════════════════════════════════════════

np.random.seed(42)
n = 300
T = np.random.uniform(2000, 40000, n)     # Kelvin
R = np.random.uniform(0.1, 200, n)        # Gunes yaricapi
L = R**2 * (T / 5778)**4                  # Stefan-Boltzmann (normalize)
noise = np.random.normal(1, 0.05, n)      # %5 gurultu
L_noisy = L * noise

df5 = pd.DataFrame({
    "Temperature_K": T.round(0),
    "Radius_Rsun": R.round(3),
    "Luminosity_Lsun": L_noisy.round(4)
})
df5.to_csv("datasets/stars.csv", index=False)
print(f"Stars (sentetik, Stefan-Boltzmann): {df5.shape}")

# ════════════════════════════════════════════
# OZET
# ════════════════════════════════════════════
print("\n=== Indirilen/Uretilen veri setleri ===")
for f in sorted(os.listdir("datasets")):
    if f.endswith(".csv"):
        df = pd.read_csv(f"datasets/{f}")
        print(f"  {f}: {df.shape[0]} satir x {df.shape[1]} sutun | "
              f"sutunlar: {', '.join(df.columns.tolist())}")
