import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GeoViz Pro", layout="wide", page_icon="🌍")

# CSS Custom untuk sedikit mempercantik tampilan
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- JUDUL UTAMA ---
st.title("🌍 3D Reservoir Visualization")
st.markdown("*Interactive Structural Map, Fluid Contact & Reserves Calculator*")

# --- 1. INISIALISASI SESSION STATE ---
if 'data_points' not in st.session_state:
    st.session_state['data_points'] = []

# --- 2. SIDEBAR KEREN ---
with st.sidebar:
    st.header("🛠 Panel Input")
    # --- BAGIAN A: INPUT DATA ---
    st.markdown("### 📍 Input Koordinat")
    
    with st.form(key='input_form', clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            x_val = st.number_input("X (Timur-Barat)", value=0.0, step=10.0)
        with c2:
            y_val = st.number_input("Y (Utara-Selatan)", value=0.0, step=10.0)
        
        z_val = st.number_input("Z (Kedalaman/Depth)", value=1000.0, step=10.0, help="Makin besar angka, makin dalam")
        
        # Tombol Submit dengan tipe Primary (Warna mencolok)
        submit_button = st.form_submit_button(label='➕ Tambah Titik', type="primary")

    if submit_button:
        st.session_state['data_points'].append({'X': x_val, 'Y': y_val, 'Z': z_val})
        st.toast(f"Titik ({x_val}, {y_val}, {z_val}) berhasil disimpan!", icon='✅')

    # --- BAGIAN B: STATUS DATA ---
    df = pd.DataFrame(st.session_state['data_points'])
    
    if not df.empty:
        st.divider()
        st.markdown("### 📊 Status Data")
        
        # Tampilkan Metrics Sederhana
        m1, m2 = st.columns(2)
        m1.metric("Total Titik", len(df))
        m2.metric("Kedalaman Max", f"{df['Z'].max()} m")
        
        # --- BAGIAN C: KONTAK FLUIDA (Hanya muncul jika ada data) ---
        st.divider()
        st.markdown("### 💧 Kontak Fluida")
        
        min_z, max_z = df['Z'].min(), df['Z'].max()
        
        # Input GOC & WOC dengan warna visual
        st.markdown(":red[Gas-Oil Contact (GOC)]")
        goc_input = st.number_input("", value=float(min_z + (max_z-min_z)*0.3), key="goc", label_visibility="collapsed")
        
        st.markdown(":blue[Water-Oil Contact (WOC)]")
        woc_input = st.number_input("", value=float(min_z + (max_z-min_z)*0.7), key="woc", label_visibility="collapsed")
        
        if goc_input > woc_input:
            st.warning("⚠ Awas: GOC > WOC!")

        # --- [BAGIAN BARU] INPUT PETROFISIKA UNTUK HITUNG CADANGAN ---
        st.divider()
        with st.expander("🧮 Parameter Petrofisika (Baru)", expanded=True):
            st.caption("Digunakan untuk menghitung STOIIP/GIIP")
            porosity = st.slider("Porositas (ϕ)", 0.05, 0.40, 0.20, 0.01)
            sw = st.slider("Water Saturation (Sw)", 0.1, 1.0, 0.3, 0.05)
            ntg = st.slider("Net-to-Gross (NTG)", 0.1, 1.0, 0.8, 0.05)
            bo = st.number_input("Faktor Vol. Formasi Minyak (Bo)", 1.0, 2.0, 1.2)
            bg = st.number_input("Faktor Ekspansi Gas (Bg)", 0.001, 0.1, 0.005, format="%.4f")
    
    st.markdown("---")
        # upload file
    with st.expander("📂 Upload File", expanded=True):
        uploaded_file = st.file_uploader("Upload CSV/Excel (Wajib: X, Y, Z)", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                # Menampilkan preview 5 baris pertama agar user yakin isinya benar
                st.caption("🔎 Preview data yang kamu upload:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                # Validasi kolom
                df_upload.columns = [c.upper() for c in df_upload.columns]
                required_cols = {'X', 'Y', 'Z'}
                
                if required_cols.issubset(df_upload.columns):
                    st.success(f"File valid! {len(df_upload)} baris data.")
                    if st.button("📥 Muat Data ke Aplikasi", type="primary"):
                        new_data = df_upload[['X', 'Y', 'Z']].to_dict('records')
                        st.session_state['data_points'].extend(new_data)
                        st.toast(f"Berhasil menambahkan {len(new_data)} titik!", icon='✅')
                        st.rerun() 
                else:
                    st.error(f"Format salah! File harus punya kolom: {required_cols}")
            except Exception as e:
                st.error(f"Error membaca file: {e}")

    # --- BAGIAN D: UTILITAS (Disembunyikan di Expander) ---
    with st.expander("⚙ Pengaturan Data", expanded=False):
        if st.button("🔄 Reset Semua Data"):
            st.session_state['data_points'] = []
            st.rerun()
        
        if st.button("📂 Load Data Demo"):
            st.session_state['data_points'] = [
                {'X': 100, 'Y': 100, 'Z': 1300}, {'X': 300, 'Y': 100, 'Z': 1300},
                {'X': 100, 'Y': 300, 'Z': 1300}, {'X': 300, 'Y': 300, 'Z': 1300},
                {'X': 200, 'Y': 200, 'Z': 1000}, # Puncak
                {'X': 200, 'Y': 100, 'Z': 1150}, {'X': 200, 'Y': 300, 'Z': 1150},
                {'X': 100, 'Y': 200, 'Z': 1150}, {'X': 300, 'Y': 200, 'Z': 1150},
                {'X': 150, 'Y': 150, 'Z': 1100}, {'X': 250, 'Y': 250, 'Z': 1100},
                {'X': 150, 'Y': 250, 'Z': 1100}, {'X': 250, 'Y': 150, 'Z': 1100}
            ]
            st.rerun()

# --- 3. LOGIC VISUALISASI UTAMA ---
if df.empty:
    st.info("👈 Silakan masukkan data koordinat melalui panel di sebelah kiri.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100) # Placeholder aja
else:
    # --- PROSES GRIDDATA (Interpolasi) ---
    # Minimal 4 titik untuk kontur yang baik
    if len(df) >= 4:
        df_unique = df.groupby(['X', 'Y'], as_index=False)['Z'].mean()
        grid_x = np.linspace(df['X'].min(), df['X'].max(), 100)
        grid_y = np.linspace(df['Y'].min(), df['Y'].max(), 100)
        grid_x, grid_y = np.meshgrid(grid_x, grid_y)

        try:
            grid_z = griddata((df_unique['X'], df_unique['Y']), df_unique['Z'], (grid_x, grid_y), method='cubic')
        except:
            grid_z = griddata((df_unique['X'], df_unique['Y']), df_unique['Z'], (grid_x, grid_y), method='linear')


        # --- FITUR PERHITUNGAN VOLUME (VOLUMETRICS) ---
        st.markdown("### 📊 Estimasi Volume & Cadangan")
        
        # 1. Hitung dimensi sel grid
        x_min, x_max = df['X'].min(), df['X'].max()
        y_min, y_max = df['Y'].min(), df['Y'].max()
        nx, ny = 100, 100
        
        dx = (x_max - x_min) / (nx - 1)
        dy = (y_max - y_min) / (ny - 1)
        cell_area = dx * dy  # Luas per satu kotak grid
        
        # 2. Hitung Volume di atas WOC (Total Reservoir Potensial)
        thick_above_woc = woc_input - grid_z
        thick_above_woc[thick_above_woc < 0] = 0  # Filter yang di bawah WOC
        vol_total_res = np.nansum(thick_above_woc) * cell_area
        
        # 3. Hitung Volume di atas GOC (Gas Cap)
        thick_above_goc = goc_input - grid_z
        thick_above_goc[thick_above_goc < 0] = 0
        vol_gas_cap = np.nansum(thick_above_goc) * cell_area
        
        # 4. Hitung Volume Oil (Selisih Total - Gas)
        vol_oil_zone = max(0, vol_total_res - vol_gas_cap)

        # --- [BAGIAN BARU] HITUNG STOIIP & GIIP ---
        # Rumus: GRV * NTG * Porosity * (1-Sw) / Bo
        stoiip = (vol_oil_zone * ntg * porosity * (1 - sw)) / bo
        giip = (vol_gas_cap * ntg * porosity * (1 - sw)) / bg

        # 5. Tampilkan Metrics (Gross Rock Volume)
        col_vol1, col_vol2, col_vol3 = st.columns(3)
        
        # Helper untuk format juta (Million)
        def fmt_vol(v): return f"{v/1e6:.2f} Juta m³"

        col_vol1.metric("🔴 Gross Gas Volume", fmt_vol(vol_gas_cap), help="Volume batuan gas cap")
        col_vol2.metric("🟢 Gross Oil Volume", fmt_vol(vol_oil_zone), help="Volume batuan oil zone")
        col_vol3.metric("🔵 Total Reservoir", fmt_vol(vol_total_res), help="Total volume batuan reservoir")

        # --- [BAGIAN BARU] METRICS CADANGAN ---
        st.caption("Ekspektasi Cadangan Minyak & Gas (In-Place):")
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("🔥 GIIP (Gas In Place)", f"{giip/1e9:.2f} BCF", help="Miliar Kaki Kubik")
        c_res2.metric("🛢 STOIIP (Oil In Place)", f"{stoiip/1e6:.2f} MMbbls", help="Juta Barel Minyak")

        
        # --- [DIUPDATE] TABS VISUALISASI DITAMBAH 1 ---
        tab1, tab2, tab3, tab4 = st.tabs(["🗺 Peta Kontur 2D", "🧊 Model 3D", "📋 Data Mentah", "✂ Penampang (Baru)"])

        # === TAB 1: 2D ===
        with tab1:
            fig_2d = go.Figure()

            # Layer Kontur
            fig_2d.add_trace(go.Contour(
                z=grid_z, x=np.linspace(df['X'].min(), df['X'].max(), 100),
                y=np.linspace(df['Y'].min(), df['Y'].max(), 100),
                colorscale='Greys', opacity=0.4,
                contours=dict(start=min_z, end=max_z, size=(max_z - min_z)/10, showlabels=True),
                name='Structure'
            ))

            # Layer Titik Fluida
            conditions = [
                (df['Z'] < goc_input),
                (df['Z'] >= goc_input) & (df['Z'] <= woc_input),
                (df['Z'] > woc_input)
            ]
            choices = ['Gas Cap', 'Oil Zone', 'Aquifer']
            colors_map = {'Gas Cap': 'red', 'Oil Zone': 'green', 'Aquifer': 'blue'}
            df['Fluid'] = np.select(conditions, choices, default='Unknown')

            for fluid in choices:
                subset = df[df['Fluid'] == fluid]
                if not subset.empty:
                    fig_2d.add_trace(go.Scatter(
                        x=subset['X'], y=subset['Y'],
                        mode='markers+text', text=subset['Z'].astype(int), textposition="top center",
                        marker=dict(size=12, color=colors_map[fluid], line=dict(width=1, color='black')),
                        name=fluid
                    ))

            fig_2d.update_layout(height=650, margin=dict(l=20, r=20, t=40, b=20),
                                xaxis_title="X Coordinate", yaxis_title="Y Coordinate")
            st.plotly_chart(fig_2d, use_container_width=True)

        # === TAB 2: 3D [DIUPDATE: WARNA & TIANG SUMUR] ===
        with tab2:
            fig_3d = go.Figure()
            
            # Surface Tanah (Warna dirubah jadi Earth_r biar keren)
            fig_3d.add_trace(go.Surface(
                z=grid_z, x=grid_x, y=grid_y, 
                colorscale='Earth_r', # Ganti warna
                opacity=0.9, name='Structure'
            ))
            
            # Plane GOC/WOC
            def create_plane(z_lvl, color, name):
                return go.Surface(
                    z=z_lvl * np.ones_like(grid_z), x=grid_x, y=grid_y,
                    colorscale=[[0, color], [1, color]], opacity=0.4, showscale=False, name=name
                )

            fig_3d.add_trace(create_plane(goc_input, 'red', 'GOC'))
            fig_3d.add_trace(create_plane(woc_input, 'blue', 'WOC'))

            # [BARU] Loop untuk membuat garis sumur (stick)
            for i, row in df.iterrows():
                fig_3d.add_trace(go.Scatter3d(
                    x=[row['X'], row['X']], y=[row['Y'], row['Y']], z=[min_z, row['Z']], # Garis dari atas ke titik
                    mode='lines+markers', marker=dict(size=3, color='black'), line=dict(color='black', width=4),
                    showlegend=False
                ))

            fig_3d.update_layout(
                scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Depth', zaxis=dict(autorange="reversed")),
                height=650, margin=dict(l=0, r=0, b=0, t=0)
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        with tab3:
            st.dataframe(df, use_container_width=True)

        # === [TAB BARU] TAB 4: CROSS SECTION ===
        with tab4:
            

            st.markdown("##### ✂ Penampang Melintang (Cross-Section)")
            st.caption("Geser slider untuk memotong peta dari Barat ke Timur pada posisi Y tertentu.")
            
            # Slider pemilihan irisan Y
            slice_y = st.slider("Pilih Posisi Irisan Y", float(y_min), float(y_max), float((y_min+y_max)/2))
            
            # Logic mengambil data irisan
            idx_y = (np.abs(grid_y[:, 0] - slice_y)).argmin() # Cari index grid Y terdekat
            z_profile = grid_z[idx_y, :] # Ambil profil Z sepanjang X
            
            fig_xs = go.Figure()
            
            # Gambar Profil Tanah
            fig_xs.add_trace(go.Scatter(x=grid_x[0, :], y=z_profile, mode='lines', fill='tozeroy', line=dict(color='brown'), name='Top Structure'))
            
            # Gambar Garis Kontak Fluida
            fig_xs.add_hline(y=goc_input, line_dash="dash", line_color="red", annotation_text="GOC")
            fig_xs.add_hline(y=woc_input, line_dash="dash", line_color="blue", annotation_text="WOC")
            
            fig_xs.update_yaxes(autorange="reversed", title="Depth (m)")
            fig_xs.update_layout(title=f"Irisan pada Y = {slice_y:.1f}", xaxis_title="X Coordinate", height=500)
            st.plotly_chart(fig_xs, use_container_width=True)

    else:
        st.warning("⚠ Data belum cukup untuk membuat kontur. Masukkan minimal 4 titik yang menyebar.")
        st.dataframe(df, use_container_width=True)