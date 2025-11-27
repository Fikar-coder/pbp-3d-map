import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata # Library baru untuk bikin garis kontur halus

# Konfigurasi Halaman
st.set_page_config(page_title="Manual Contour Viz", layout="wide")

st.title("Peta Struktur & Kontak Fluida (Kontur)")
st.markdown("Input titik koordinat, dan sistem akan membuat **Garis Kontur** secara otomatis.")

# --- 1. INISIALISASI SESSION STATE ---
if 'data_points' not in st.session_state:
    st.session_state['data_points'] = []

# --- 2. SIDEBAR: INPUT DATA ---
st.sidebar.header("1. Input Data")

with st.sidebar.form(key='input_form'):
    col1, col2 = st.columns(2)
    with col1:
        x_val = st.number_input("X (Koordinat)", value=0.0)
    with col2:
        y_val = st.number_input("Y (Koordinat)", value=0.0)
    
    z_val = st.number_input("Z (Kedalaman/Depth)", value=1000.0)
    
    submit_button = st.form_submit_button(label='➕ Tambah Titik')

if submit_button:
    st.session_state['data_points'].append({'X': x_val, 'Y': y_val, 'Z': z_val})
    st.sidebar.success(f"Titik ({x_val}, {y_val}, {z_val}) masuk!")

# Tombol Reset & Demo
c_b1, c_b2 = st.sidebar.columns(2)
if c_b1.button("Hapus Data"):
    st.session_state['data_points'] = []
    st.rerun()

if c_b2.button("Load Data Demo"):
    # Data Anticline (Kubah) yang lebih banyak biar konturnya bagus
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

# --- 3. PROSES DATA ---
df = pd.DataFrame(st.session_state['data_points'])

with st.expander("Lihat Tabel Data"):
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Data kosong.")

# --- 4. VISUALISASI ---
if not df.empty:
    min_z, max_z = df['Z'].min(), df['Z'].max()
    
    st.sidebar.markdown("---")
    st.sidebar.header("2. Setting Kontak Fluida")
    goc_input = st.sidebar.number_input("GOC (Gas-Oil)", value=float(min_z + (max_z-min_z)*0.3))
    woc_input = st.sidebar.number_input("WOC (Water-Oil)", value=float(min_z + (max_z-min_z)*0.7))

    tab1, tab2 = st.tabs(["Peta Kontur 2D (Jelas)", "Model 3D"])

    # === PERSIAPAN GRID (Interpolasi) ===
    # Kita butuh minimal 4 titik agar interpolasi griddata berjalan lancar
    if len(df) >= 4:
        # 1. Bikin Grid X dan Y yang rapat (100x100 titik)
        grid_x = np.linspace(df['X'].min(), df['X'].max(), 100)
        grid_y = np.linspace(df['Y'].min(), df['Y'].max(), 100)
        grid_x, grid_y = np.meshgrid(grid_x, grid_y)

        # 2. Interpolasi nilai Z ke dalam Grid tersebut
        # method='cubic' membuat garis melengkung halus
        # method='linear' membuat garis patah-patah (lebih aman jika data sedikit)
        try:
            grid_z = griddata((df['X'], df['Y']), df['Z'], (grid_x, grid_y), method='cubic')
        except:
            # Fallback ke linear jika titik input membentuk garis lurus (collinear)
            grid_z = griddata((df['X'], df['Y']), df['Z'], (grid_x, grid_y), method='linear')

        # === PLOT 2D CONTOUR ===
        with tab1:
            fig_2d = go.Figure()

            # A. Layer Kontur (Garis & Warna Tanah)
            fig_2d.add_trace(go.Contour(
                z=grid_z,
                x=np.linspace(df['X'].min(), df['X'].max(), 100),
                y=np.linspace(df['Y'].min(), df['Y'].max(), 100),
                colorscale='Greys', # Pakai abu-abu biar titik warnanya menonjol
                opacity=0.5,        # Transparan dikit
                contours=dict(
                    start=min_z,
                    end=max_z,
                    size=(max_z - min_z) / 10, # Interval kontur otomatis
                    showlabels=True, # Tampilkan angka kedalaman di garis
                    labelfont=dict(size=12, color='white')
                ),
                name='Structure Map'
            ))

            # B. Layer Titik Sumur (User Input) - Berwarna sesuai fluida
            # Klasifikasi Fluida
            conditions = [
                (df['Z'] < goc_input),
                (df['Z'] >= goc_input) & (df['Z'] <= woc_input),
                (df['Z'] > woc_input)
            ]
            choices = ['Gas Cap', 'Oil Zone', 'Aquifer (Water)']
            colors_map = {'Gas Cap': 'red', 'Oil Zone': 'green', 'Aquifer (Water)': 'blue'}
            df['Fluid'] = np.select(conditions, choices, default='Unknown')

            for fluid in choices:
                subset = df[df['Fluid'] == fluid]
                if not subset.empty:
                    fig_2d.add_trace(go.Scatter(
                        x=subset['X'], y=subset['Y'],
                        mode='markers+text', # Tampilkan titik + teks
                        text=subset['Z'].astype(int), # Tampilkan angka kedalaman
                        textposition="top center",
                        marker=dict(size=10, color=colors_map[fluid], line=dict(width=2, color='black')),
                        name=fluid
                    ))

            fig_2d.update_layout(
                title="Peta Struktur Kontur & Sebaran Fluida",
                xaxis_title="X Coordinate",
                yaxis_title="Y Coordinate",
                height=700
            )
            st.plotly_chart(fig_2d, use_container_width=True)
            st.caption("Garis melengkung adalah kedalaman struktur (Kontur). Titik berwarna adalah sumur/input data Anda.")

        # === PLOT 3D ===
        with tab2:
            fig_3d = go.Figure()
            
            # Plot Surface dari hasil interpolasi (Lebih halus dari Mesh3d biasa)
            fig_3d.add_trace(go.Surface(
                z=grid_z,
                x=grid_x,
                y=grid_y,
                colorscale='Greys',
                opacity=0.8,
                name='Structure'
            ))

            # Plot Titik Asli
            fig_3d.add_trace(go.Scatter3d(
                x=df['X'], y=df['Y'], z=df['Z'],
                mode='markers',
                marker=dict(size=5, color='black'),
                name='Titik Data'
            ))

            # Bidang GOC/WOC (Plane)
            # Kita pakai range dari grid
            x_min, x_max = df['X'].min(), df['X'].max()
            y_min, y_max = df['Y'].min(), df['Y'].max()

            def create_plane(z_lvl, color, name):
                return go.Surface(
                    z=z_lvl * np.ones_like(grid_z), # Bidang datar seluas grid
                    x=grid_x,
                    y=grid_y,
                    colorscale=[[0, color], [1, color]],
                    opacity=0.4,
                    showscale=False,
                    name=name
                )

            fig_3d.add_trace(create_plane(goc_input, 'red', 'GOC'))
            fig_3d.add_trace(create_plane(woc_input, 'blue', 'WOC'))

            fig_3d.update_layout(
                scene=dict(
                    xaxis_title='X', yaxis_title='Y', zaxis_title='Depth',
                    zaxis=dict(autorange="reversed")
                ),
                height=700
            )
            st.plotly_chart(fig_3d, use_container_width=True)

    else:
        st.warning("⚠️ Masukkan minimal 4 titik data yang tersebar agar garis kontur bisa terbentuk.")
        st.dataframe(df)

else:
    st.info("Mulai dengan memasukkan titik koordinat di sidebar.")