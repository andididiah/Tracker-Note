import streamlit as st
import time
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Pomodoro Overtime Tracker", page_icon="⏳")

DATA_FILE = "riwayat_pomodoro_overtime.csv"

def simpan_sesi(kategori, tugas, durasi_target, waktu_akhir_detik, tipe_sesi):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Menghitung durasi nyata (bisa lebih besar dari target karena overtime)
    # waktu_akhir_detik adalah sisa waktu (jika positif = interrupted, jika negatif = overtime)
    durasi_detik_pakai = (durasi_target * 60) - waktu_akhir_detik
    durasi_menit_nyata = durasi_detik_pakai / 60
    
    status = "Completed" if waktu_akhir_detik <= 0 else "Interrupted"
    is_overtime = "Ya" if waktu_akhir_detik < 0 else "Tidak"
    
    data_baru = {
        "Waktu": [timestamp],
        "Tipe": [tipe_sesi],
        "Kategori": [kategori],
        "Tugas": [tugas],
        "Target (Menit)": [durasi_target],
        "Realisasi (Menit)": [round(durasi_menit_nyata, 2)],
        "Status": [status],
        "Overtime": [is_overtime]
    }
    
    df_baru = pd.DataFrame(data_baru)
    if not os.path.isfile(DATA_FILE):
        df_baru.to_csv(DATA_FILE, index=False)
    else:
        df_baru.to_csv(DATA_FILE, mode='a', header=False, index=False)

## --- SIDEBAR ---
st.sidebar.header("⚙️ Konfigurasi")

if "list_kategori" not in st.session_state:
    st.session_state.list_kategori = ["Bekerja", "Belajar", "Tugas Lainnya"]

kategori_baru = st.sidebar.text_input("Tambah Tag/Kategori Baru")
if st.sidebar.button("Tambah Tag"):
    if kategori_baru and kategori_baru not in st.session_state.list_kategori:
        st.session_state.list_kategori.append(kategori_baru)

kategori_pilih = st.sidebar.selectbox("Pilih Kategori", st.session_state.list_kategori)
tugas_input = st.sidebar.text_input("Nama Tugas", placeholder="Misal: Menyusun Laporan")

st.sidebar.subheader("Durasi Sesi")
menit_fokus = st.sidebar.slider("Durasi Fokus (Menit)", 1, 60, 25)
menit_istirahat = st.sidebar.slider("Durasi Istirahat (Menit)", 1, 30, 5)

## --- MAIN UI ---
st.title("⏳ Pomodoro Flow Tracker")

tab1, tab2 = st.tabs(["Timer", "Riwayat & Analisis"])

with tab1:
    mode = st.radio("Pilih Mode:", ["Focus", "Break"], horizontal=True)
    durasi_target = menit_fokus if mode == "Focus" else menit_istirahat

    # Inisialisasi State
    if "time_left" not in st.session_state or st.session_state.get('last_mode') != mode:
        st.session_state.time_left = durasi_target * 60
        st.session_state.last_mode = mode
        st.session_state.run = False

    timer_placeholder = st.empty()
    status_placeholder = st.empty()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Mulai", use_container_width=True):
            st.session_state.run = True
    with c2:
        if st.button("Selesai & Simpan", use_container_width=True):
            if st.session_state.run or st.session_state.time_left != durasi_target * 60:
                simpan_sesi(kategori_pilih, tugas_input, durasi_target, st.session_state.time_left, mode)
                st.session_state.run = False
                st.session_state.time_left = durasi_target * 60 # Reset ke awal
                st.success("Sesi berhasil dicatat!")
                st.rerun()
    with c3:
        if st.button("Reset", use_container_width=True):
            st.session_state.run = False
            st.session_state.time_left = durasi_target * 60

    # Logika Timer (Loop)
    while st.session_state.run:
        # Menghitung Menit & Detik (Bisa negatif untuk overtime)
        abs_time = abs(st.session_state.time_left)
        mins, secs = divmod(int(abs_time), 60)
        
        # Jika time_left < 0, tampilkan tanda minus (Overtime)
        prefix = "-" if st.session_state.time_left < 0 else ""
        timer_text = f"{prefix}{mins:02d}:{secs:02d}"
        
        # Ubah warna jika overtime
        if st.session_state.time_left < 0:
            timer_placeholder.metric("Overtime Running...", timer_text, delta="Overtime Aktif", delta_color="inverse")
        else:
            timer_placeholder.metric(f"Sesi {mode} Aktif", timer_text)
            
        time.sleep(1)
        st.session_state.time_left -= 1
        
        # Trigger jika baru saja melewati 0 (Opsional: Bunyi atau Balon)
        if st.session_state.time_left == 0:
            st.toast(f"Sesi {mode} telah mencapai target! Timer berlanjut...")

    # Tampilan saat diam
    if not st.session_state.run:
        abs_time = abs(st.session_state.time_left)
        mins, secs = divmod(int(abs_time), 60)
        prefix = "-" if st.session_state.time_left < 0 else ""
        timer_placeholder.metric(f"Sesi {mode}", f"{prefix}{mins:02d}:{secs:02d}")

with tab2:
    st.subheader("📜 Log Aktivitas Lengkap")
    if os.path.isfile(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        # Styling tabel
        def highlight_overtime(row):
            return ['background-color: #d4edda' if row.Overtime == "Ya" else '' for _ in row]
        
        st.dataframe(df.tail(10), use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "pomodoro_overtime_report.csv")
    else:
        st.info("Belum ada riwayat sesi.")
