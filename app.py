import streamlit as st
import time
import pandas as pd
import os
import pytz # Tambahkan ini untuk zona waktu
from datetime import datetime

st.set_page_config(page_title="Pomodoro Pro Logs (WITA)", page_icon="⏳")

# Pengaturan Zona Waktu Samarinda (WITA)
WITA = pytz.timezone('Asia/Makassar')

DATA_FILE = "riwayat_pomodoro_final.csv"

# Fungsi untuk mendapatkan waktu sekarang di WITA
def get_now_wita():
    return datetime.now(WITA)

# --- FUNGSI SIMPAN ---
def simpan_sesi(kategori, tugas, durasi_target, sisa_waktu_detik, tipe_sesi, jam_mulai):
    jam_selesai = datetime.now().strftime("%H:%M")
    tanggal = datetime.now().strftime("%Y-%m-%d")
    
    durasi_detik_pakai = (durasi_target * 60) - sisa_waktu_detik
    durasi_menit_nyata = round(durasi_detik_pakai / 60, 2)
    
    status = "Completed" if sisa_waktu_detik <= 0 else "Interrupted"
    overtime = "Ya" if sisa_waktu_detik < 0 else "Tidak"
    
    data_baru = {
        "Tanggal": [tanggal],
        "Jam": [f"{jam_mulai} - {jam_selesai}"],
        "Tipe": [tipe_sesi],
        "Kategori": [kategori],
        "Tugas": [tugas],
        "Target (Min)": [durasi_target],
        "Realisasi (Min)": [durasi_menit_nyata],
        "Status": [status],
        "Overtime": [overtime]
    }
    
    df_baru = pd.DataFrame(data_baru)
    if not os.path.isfile(DATA_FILE):
        df_baru.to_csv(DATA_FILE, index=False)
    else:
        df_baru.to_csv(DATA_FILE, mode='a', header=False, index=False)

# --- UI SIDEBAR ---
st.sidebar.header("⚙️ Konfigurasi")
if "list_kategori" not in st.session_state:
    st.session_state.list_kategori = ["Study", "Work"]

kategori_baru = st.sidebar.text_input("Tambah Tag Baru")
if st.sidebar.button("Tambah Tag"):
    if kategori_baru and kategori_baru not in st.session_state.list_kategori:
        st.session_state.list_kategori.append(kategori_baru)

kategori_pilih = st.sidebar.selectbox("Pilih Kategori", st.session_state.list_kategori)
tugas_input = st.sidebar.text_input("Note", placeholder="Contoh: Rekonsiliasi Data")

st.sidebar.subheader("Durasi Sesi")
menit_fokus = st.sidebar.slider("Fokus (Menit)", 1, 60, 25)
menit_istirahat = st.sidebar.slider("Istirahat (Menit)", 1, 30, 5)

# --- MAIN UI ---
st.title("⏳ Pomodoro Tracker & Logger")
tab1, tab2 = st.tabs(["Timer", "Riwayat"])

with tab1:
    mode = st.radio("Mode:", ["Focus", "Break"], horizontal=True)
    durasi_target = menit_fokus if mode == "Focus" else menit_istirahat

    if "time_left" not in st.session_state or st.session_state.get('last_mode') != mode:
        st.session_state.time_left = durasi_target * 60
        st.session_state.last_mode = mode
        st.session_state.run = False
        st.session_state.start_time_str = ""

    timer_placeholder = st.empty()
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("Mulai", use_container_width=True):
            st.session_state.run = True
            st.session_state.start_time_str = datetime.now().strftime("%H:%M")
            
    with c2:
        if st.button("Selesai & Simpan", use_container_width=True):
            if st.session_state.run or st.session_state.get('start_time_str'):
                simpan_sesi(kategori_pilih, tugas_input, durasi_target, st.session_state.time_left, mode, st.session_state.start_time_str)
                st.session_state.run = False
                st.session_state.time_left = durasi_target * 60 
                st.success("Sesi berhasil dicatat!")
                st.rerun()
    with c3:
        if st.button("Reset", use_container_width=True):
            st.session_state.run = False
            st.session_state.time_left = durasi_target * 60

    while st.session_state.run:
        abs_time = abs(st.session_state.time_left)
        mins, secs = divmod(int(abs_time), 60)
        prefix = "-" if st.session_state.time_left < 0 else ""
        timer_placeholder.metric(f"Sesi {mode} Aktif", f"{prefix}{mins:02d}:{secs:02d}")
        time.sleep(1)
        st.session_state.time_left -= 1

with tab2:
    st.subheader("📜 Log Aktivitas")
    if os.path.isfile(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        st.write("Centang baris dan tekan tombol **Delete** pada keyboard (atau gunakan menu sampah) lalu klik **Simpan Perubahan**.")
        
        # Fitur Hapus Per Baris menggunakan data_editor
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        col_save, col_del_all = st.columns(2)
        
        with col_save:
            if st.button("💾 Simpan Perubahan (Hapus Baris)", use_container_width=True):
                edited_df.to_csv(DATA_FILE, index=False)
                st.success("Riwayat berhasil diperbarui!")
                st.rerun()
        
        with col_del_all:
            if st.button("🗑️ Hapus Semua Riwayat", type="primary", use_container_width=True):
                os.remove(DATA_FILE)
                st.rerun()
                
        st.download_button("Download CSV", df.to_csv(index=False), "pomodoro_report.csv")
    else:
        st.info("Belum ada riwayat sesi.")
