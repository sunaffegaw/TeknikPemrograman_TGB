import streamlit as st
import segyio
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class SegyReader:
    """Class untuk membaca dan memproses file SEG-Y"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data_segy = None
        self.header_df = None
        
    def read_header_and_data(self, byte_locs, length=4, signed=True):
        """
        Membaca data dan header dari file SEG-Y
        
        Parameters
        ----------
        byte_locs : list
            Daftar byte location (1-based)
        length : int
            Panjang field dalam byte
        signed : bool
            Jika True nilai dianggap signed integer
        """
        byte_locs = list(byte_locs)
        
        with segyio.open(self.file_path, "r", ignore_geometry=True) as f:
            n_traces = f.tracecount
            n_locs = len(byte_locs)
            
            values = np.zeros((n_traces, n_locs), dtype=np.int32)
            data_segy = []
            
            for i in range(n_traces):
                h = f.header[i]
                buf = h.buf
                
                for j, byte_pos in enumerate(byte_locs):
                    start = byte_pos - 1
                    raw = bytes(buf[start:start+length])
                    values[i, j] = int.from_bytes(raw, byteorder="big", signed=signed)
                
                data_segy.append(f.trace[i])
        
        # Simpan data
        self.data_segy = np.array(data_segy).T
        
        # Buat DataFrame header
        col_names = [f"byte_{loc}" for loc in byte_locs]
        self.header_df = pd.DataFrame(values, columns=col_names)
        
        return self.data_segy, self.header_df


class SeismicPlotter:
    """Class untuk plotting data seismik"""
    
    def __init__(self):
        self.colormaps = {
            "Seismic": [[0.0, "blue"], [0.5, "white"], [1.0, "red"]],
            "Gray": [[0.0, "black"], [0.5, "gray"], [1.0, "white"]],
            "Viridis": "viridis",
            "Jet": "jet",
            "Hot": "hot",
            "Cool": "cool",
            "Rainbow": "rainbow"
        }
        
    def get_colormap_list(self):
        """Mengembalikan daftar nama colormap"""
        return list(self.colormaps.keys())
    
    def plot_seismic(self, data, colormap_name="Seismic", vmin=None, vmax=None, 
                     scale_mode="Auto", reverse_axis=False, as_image=False):
        """
        Plot data seismik dengan berbagai opsi
        
        Parameters
        ----------
        data : numpy.ndarray
            Data seismik 2D
        colormap_name : str
            Nama colormap yang dipilih
        vmin : float, optional
            Nilai minimum untuk scaling
        vmax : float, optional
            Nilai maximum untuk scaling
        scale_mode : str
            Mode scaling: "Auto" atau "Manual"
        reverse_axis : bool
            Membalik sumbu waktu
        as_image : bool
            Menyimpan plot sebagai gambar
        """
        # Tentukan colormap
        colormap = self.colormaps.get(colormap_name, self.colormaps["Seismic"])
        
        # Tentukan range nilai
        if scale_mode == "Auto":
            zmin = None
            zmax = None
        else:
            zmin = vmin
            zmax = vmax
        
        # Buat plot
        fig = px.imshow(
            data,
            color_continuous_scale=colormap,
            aspect="auto",
            origin="lower",
            zmin=zmin,
            zmax=zmax
        )
        
        # Opsi reverse axis
        if reverse_axis:
            fig.update_yaxes(autorange="reversed")
        
        fig.update_layout(
            height=600,
            xaxis_title="Trace Number",
            yaxis_title="Time Sample",
            coloraxis_colorbar=dict(title="Amplitude")
        )
        
        return fig


class SegyViewerApp:
    """Main application class untuk SEG-Y Viewer"""
    
    def __init__(self):
        self.initialize_session_state()
        self.plotter = SeismicPlotter()
        
    def initialize_session_state(self):
        """Inisialisasi session state"""
        if "segy_reader" not in st.session_state:
            st.session_state.segy_reader = None
        if "data_loaded" not in st.session_state:
            st.session_state.data_loaded = False
            
    def render_header(self):
        """Render judul aplikasi"""
        st.title("📌 Streamlit Viewer — Post-Stack SEG-Y (OOP Version)")
        st.write("Aplikasi untuk loading SEG-Y post-stack dengan kontrol tampilan lengkap.")
        
    def render_file_upload(self):
        """Render section upload file"""
        uploaded = st.file_uploader("Upload File SEG-Y", type=["sgy", "segy"])
        
        if uploaded is not None:
            st.success("File berhasil di-upload!")
            
            # Simpan file sementara
            tmp_path = "temp_uploaded.sgy"
            with open(tmp_path, "wb") as f:
                f.write(uploaded.read())
            
            return tmp_path
        
        return None
    
    def render_byte_location_input(self):
        """Render input byte location"""
        st.subheader("Masukkan Lokasi Byte (1-based index)")
        col1, col2, col3 = st.columns(3)
        
        byte_cdp = col1.number_input("Byte CDP", value=9, min_value=1, max_value=240)
        byte_cdp_x = col2.number_input("Byte CDP-X", value=73, min_value=1, max_value=240)
        byte_cdp_y = col3.number_input("Byte CDP-Y", value=77, min_value=1, max_value=240)
        
        return [byte_cdp, byte_cdp_x, byte_cdp_y]
    
    def render_plot_controls(self, max_traces):
        """Render kontrol untuk plotting"""
        st.subheader("⚙️ Kontrol Plot")
        
        # 1. Pilihan Colormap
        st.markdown("**1. Pilihan Colormap**")
        colormap_options = self.plotter.get_colormap_list()
        selected_colormap = st.selectbox(
            "Pilih Colormap:",
            options=colormap_options,
            index=0
        )
        
        st.divider()
        
        # 2. Kontrol Vmin dan Vmax
        st.markdown("**2. Kontrol Amplitude Range (Vmin & Vmax)**")
        
        # Hitung statistik data untuk default values
        if st.session_state.segy_reader is not None:
            data_sample = st.session_state.segy_reader.data_segy
            data_min = float(np.min(data_sample))
            data_max = float(np.max(data_sample))
        else:
            data_min = -1.0
            data_max = 1.0
        
        col1, col2 = st.columns(2)
        vmin = col1.slider(
            "Vmin (Amplitude Minimum):",
            min_value=data_min,
            max_value=data_max,
            value=data_min,
            step=(data_max - data_min) / 100
        )
        vmax = col2.slider(
            "Vmax (Amplitude Maximum):",
            min_value=data_min,
            max_value=data_max,
            value=data_max,
            step=(data_max - data_min) / 100
        )
        
        st.divider()
        
        # 3. Opsi Auto Scale dan Manual Scale
        st.markdown("**3. Mode Scaling**")
        scale_mode = st.radio(
            "Pilih Mode:",
            options=["Auto", "Manual"],
            horizontal=True,
            help="Auto: menggunakan range data otomatis. Manual: menggunakan vmin/vmax dari slider."
        )
        
        st.divider()
        
        # 4. Opsi Tambahan
        st.markdown("**4. Opsi Tampilan**")
        
        col1, col2 = st.columns(2)
        
        reverse_axis = col1.checkbox(
            "Balik Sumbu Waktu",
            value=True,
            help="Membalik orientasi sumbu vertikal (waktu)"
        )
        
        save_as_image = col2.checkbox(
            "Simpan sebagai Gambar",
            value=False,
            help="Menyimpan plot dalam format gambar"
        )
        
        return {
            "colormap": selected_colormap,
            "vmin": vmin,
            "vmax": vmax,
            "scale_mode": scale_mode,
            "reverse_axis": reverse_axis,
            "save_as_image": save_as_image
        }
    
    def run(self):
        """Menjalankan aplikasi"""
        self.render_header()
        
        # Upload file
        tmp_path = self.render_file_upload()
        
        if tmp_path is not None:
            # Input byte locations
            byte_locs = self.render_byte_location_input()
            
            # Tombol load
            btn_load = st.button("🔄 Loading Segy to Memory", type="primary")
            
            if btn_load:
                with st.spinner("Memuat data SEG-Y..."):
                    reader = SegyReader(tmp_path)
                    reader.read_header_and_data(byte_locs)
                    st.session_state.segy_reader = reader
                    st.session_state.data_loaded = True
                st.success("✅ Loading Sukses!")
            
            # Tampilkan data jika sudah dimuat
            if st.session_state.data_loaded and st.session_state.segy_reader is not None:
                reader = st.session_state.segy_reader
                
                # Header View
                with st.expander("📋 Header View"):
                    st.dataframe(reader.header_df, use_container_width=True)
                
                # Seismic Data View
                with st.expander("📊 Seismic Data Viewer", expanded=True):
                    st.write("**Plot Data Seismik**")
                    
                    n_samples, n_traces = reader.data_segy.shape
                    st.info(f"📏 Data Shape: {n_samples} samples × {n_traces} traces")
                    
                    # Input range CDP
                    col1, col2 = st.columns(2)
                    cdp_min = col1.number_input(
                        "Trace Start:", 
                        min_value=0, 
                        max_value=n_traces-1,
                        value=0
                    )
                    cdp_max = col2.number_input(
                        "Trace End:", 
                        min_value=1, 
                        max_value=n_traces,
                        value=min(500, n_traces)
                    )
                    
                    # Kontrol plot
                    plot_params = self.render_plot_controls(n_traces)
                    
                    # Tombol plot
                    btn_plot = st.button("🎨 Generate Plot", type="primary")
                    
                    if btn_plot:
                        if cdp_min >= cdp_max:
                            st.error("❌ Trace Start harus lebih kecil dari Trace End!")
                        else:
                            with st.spinner("Membuat plot..."):
                                # Extract data
                                data = reader.data_segy[:, cdp_min:cdp_max]
                                
                                # Plot
                                fig = self.plotter.plot_seismic(
                                    data,
                                    colormap_name=plot_params["colormap"],
                                    vmin=plot_params["vmin"],
                                    vmax=plot_params["vmax"],
                                    scale_mode=plot_params["scale_mode"],
                                    reverse_axis=plot_params["reverse_axis"],
                                    as_image=plot_params["save_as_image"]
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Info tambahan
                                st.success(f"✅ Plot berhasil dibuat untuk traces {cdp_min} - {cdp_max}")
                                
                                # Opsi download jika save as image dipilih
                                if plot_params["save_as_image"]:
                                    st.info("💾 Gunakan tombol 📷 di toolbar plot untuk menyimpan gambar")


# Jalankan aplikasi
if __name__ == "__main__":
    app = SegyViewerApp()
    app.run()
