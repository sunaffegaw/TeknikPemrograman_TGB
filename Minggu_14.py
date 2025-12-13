import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO


# =============================
# 🔹 MODEL DATA (OOP)
# =============================
class DatasetMagnetik:
    def __init__(self, data_raw: str):
        self.data = self.parse_data(data_raw)
        self.statistik = self.hitung_statistik()

    def parse_data(self, data_raw: str) -> pd.DataFrame:
        df = pd.read_csv(StringIO(data_raw))
        df = df.dropna()
        df.columns = df.columns.str.strip()
        return df

    def hitung_statistik(self):
        t = self.data["t_obs"]
        x = self.data["x"]
        y = self.data["y"]
        return {
            "tMin": float(t.min()),
            "tMax": float(t.max()),
            "jumlah": len(t),
            "rangeX": [float(x.min()), float(x.max())],
            "rangeY": [float(y.min()), float(y.max())],
            "rataRata": float(t.mean()),
        }

    def get_data_regional(self) -> pd.DataFrame:
        """Hitung rata-rata regional berdasarkan lintasan (kelompok y)"""
        df = self.data.copy()
        df["region"] = (df["y"] // 100) * 100
        regional_means = df.groupby("region")["t_obs"].transform("mean")
        df["t_obs_regional"] = regional_means
        # kembalikan dataframe dengan x, y, dan nilai rata-rata per region
        return df[["x", "y", "t_obs_regional"]].rename(columns={"t_obs_regional": "t_obs"})

    def get_data_residual(self) -> pd.DataFrame:
        """Hitung residual (observasi - rata-rata regional)"""
        df = self.data.copy()
        df["region"] = (df["y"] // 100) * 100
        regional_means = df.groupby("region")["t_obs"].transform("mean")
        df["residual"] = df["t_obs"] - regional_means
        return df[["x", "y", "residual"]].rename(columns={"residual": "t_obs"})


# =============================
# 🔹 KONFIGURASI WARNA (OOP)
# =============================
class KonfigurasiVisualisasi:
    def __init__(self, colormap="viridis"):
        self.colormap = colormap

    def get_colormap(self):
        maps = {
            "viridis": "Viridis",
            "plasma": "Plasma",
            "cividis": "Cividis",
            "inferno": "Inferno",
            "turbo": "Turbo",
            "rdBu": "RdBu",
        }
        return maps.get(self.colormap, "Viridis")


# =============================
# 🔹 DATASET: test_magnetic
# =============================
data_text = """x,y,t_obs
1.23,52.10,45005.12
51.45,49.88,45009.34
102.10,50.55,45013.78
148.90,48.20,45018.12
201.30,51.15,45022.45
249.50,50.90,45026.89
302.10,49.45,45031.23
351.80,51.60,45036.56
398.20,50.10,45041.89
452.40,49.90,45048.23
501.10,52.30,45055.67
548.90,50.40,45062.12
602.30,51.20,45065.45
651.50,49.80,45068.78
702.10,50.15,45070.12
751.40,51.10,45072.34
801.20,49.90,45074.56
849.80,50.30,45076.89
901.50,51.40,45078.12
952.10,49.70,45080.45
1001.20,50.90,45082.67
2.15,151.30,45015.45
49.80,149.50,45019.67
101.20,150.80,45023.90
152.40,151.20,45028.12
199.10,149.90,45032.56
251.30,150.40,45037.89
300.50,151.10,45043.23
352.10,149.60,45049.56
399.40,150.90,45058.12
451.20,151.30,45070.45
502.50,149.80,45085.67
549.10,150.50,45095.89
601.40,151.00,45098.12
652.30,149.40,45095.34
699.80,150.70,45088.56
751.20,151.50,45082.78
800.40,149.90,45078.90
851.10,150.30,45076.12
900.20,151.40,45075.45
951.50,149.70,45076.67
1002.10,150.20,45078.90
4.50,250.10,45025.12
52.10,248.90,45029.34
98.70,251.20,45034.56
151.20,249.50,45039.78
202.40,250.80,45046.12
248.90,251.40,45054.34
301.20,249.10,45065.56
350.50,250.70,45080.78
402.10,251.30,45105.12
451.40,249.80,45145.45
499.80,250.90,45190.67
552.10,251.50,45210.89
600.30,249.40,45195.12
648.70,250.60,45155.34
701.50,251.10,45120.56
750.20,249.70,45100.78
801.40,250.30,45090.90
852.10,251.80,45085.12
899.50,249.20,45082.45
948.80,250.50,45081.67
1001.30,251.00,45082.90
"""

# =============================
# 🔹 STREAMLIT APP
# =============================
st.set_page_config(page_title="Visualisasi Spasial", layout="wide")

st.title("🌍 Visualisasi Spasial Anomali Magnetik")

# Sidebar pengaturan
st.sidebar.header("⚙️ Pengaturan Visualisasi")
colormap = st.sidebar.selectbox("Pilih Colormap", ["viridis", "plasma", "inferno", "cividis", "turbo", "rdBu"])
mode = st.sidebar.radio("Mode Tampilan", ["Observasi", "Regional", "Residual"])

dataset = DatasetMagnetik(data_text)
viz = KonfigurasiVisualisasi(colormap)

# Pilih data sesuai mode
if mode == "Regional":
    df_display = dataset.get_data_regional()
elif mode == "Residual":
    df_display = dataset.get_data_residual()
else:
    df_display = dataset.data.copy()

# Pastikan x, y, dan t_obs selalu ada
if not {"x", "y", "t_obs"}.issubset(df_display.columns):
    st.error("❌ Kolom x, y, atau t_obs tidak ditemukan di dataset yang akan divisualisasikan.")
else:
    fig = px.scatter(
        df_display,
        x="x",
        y="y",
        color="t_obs",
        color_continuous_scale=viz.get_colormap(),
        title=f"Peta Anomali Magnetik ({mode})",
        hover_data=["x", "y", "t_obs"],
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# Statistik dataset
st.subheader("📈 Statistik Dataset")
col1, col2, col3 = st.columns(3)
col1.metric("Jumlah Titik", dataset.statistik["jumlah"])
col2.metric("Nilai Minimum (nT)", f"{dataset.statistik['tMin']:.2f}")
col3.metric("Nilai Maksimum (nT)", f"{dataset.statistik['tMax']:.2f}")
