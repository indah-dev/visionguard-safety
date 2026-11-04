import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import base64
import os
import io
import pandas as pd
from datetime import datetime
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from fpdf import FPDF

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="VisionGuard Safety - Kepatuhan APD",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNGSI CUSTOM BACKGROUND & KOTAK TENGAH GELAP ---
def set_custom_theme():
    bg_filename = "background.jpg"
    
    if os.path.exists(bg_filename):
        with open(bg_filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                position: relative;
                background-color: #0F172A;
            }}
            
            [data-testid="stAppViewContainer"]::before {{
                content: "";
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background-image: url("data:image/jpeg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                opacity: 0.85; 
                pointer-events: none;
                z-index: 0;
            }}

            [data-testid="stAppViewContainer"] > * {{
                position: relative;
                z-index: 1;
            }}

            section[data-testid="stSidebar"] {{
                background-color: #0A192F !important; 
                border-right: 1px solid #1E293B;
            }}
            
            section[data-testid="stSidebar"] * {{
                color: #F1F5F9 !important;
            }}

            [data-testid="stHeader"] {{
                background-color: rgba(0, 0, 0, 0) !important;
            }}

            div.block-container {{
                background-color: rgba(10, 25, 47, 0.95) !important; 
                border-radius: 15px !important; 
                padding: 40px !important;
                margin-top: 30px !important;
                margin-bottom: 30px !important;
                box-shadow: 0px 10px 40px rgba(0, 0, 0, 0.8) !important; 
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }}

            div.block-container h1, 
            div.block-container h2, 
            div.block-container h3, 
            div.block-container p, 
            div.block-container label,
            div.block-container [data-testid="stMetricValue"],
            div.block-container [data-testid="stMetricLabel"] {{
                color: #FFFFFF !important;
            }}

            /* STYLING TOMBOL */
            .stDownloadButton button, 
            div.stButton > button, 
            button[data-testid="baseButton-secondary"] {{
                background-color: rgba(30, 41, 59, 0.9) !important; 
                border: 1px solid #38BDF8 !important; 
                border-radius: 8px !important;
                color: #FFFFFF !important; 
                font-weight: 600 !important;
            }}
            
            .stDownloadButton button p, 
            div.stButton > button p, 
            button[data-testid="baseButton-secondary"] p {{
                color: #FFFFFF !important; 
            }}

            .stDownloadButton button:hover, 
            div.stButton > button:hover, 
            button[data-testid="baseButton-secondary"]:hover {{
                background-color: #38BDF8 !important; 
                border-color: #38BDF8 !important;
                color: #0F172A !important;
            }}
            
            .stDownloadButton button:hover p, 
            div.stButton > button:hover p, 
            button[data-testid="baseButton-secondary"]:hover p {{
                color: #0F172A !important; 
            }}

            /* KOTAK UPLOAD FILE */
            [data-testid="stFileUploader"] > section,
            [data-testid="stFileUploadDropzone"] {{
                background-color: rgba(30, 41, 59, 0.95) !important; 
                border: 2px dashed #38BDF8 !important; 
                border-radius: 12px !important;
                padding: 20px !important;
            }}
            
            [data-testid="stFileUploader"] > section *,
            [data-testid="stFileUploadDropzone"] * {{
                color: #F8FAFC !important;
            }}

            [data-testid="stFileUploader"] button,
            [data-testid="stFileUploadDropzone"] button {{
                background-color: #38BDF8 !important; 
                color: #0F172A !important; 
                border: none !important;
                font-weight: bold !important;
                border-radius: 6px !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.warning("⚠️ File 'background.jpg' tidak ditemukan di folder proyek.")

set_custom_theme()

# --- 3. CUSTOM CSS KOMPONEN ---
st.markdown("""
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 6px;
    }
    .status-card-safe {
        background: rgba(34, 197, 94, 0.2);
        border: 1px solid #22C55E;
        padding: 16px;
        border-radius: 12px;
        color: #4ADE80 !important;
        font-weight: 600;
        text-align: center;
    }
    .status-card-danger {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid #EF4444;
        padding: 16px;
        border-radius: 12px;
        color: #F87171 !important;
        font-weight: 600;
        text-align: center;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. HERO BANNER HEADER ---
st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🛡️ VisionGuard Safety</div>
        <div class="hero-subtitle">Sistem Pemantauan & Analisis Kepatuhan APD Proyek Konstruksi Real-Time</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. KONFIGURASI API ROBOFLOW ---
API_KEY = "mr4rN1CwX8na9vGEIdNh"
MODEL_ID = "construction-site-safety/27"

@st.cache_resource
def get_roboflow_client(api_key):
    try:
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=api_key
        ).configure(InferenceConfiguration(api_key_transport="header"))
        return client
    except Exception as e:
        st.error("Gagal terhubung ke Roboflow Client. Periksa API Key kamu.")
        return None

client = get_roboflow_client(API_KEY)

def convert_image_to_bytes(img_array):
    pil_img = Image.fromarray(img_array)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()

def generate_csv_log_report(log_records):
    if not log_records:
        df = pd.DataFrame([{
            "Waktu / Interval 10 Detik": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Sumber": "N/A",
            "Objek Terdeteksi": "Tidak ada",
            "Jumlah": 0,
            "Status K3": "AMAN",
            "Catatan Interval": "-"
        }])
    else:
        df = pd.DataFrame(log_records)
    return df.to_csv(index=False).encode('utf-8')

def generate_pdf_interval_report(log_records, source_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    
    pdf.cell(0, 8, "Laporan Audit Kepatuhan K3 (Interval 10 Detik)", ln=True, align="C")
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, f"Waktu Ekspor: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Sumber: {source_type}", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(35, 7, "Waktu / Interval", 1, 0, "C", True)
    pdf.cell(45, 7, "Objek / Atribut", 1, 0, "C", True)
    pdf.cell(25, 7, "Status K3", 1, 0, "C", True)
    pdf.cell(85, 7, "Miniatur Bukti (Per 10 Detik)", 1, 1, "C", True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    if not log_records:
        pdf.cell(35, 15, "-", 1, 0, "C")
        pdf.cell(45, 15, "Tidak ada data", 1, 0, "C")
        pdf.cell(25, 15, "AMAN", 1, 0, "C")
        pdf.cell(85, 15, "-", 1, 1, "C")
    else:
        for idx, rec in enumerate(log_records):
            tmp_thumb = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            img_to_save = rec.get("frame_image")
            if img_to_save is not None:
                Image.fromarray(img_to_save).save(tmp_thumb)
            
            row_height = 16
            current_y = pdf.get_y()
            
            if current_y > 260:
                pdf.add_page()
                current_y = pdf.get_y()
                
            pdf.cell(35, row_height, str(rec.get("Waktu / Interval 10 Detik")), 1, 0, "C")
            pdf.cell(45, row_height, str(rec.get("Objek Terdeteksi")), 1, 0, "L")
            pdf.cell(25, row_height, str(rec.get("Status K3")), 1, 0, "C")
            
            x_img = pdf.get_x()
            y_img = pdf.get_y()
            pdf.cell(85, row_height, "", 1, 1, "C")
            
            if img_to_save is not None and os.path.exists(tmp_thumb):
                pdf.image(tmp_thumb, x=x_img + 25, y=y_img + 1.5, w=35)
                try:
                    os.remove(tmp_thumb)
                except:
                    pass

    return bytes(pdf.output())

# --- 6. SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Pengaturan Deteksi")
conf_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.10,
    max_value=1.00,
    value=0.25,
    step=0.05,
    help="Filter tingkat kepercayaan minimum hasil deteksi."
)

st.sidebar.markdown("---")
st.sidebar.header("📁 Sumber Media")
source_option = st.sidebar.radio("Pilih Input:", ("Upload Gambar", "Upload Video", "Kamera Laptop (Live & Snapshot)"))

# --- 7. MODUL PROSES GAMBAR ---
if source_option == "Upload Gambar":
    uploaded_file = st.file_uploader("Unggah foto area kerja / pekerja proyek...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None and client is not None:
        col1, col2 = st.columns(2)
        
        image = Image.open(uploaded_file)
        with col1:
            st.image(image, caption="Gambar Asli Area Kerja", use_container_width=True)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
            
        with st.spinner("🤖 Menganalisis Kepatuhan APD via API..."):
            result = client.infer(tmp_path, model_id=MODEL_ID)
            
            img_np = np.array(image)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            predictions = result.get("predictions", [])
            detected_counts = {}
            violation_count = 0
            
            for pred in predictions:
                conf = pred.get("confidence", 0)
                if conf < conf_threshold:
                    continue
                    
                x = int(pred["x"] - pred["width"] / 2)
                y = int(pred["y"] - pred["height"] / 2)
                w = int(pred["width"])
                h = int(pred["height"])
                label = pred["class"]
                
                detected_counts[label] = detected_counts.get(label, 0) + 1
                is_violation = "NO-" in label.upper()
                if is_violation:
                    violation_count += 1
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)
                
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img_bgr, f"{label} {conf:.2f}", (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
            res_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        os.remove(tmp_path) 
            
        with col2:
            st.image(res_rgb, caption="Hasil Deteksi VisionGuard", use_container_width=True)
            
        st.markdown("---")
        st.subheader("📊 Laporan Deteksi APD & Kepatuhan OHS")
        
        if violation_count > 0:
            st.markdown(f'<div class="status-card-danger">🚨 TERDETEKSI {violation_count} PELANGGARAN K3/APD PADA AREA KERJA</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-card-safe">✅ SELURUH PEKERJA TERDETEKSI PATUH APD (K3 AMAN)</div>', unsafe_allow_html=True)
            
        st.write("")
        
        single_log = []
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if detected_counts:
            for lbl, cnt in detected_counts.items():
                stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                single_log.append({
                    "Waktu / Interval 10 Detik": ts_now,
                    "Sumber": "Upload Gambar",
                    "Objek Terdeteksi": f"{lbl} ({cnt}x)",
                    "Jumlah": cnt,
                    "Status K3": stat,
                    "Catatan Interval": "Gambar Tunggal",
                    "frame_image": res_rgb
                })
        else:
            single_log.append({
                "Waktu / Interval 10 Detik": ts_now,
                "Sumber": "Upload Gambar",
                "Objek Terdeteksi": "Tidak ada objek",
                "Jumlah": 0,
                "Status K3": "AMAN",
                "Catatan Interval": "Bersih",
                "frame_image": res_rgb
            })

        st.markdown("---")
        st.subheader("📥 3 Opsi Unduh Laporan & Bukti Inspeksi")
        dl1, dl2, dl3 = st.columns(3)
        
        evidence_name = f"VisionGuard_Evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img_bytes = convert_image_to_bytes(res_rgb)
        csv_buffer = generate_csv_log_report(single_log)
        pdf_bytes = generate_pdf_interval_report(single_log, "Upload Gambar")
        
        with dl1:
            st.download_button("🖼️ 1. Download Gambar (.png)", data=img_bytes, file_name=evidence_name, mime="image/png", use_container_width=True)
        with dl2:
            st.download_button("📊 2. Download CSV (.csv)", data=csv_buffer, file_name=f"VisionGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
        with dl3:
            st.download_button("📑 3. Download PDF (Gabungan)", data=pdf_bytes, file_name=f"VisionGuard_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf", use_container_width=True)

# --- 8. MODUL PROSES VIDEO ---
elif source_option == "Upload Video":
    uploaded_video = st.file_uploader("Unggah video pengawasan area proyek...", type=["mp4", "avi", "mov"])
    
    if uploaded_video is not None and client is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        
        st_frame = st.empty()
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            start_vid = st.button("▶️ Mulai Putar Video")
        with col_ctrl2:
            stop_vid = st.button("⏹️ Hentikan Video (Stop & Rekap)")
            
        if 'vid_logs' not in st.session_state:
            st.session_state.vid_logs = []
            st.session_state.vid_finished = False
            st.session_state.last_active_frame = None
            st.session_state.last_preds_summary = []
            
        if start_vid:
            st.session_state.vid_logs = []
            st.session_state.vid_finished = False
            st.session_state.last_active_frame = None
            st.session_state.last_preds_summary = []
            
            cap = cv2.VideoCapture(tfile.name)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: 
                fps = 30  
                
            interval_frames = int(fps * 10)
            frame_count = 0
            
            while cap.isOpened() and not stop_vid:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                
                if frame_count % 10 == 0:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_frame:
                        cv2.imwrite(tmp_frame.name, frame)
                        tmp_name = tmp_frame.name
                    
                    try:
                        result = client.infer(tmp_name, model_id=MODEL_ID)
                        preds = result.get("predictions", [])
                    except:
                        preds = []
                    os.remove(tmp_name)
                    
                    for pred in preds:
                        conf = pred.get("confidence", 0)
                        if conf < conf_threshold:
                            continue
                        x = int(pred["x"] - pred["width"] / 2)
                        y = int(pred["y"] - pred["height"] / 2)
                        w = int(pred["width"])
                        h = int(pred["height"])
                        label = pred["class"]
                        
                        color = (0, 0, 255) if "NO-" in label.upper() else (0, 255, 0)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x, max(y - 10, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    res_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st_frame.image(res_rgb, caption=f"Memproses Video... (Frame: {frame_count})", use_container_width=True)
                    
                    st.session_state.last_active_frame = res_rgb
                    st.session_state.last_preds_summary = preds
                    
                    if frame_count % interval_frames == 0 or frame_count == 1:
                        sec_mark = int(frame_count / fps)
                        time_label = f"T + {sec_mark} Detik"
                        
                        if preds:
                            for p in preds:
                                if p.get("confidence", 0) >= conf_threshold:
                                    lbl = p["class"]
                                    stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                                    st.session_state.vid_logs.append({
                                        "Waktu / Interval 10 Detik": time_label,
                                        "Sumber": "Upload Video",
                                        "Objek Terdeteksi": lbl,
                                        "Jumlah": 1,
                                        "Status K3": stat,
                                        "Catatan Interval": f"Interval {sec_mark}s",
                                        "frame_image": res_rgb
                                    })
                        else:
                            st.session_state.vid_logs.append({
                                "Waktu / Interval 10 Detik": time_label,
                                "Sumber": "Upload Video",
                                "Objek Terdeteksi": "Kondisi Aman / Patuh",
                                "Jumlah": 0,
                                "Status K3": "AMAN",
                                "Catatan Interval": f"Interval {sec_mark}s",
                                "frame_image": res_rgb
                            })
            cap.release()
            st.session_state.vid_finished = True
            
        if (stop_vid or st.session_state.vid_finished) and not st.session_state.vid_logs and st.session_state.last_active_frame is not None:
            time_label = "Snapshot Akhir (Manual Stop)"
            if st.session_state.last_preds_summary:
                for p in st.session_state.last_preds_summary:
                    if p.get("confidence", 0) >= conf_threshold:
                        lbl = p["class"]
                        stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                        st.session_state.vid_logs.append({
                            "Waktu / Interval 10 Detik": time_label,
                            "Sumber": "Upload Video",
                            "Objek Terdeteksi": lbl,
                            "Jumlah": 1,
                            "Status K3": stat,
                            "Catatan Interval": "Dihentikan Pengguna",
                            "frame_image": st.session_state.last_active_frame
                        })
            if not st.session_state.vid_logs:
                st.session_state.vid_logs.append({
                    "Waktu / Interval 10 Detik": time_label,
                    "Sumber": "Upload Video",
                    "Objek Terdeteksi": "Kondisi Aman / Patuh",
                    "Jumlah": 0,
                    "Status K3": "AMAN",
                    "Catatan Interval": "Dihentikan Pengguna",
                    "frame_image": st.session_state.last_active_frame
                })

        if stop_vid or st.session_state.vid_finished:
            if st.session_state.vid_logs:
                st.markdown("---")
                st.subheader("📥 Laporan Rekapitulasi Video Siap Diunduh")
                dlv1, dlv2, dlv3 = st.columns(3)
                
                last_img = st.session_state.vid_logs[-1]["frame_image"]
                evidence_vid_name = f"VisionGuard_Evidence_Video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                vid_img_bytes = convert_image_to_bytes(last_img)
                vid_csv_buffer = generate_csv_log_report(st.session_state.vid_logs)
                vid_pdf_bytes = generate_pdf_interval_report(st.session_state.vid_logs, "Upload Video")
                
                with dlv1:
                    st.download_button("🖼️ 1. Download Gambar Frame (.png)", data=vid_img_bytes, file_name=evidence_vid_name, mime="image/png", use_container_width=True)
                with dlv2:
                    st.download_button("📊 2. Download CSV (.csv)", data=vid_csv_buffer, file_name=f"VisionGuard_VideoReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
                with dlv3:
                    st.download_button("📑 3. Download PDF (Gabungan)", data=vid_pdf_bytes, file_name=f"VisionGuard_VideoAudit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf", use_container_width=True)

# --- 9. MODUL PROSES WEBCAM SNAPSHOT & LIVE ---
elif source_option == "Kamera Laptop (Live & Snapshot)":
    
    cam_mode = st.radio("Pilih Mode Penggunaan Kamera:", ("📸 Ambil Foto (Snapshot)", "🎥 Live Video (Real-Time)"))
    
    if cam_mode == "📸 Ambil Foto (Snapshot)":
        picture = st.camera_input("Ambil foto dari webcam untuk pengujian APD")
        
        if picture and client is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(picture.getvalue())
                tmp_path = tmp.name
                
            image = Image.open(picture)
            result = client.infer(tmp_path, model_id=MODEL_ID)
            os.remove(tmp_path)
            
            img_np = np.array(image)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            detected_counts = {}
            for pred in result.get("predictions", []):
                conf = pred.get("confidence", 0)
                if conf < conf_threshold:
                    continue
                x = int(pred["x"] - pred["width"] / 2)
                y = int(pred["y"] - pred["height"] / 2)
                w = int(pred["width"])
                h = int(pred["height"])
                label = pred["class"]
                detected_counts[label] = detected_counts.get(label, 0) + 1
                color = (0, 0, 255) if "NO-" in label.upper() else (0, 255, 0)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img_bgr, f"{label} {conf:.2f}", (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
            res_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            st.image(res_rgb, caption="Hasil Deteksi Kamera Snapshot", use_container_width=True)
            
            snap_log = []
            ts_snap = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if detected_counts:
                for lbl, cnt in detected_counts.items():
                    stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                    snap_log.append({
                        "Waktu / Interval 10 Detik": ts_snap,
                        "Sumber": "Snapshot",
                        "Objek Terdeteksi": f"{lbl} ({cnt}x)",
                        "Jumlah": cnt,
                        "Status K3": stat,
                        "Catatan Interval": "Snapshot",
                        "frame_image": res_rgb
                    })
            else:
                snap_log.append({
                    "Waktu / Interval 10 Detik": ts_snap,
                    "Sumber": "Snapshot",
                    "Objek Terdeteksi": "Tidak ada",
                    "Jumlah": 0,
                    "Status K3": "AMAN",
                    "Catatan Interval": "Snapshot",
                    "frame_image": res_rgb
                })

            st.markdown("---")
            st.subheader("📥 3 Opsi Unduh Laporan Snapshot")
            dls1, dls2, dls3 = st.columns(3)
            
            evidence_snap_name = f"VisionGuard_Evidence_Snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            snap_img_bytes = convert_image_to_bytes(res_rgb)
            csv_buffer = generate_csv_log_report(snap_log)
            pdf_bytes = generate_pdf_interval_report(snap_log, "Kamera Snapshot")
            
            with dls1:
                st.download_button("🖼️ 1. Download Gambar Snapshot (.png)", data=snap_img_bytes, file_name=evidence_snap_name, mime="image/png", use_container_width=True)
            with dls2:
                st.download_button("📊 2. Download CSV (.csv)", data=csv_buffer, file_name=f"VisionGuard_SnapshotReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
            with dls3:
                st.download_button("📑 3. Download PDF (Gabungan)", data=pdf_bytes, file_name=f"VisionGuard_SnapshotAudit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf", use_container_width=True)

    elif cam_mode == "🎥 Live Video (Real-Time)":
        col_live1, col_live2 = st.columns(2)
        with col_live1:
            start_live = st.button("▶️ Mulai Live CCTV")
        with col_live2:
            stop_live = st.button("⏹️ Matikan Kamera / Stop & Rekap")
            
        st_frame = st.empty()
        
        if 'live_logs' not in st.session_state:
            st.session_state.live_logs = []
            st.session_state.live_finished = False
            st.session_state.last_live_active_frame = None
            st.session_state.last_live_preds = []
            
        if start_live:
            st.session_state.live_logs = []
            st.session_state.live_finished = False
            st.session_state.last_live_active_frame = None
            st.session_state.last_live_preds = []
            
            cap = cv2.VideoCapture(0)
            
            frame_count = 0
            live_interval_frames = 300 
            start_time_live = datetime.now()
            
            while not stop_live:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                if frame_count % 10 == 0:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_frame:
                        cv2.imwrite(tmp_frame.name, frame)
                        tmp_name = tmp_frame.name
                        
                    try:
                        result = client.infer(tmp_name, model_id=MODEL_ID)
                        preds = result.get("predictions", [])
                    except:
                        preds = []
                    os.remove(tmp_name)
                    
                    for pred in preds:
                        conf = pred.get("confidence", 0)
                        if conf < conf_threshold:
                            continue
                        x = int(pred["x"] - pred["width"] / 2)
                        y = int(pred["y"] - pred["height"] / 2)
                        w = int(pred["width"])
                        h = int(pred["height"])
                        label = pred["class"]
                        
                        color = (0, 0, 255) if "NO-" in label.upper() else (0, 255, 0)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x, max(y - 10, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    res_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st_frame.image(res_rgb, caption="Live CCTV Kepatuhan APD Berjalan...", use_container_width=True)
                    
                    st.session_state.last_live_active_frame = res_rgb
                    st.session_state.last_live_preds = preds
                    
                    elapsed_secs = int((datetime.now() - start_time_live).total_seconds())
                    if frame_count % live_interval_frames == 0 or frame_count == 1:
                        time_label = f"Live T+{elapsed_secs}s"
                        if preds:
                            for p in preds:
                                if p.get("confidence", 0) >= conf_threshold:
                                    lbl = p["class"]
                                    stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                                    st.session_state.live_logs.append({
                                        "Waktu / Interval 10 Detik": time_label,
                                        "Sumber": "Live Webcam",
                                        "Objek Terdeteksi": lbl,
                                        "Jumlah": 1,
                                        "Status K3": stat,
                                        "Catatan Interval": f"Snapshot {elapsed_secs}s",
                                        "frame_image": res_rgb
                                    })
                        else:
                            st.session_state.live_logs.append({
                                "Waktu / Interval 10 Detik": time_label,
                                "Sumber": "Live Webcam",
                                "Objek Terdeteksi": "Kondisi Aman / Patuh",
                                "Jumlah": 0,
                                "Status K3": "AMAN",
                                "Catatan Interval": f"Snapshot {elapsed_secs}s",
                                "frame_image": res_rgb
                            })
            cap.release()
            st.session_state.live_finished = True
            
        if (stop_live or st.session_state.live_finished) and not st.session_state.live_logs and st.session_state.last_live_active_frame is not None:
            time_label = "Snapshot Live Akhir"
            if st.session_state.last_live_preds:
                for p in st.session_state.last_live_preds:
                    if p.get("confidence", 0) >= conf_threshold:
                        lbl = p["class"]
                        stat = "PELANGGARAN" if "NO-" in lbl.upper() else "PATUH"
                        st.session_state.live_logs.append({
                            "Waktu / Interval 10 Detik": time_label,
                            "Sumber": "Live Webcam",
                            "Objek Terdeteksi": lbl,
                            "Jumlah": 1,
                            "Status K3": stat,
                            "Catatan Interval": "Kamera Dimatikan",
                            "frame_image": st.session_state.last_live_active_frame
                        })
            if not st.session_state.live_logs:
                st.session_state.live_logs.append({
                    "Waktu / Interval 10 Detik": time_label,
                    "Sumber": "Live Webcam",
                    "Objek Terdeteksi": "Kondisi Aman / Patuh",
                    "Jumlah": 0,
                    "Status K3": "AMAN",
                    "Catatan Interval": "Kamera Dimatikan",
                    "frame_image": st.session_state.last_live_active_frame
                })
            
        if stop_live or st.session_state.live_finished:
            if st.session_state.live_logs:
                st.markdown("---")
                st.subheader("📥 Laporan Rekapitulasi Berkala Live CCTV Siap Diunduh")
                dll1, dll2, dll3 = st.columns(3)
                
                last_live_img = st.session_state.live_logs[-1]["frame_image"]
                evidence_live_name = f"VisionGuard_Evidence_Live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                live_img_bytes = convert_image_to_bytes(last_live_img)
                live_csv_buffer = generate_csv_log_report(st.session_state.live_logs)
                live_pdf_bytes = generate_pdf_interval_report(st.session_state.live_logs, "Live Webcam")
                
                with dll1:
                    st.download_button("🖼️ 1. Download Gambar Frame (.png)", data=live_img_bytes, file_name=evidence_live_name, mime="image/png", use_container_width=True)
                with dll2:
                    st.download_button("📊 2. Download CSV (.csv)", data=live_csv_buffer, file_name=f"VisionGuard_LiveReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
                with dll3:
                    st.download_button("📑 3. Download PDF (Gabungan)", data=live_pdf_bytes, file_name=f"VisionGuard_LiveAudit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf", use_container_width=True)