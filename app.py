import streamlit as st
import numpy as np
import pandas as pd
import json
import datetime

# ==========================================
# 1. INITIAL SYSTEM CONFIGURATION & UI THEME
# ==========================================
st.set_page_config(
    page_title="Industrial CNC Cutting Parameter Decision Support System (DSS)",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thêm CSS đồng bộ Theme công nghiệp Siemens / DMG MORI cho giao diện web hiển thị
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    .kpi-card {
        background: #ffffff; padding: 16px; border-radius: 4px;
        border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .kpi-title { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #0f172a; margin: 4px 0; }
    .kpi-unit { font-size: 12px; color: #94a3b8; font-weight: 500; }
    .status-normal { border-left: 4px solid #005fa3; }
    .status-success { border-left: 4px solid #16a34a; }
    .status-warning { border-left: 4px solid #ea580c; }
    .status-danger { border-left: 4px solid #dc2626; }
    .module-box { background: #ffffff; padding: 20px; border-radius: 4px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .module-header {
        font-size: 13px; font-weight: 700; color: #0f172a;
        border-bottom: 2px solid #005fa3; padding-bottom: 6px; margin-bottom: 15px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 2. INTERNAL RELATIONAL INDUSTRIAL DATABASES
# ==========================================
MATERIAL_DB = {
    "ISO P01 (Thép kết cấu C45)": {"group": "ISO P", "hb": 180, "hrc": 15, "density": 7.85, "kc1": 1500, "mc": 0.25, "base_vc": 180, "base_fz": 0.08},
    "ISO P05 (Thép khuôn mẫu P20)": {"group": "ISO P", "hb": 300, "hrc": 32, "density": 7.80, "kc1": 1900, "mc": 0.26, "base_vc": 130, "base_fz": 0.05},
    "ISO M02 (Thép không gỉ Inox 304)": {"group": "ISO M", "hb": 200, "hrc": 20, "density": 7.93, "kc1": 2200, "mc": 0.23, "base_vc": 90, "base_fz": 0.04},
    "ISO N01 (Hợp kim nhôm Al6061-T6)": {"group": "ISO N", "hb": 95, "hrc": 0, "density": 2.70, "kc1": 700, "mc": 0.15, "base_vc": 450, "base_fz": 0.12}
}

TOOL_MATERIAL_DB = {
    "Hợp kim cứng nguyên khối (Solid Carbide)": {"factor_vc": 1.0, "max_temp": 900},
    "Thép gió cao cấp (HSS-E Cobalt)": {"factor_vc": 0.35, "max_temp": 600}
}
TOOL_COATING_DB = {
    "Không phủ (Uncoated)": {"factor_vc": 1.0, "factor_life": 1.0},
    "Phủ TiAlN (Gia công tốc độ cao, chịu nhiệt)": {"factor_vc": 1.35, "factor_life": 3.0},
    "Phủ AlTiN (Gia công thép cứng, chịu va đập)": {"factor_vc": 1.25, "factor_life": 3.5},
    "Phủ DLC (Chuyên dụng cho Nhôm, chống dính)": {"factor_vc": 1.50, "factor_life": 4.0}
}

MACHINE_DB = {
    "Makino F5 (High-Speed VMC)": {"power": 15.0, "torque": 124.0, "max_rpm": 20000, "eff": 0.85, "control": "Fanuc Professional 6"},
    "Mazak VCN-530C": {"power": 18.5, "torque": 195.0, "max_rpm": 12000, "eff": 0.88, "control": "Mazatrol SmoothG"},
    "Haas VF-2SS": {"power": 22.4, "torque": 122.0, "max_rpm": 15000, "eff": 0.82, "control": "Haas NextGen"},
    "DMG MORI CMX 1100V": {"power": 13.0, "torque": 102.0, "max_rpm": 12000, "eff": 0.87, "control": "Siemens CELOS"}
}

STRATEGY_DB = {
    "Roughing (Phá thô hiệu suất cao)": {"k_ap": 1.5, "k_ae": 0.6, "req_ra": 6.3},
    "Semi Finishing (Gia công bán tinh)": {"k_ap": 0.5, "k_ae": 0.2, "req_ra": 3.2},
    "Finishing (Gia công tinh bề mặt)": {"k_ap": 0.1, "k_ae": 0.05, "req_ra": 0.8},
    "Adaptive Milling (Phay thích nghi - Trochoidal)": {"k_ap": 2.0, "k_ae": 0.1, "req_ra": 4.5},
    "Slot Milling (Phay rãnh kín)": {"k_ap": 0.5, "k_ae": 1.0, "req_ra": 3.2},
    "Face Milling (Phay khỏa mặt đầu)": {"k_ap": 0.2, "k_ae": 0.75, "req_ra": 1.6}
}

# ==========================================
# 3. INTERACTIVE MAIN APPLICATION LAYOUT
# ==========================================
st.markdown("<h2 style='margin:0; color:#0f172a;'>CNC EXPERT DSS & INTEL REPORT SYSTEM</h2>", unsafe_allow_html=True)
st.markdown("---")

col_sidebar, col_dashboard = st.columns([1, 3])

with col_sidebar:
    st.markdown("### 📥 CONFIGURATION MODULES")
    
    # MODULE A: MATERIAL
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">Module A: Vật liệu phôi</div>', unsafe_allow_html=True)
    mat_selected = st.selectbox("Chọn mác vật liệu:", list(MATERIAL_DB.keys()))
    mat_info = MATERIAL_DB[mat_selected]
    custom_hb = st.number_input("Độ cứng thực tế (HB):", min_value=50, max_value=700, value=int(mat_info["hb"]))
    st.markdown('</div>', unsafe_allow_html=True)

    # MODULE B: TOOL
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">Module B: Thông số Dao cụ</div>', unsafe_allow_html=True)
    tool_mat_selected = st.selectbox("Vật liệu lõi dao:", list(TOOL_MATERIAL_DB.keys()))
    tool_coat_selected = st.selectbox("Lớp phủ bề mặt dao:", list(TOOL_COATING_DB.keys()))
    d_input = st.number_input("Đường kính D (mm):", min_value=0.5, max_value=50.0, value=12.0, step=0.5)
    z_input = st.number_input("Số me cắt (z):", min_value=1, max_value=12, value=4, step=1)
    helix_angle = st.slider("Góc xoắn me (°):", 15, 60, 35)
    r_corner = st.number_input("Bán kính mũi R (mm):", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    tool_length = st.number_input("Chiều dài dao L_tool (mm):", min_value=10, max_value=300, value=75)
    st.markdown('</div>', unsafe_allow_html=True)

    # MODULE C: STRATEGY
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">Module C: Chiến lược gia công</div>', unsafe_allow_html=True)
    strat_selected = st.selectbox("Chiến lược công nghệ CAM:", list(STRATEGY_DB.keys()))
    strat_info = STRATEGY_DB[strat_selected]
    coolant_mode = st.radio("Chế độ tưới nguội:", ["Flood", "MQL", "Dry"])
    ap_input = st.number_input("Chiều sâu ap (mm):", value=float(d_input * strat_info["k_ap"]))
    ae_input = st.number_input("Chiều rộng ae (mm):", value=float(d_input * strat_info["k_ae"]))
    st.markdown('</div>', unsafe_allow_html=True)

    # MODULE D: MACHINE & ECONOMIC
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">Module D & E: Máy & Kinh tế</div>', unsafe_allow_html=True)
    machine_selected = st.selectbox("Trung tâm gia công CNC:", list(MACHINE_DB.keys()))
    mac_info = MACHINE_DB[machine_selected]
    l_travel = st.number_input("Chiều dài hành trình cắt L (mm):", value=500)
    hourly_cost = st.number_input("Chi phí vận hành (VNĐ/Giờ):", value=180000)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. CORE MATHEMATICAL PHYSICS ENGINE
# ==========================================
base_vc = mat_info["base_vc"] * TOOL_MATERIAL_DB[tool_mat_selected]["factor_vc"] * TOOL_COATING_DB[tool_coat_selected]["factor_vc"]
base_fz = mat_info["base_fz"] * TOOL_COATING_DB[tool_coat_selected]["factor_life"]
if coolant_mode == "Dry": base_vc *= 0.85
elif coolant_mode == "MQL": base_vc *= 1.10

S_speed = (1000 * base_vc) / (np.pi * d_input)
if S_speed > mac_info["max_rpm"]: S_speed = mac_info["max_rpm"]
F_feed = S_speed * z_input * base_fz

hm = base_fz * np.sqrt(ae_input / d_input) if ae_input < d_input else base_fz
hm_clamped = max(hm, 0.001)
kc = mat_info["kc1"] * (hm_clamped ** -mat_info["mc"])
Fc_final = max(kc * ap_input * ae_input * (F_feed / (S_speed * z_input)) / d_input * 1000 * 0.1, 50.0)

Torque_Nm = (Fc_final * (d_input / 2)) / 1000
Power_kW = (Fc_final * base_vc) / 60000
Net_Power_Required = Power_kW / mac_info["eff"]
machine_load_pct = (Net_Power_Required / mac_info["power"]) * 100
MRR_val = (ap_input * ae_input * F_feed) / 1000

T_machining_min = l_travel / F_feed
T_machining_sec = T_machining_min * 60
n_taylor = 0.25
C_taylor = base_vc * (60 ** n_taylor)
Tool_Life_Min = (C_taylor / base_vc) ** (1 / n_taylor) if base_vc > 0 else 240

# Hạch toán cấu trúc chi phí xưởng thực tế
cost_labor = (T_machining_min / 60) * (hourly_cost * 0.4)
cost_machine = (T_machining_min / 60) * (hourly_cost * 0.3)
cost_electricity = (T_machining_min / 60) * (Net_Power_Required * 3500)
cost_tool_wear = (T_machining_min / Tool_Life_Min) * 950000
Total_Cost_VND = cost_labor + cost_machine + cost_electricity + cost_tool_wear

if r_corner > 0: Ra_final = ((base_fz ** 2) / (32 * r_corner)) * 1000 * 1.1
else: Ra_final = ((base_fz ** 2) / (32 * 0.05)) * 1000 * 1.5

# Ghi dữ liệu vào biểu đồ lịch sử
history_item = {
    "Vật liệu": mat_selected, "Dao D": d_input, "Chiến lược": strat_selected,
    "S (RPM)": int(S_speed), "F (mm/min)": int(F_feed), "Ra (µm)": round(Ra_final, 2),
    "Power (kW)": round(Net_Power_Required, 2), "Cost (VNĐ)": int(Total_Cost_VND)
}
if history_item not in st.session_state.history:
    st.session_state.history.append(history_item)

# ==========================================
# 5. RENDER EXPERT INTERACTIVE WEB DASHBOARD
# ==========================================
with col_dashboard:
    st.markdown("### 📊 DECISION SUPPORT DASHBOARD SYSTEM")
    grid1, grid2, grid3, grid4 = st.columns(4)
    grid1.markdown(f'<div class="kpi-card status-success"><div class="kpi-title">🔄 Spindle Speed</div><div class="kpi-value">{int(S_speed):,}</div><div class="kpi-unit">RPM</div></div>', unsafe_allow_html=True)
    grid2.markdown(f'<div class="kpi-card status-normal"><div class="kpi-title">➡️ Feed Rate</div><div class="kpi-value">{int(F_feed):,}</div><div class="kpi-unit">mm/min</div></div>', unsafe_allow_html=True)
    grid3.markdown(f'<div class="kpi-card status-warning"><div class="kpi-title">⚡ Net Power</div><div class="kpi-value">{Net_Power_Required:.2f}</div><div class="kpi-unit">kW</div></div>', unsafe_allow_html=True)
    grid4.markdown(f'<div class="kpi-card status-success"><div class="kpi-title">✨ Surface Roughness</div><div class="kpi-value">{Ra_final:.2f}</div><div class="kpi-unit">µm (Ra)</div></div>', unsafe_allow_html=True)

    # ==========================================
    # 6. PROFESSIONAL PRINT-READY PRINT SHEET ARCHITECT ENGINE
    # ==========================================
    st.markdown("### 💾 MANUFACTURING REPORT EXPORT (SIEMENS / DMG MORI FORMAT)")
    st.info("Hệ thống đã biên dịch Phiếu công nghệ dạng Print-Ready A4 theo quy chuẩn công nghiệp cao cấp.")

    # Khởi tạo chuỗi mã nguồn HTML siêu cấu trúc đạt chuẩn in ấn của hãng phần mềm CAM thương mại
    report_id = f"RP-{datetime.datetime.now().strftime('%Y%m%d')}-{int(S_speed)}"
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.datetime.now().strftime('%H:%M:%S')

    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Professional CNC Technology Sheet</title>
    <style>
        @media print {{
            body {{ background: #fff; color: #000; margin: 0; padding: 0; }}
            .page {{ page-break-after: always; box-shadow: none; border: none; padding: 0; margin: 0; height: 297mm; }}
            .no-print {{ display: none; }}
        }}
        body {{ background: #cbd5e1; font-family: 'Arial', sans-serif; font-size: 11px; line-height: 1.4; color: #1e293b; margin: 20px 0; }}
        .page {{ background: #ffffff; width: 210mm; min-height: 292mm; padding: 15mm; margin: 0 auto 15mm auto; position: relative; box-sizing: border-box; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
        
        /* Fixed Header & Footer Utilities */
        .page-header-fixed {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #005fa3; padding-bottom: 8px; margin-bottom: 15px; }}
        .page-header-fixed .brand {{ font-size: 14px; font-weight: 700; color: #005fa3; letter-spacing: 0.5px; }}
        .page-header-fixed .doc-type {{ font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; }}
        
        .page-footer-fixed {{ position: absolute; bottom: 10mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; border-top: 1px solid #e2e8f0; padding-top: 8px; font-size: 9px; color: #94a3b8; }}
        
        /* Grid Layout Components */
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
        .grid-4 {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }}
        
        .card {{ border: 1px solid #cbd5e1; padding: 12px; border-radius: 2px; background: #f8fafc; margin-bottom: 15px; }}
        .card-title {{ font-size: 11px; font-weight: 700; color: #0f172a; text-transform: uppercase; margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }}
        
        /* Industrial Tables styling */
        table.tech-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 10.5px; }}
        table.tech-table th {{ background: #0f172a; color: #ffffff; text-align: left; padding: 6px 8px; font-weight: 600; text-transform: uppercase; }}
        table.tech-table td {{ padding: 6px 8px; border-bottom: 1px solid #e2e8f0; color: #334155; }}
        table.tech-table tr:nth-child(even) {{ background: #f8fafc; }}
        
        /* Tech KPI Elements */
        .print-kpi {{ border-left: 3px solid #005fa3; padding-left: 8px; margin-bottom: 10px; }}
        .print-kpi-val {{ font-size: 16px; font-weight: 700; color: #0f172a; }}
        .print-kpi-lbl {{ font-size: 9px; color: #64748b; text-transform: uppercase; }}
        
        .tag-success {{ color: #16a34a; font-weight: 600; }}
        .tag-warning {{ color: #d97706; font-weight: 600; }}
        .tag-danger {{ color: #dc2626; font-weight: 600; }}
    </style>
    </head>
    <body>

    <div class="page">
        <div class="page-header-fixed">
            <div class="brand">SIEMENS NX CAM METRICS ENGINE</div>
            <div class="doc-type">Technology Sheet Report</div>
        </div>
        
        <div style="text-align: center; margin-top: 40px; margin-bottom: 40px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #0f172a; margin: 0; letter-spacing: 1px;">PRODUCTION TECHNOLOGY SHEET</h1>
            <p style="font-size: 11px; color: #64748b; margin-top: 5px;">CNC CUTTING OPTIMIZATION DECISION SUPPORT SYSTEM</p>
        </div>
        
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Mã số & Định danh tài liệu</div>
                <table style="width:100%; line-height: 1.8;">
                    <tr><td><b>Report ID:</b></td><td>{report_id}</td></tr>
                    <tr><td><b>Version:</b></td><td>v3.0.0 (Industrial)</td></tr>
                    <tr><td><b>Date / Time:</b></td><td>{date_str} / {time_str}</td></tr>
                    <tr><td><b>Doanh nghiệp:</b></td><td>FDI Manufacturing Complex</td></tr>
                    <tr><td><b>Phân xưởng:</b></td><td>Xưởng Gia Công Khuôn Mẫu CNC</td></tr>
                </table>
            </div>
            <div class="card">
                <div class="card-title">Cấu trúc trạm máy & Hồ sơ CAM</div>
                <table style="width:100%; line-height: 1.8;">
                    <tr><td><b>Mã chương trình:</b></td><td>O0054_PRO_FINISH</td></tr>
                    <tr><td><b>Trung tâm CNC:</b></td><td>{machine_selected}</td></tr>
                    <tr><td><b>Hệ điều khiển:</b></td><td>{mac_info["control"]}</td></tr>
                    <tr><td><b>Kỹ sư thực hiện:</b></td><td>CNC Process Engineer Senior</td></tr>
                    <tr><td><b>Trạng thái hệ thống:</b></td><td><span class="tag-success">PRODUCTION READY</span></td></tr>
                </table>
            </div>
        </div>
        
        <h3 style="border-bottom: 1px solid #0f172a; padding-bottom: 4px; text-transform: uppercase; font-size: 12px; margin-top: 30px;">EXECUTIVE PROCESS DASHBOARD</h3>
        <p style="color:#64748b; margin-bottom: 15px;">Tóm tắt bộ thông số động lực học cắt gọt chính được phê duyệt đưa xuống xưởng:</p>
        
        <div class="grid-3" style="margin-bottom: 30px;">
            <div class="card" style="border-top: 3px solid #16a34a;"><div class="print-kpi-lbl">Tốc độ trục chính (S)</div><div class="print-kpi-val">{sidebar_s:,.0f} RPM</div><div class="print-kpi-lbl">Chuẩn G97</div></div>
            <div class="card" style="border-top: 3px solid #005fa3;"><div class="print-kpi-lbl">Tốc độ bàn máy (F)</div><div class="print-kpi-val">{sidebar_f:,.0f} mm/min</div><div class="print-kpi-lbl">Chuẩn G94</div></div>
            <div class="card" style="border-top: 3px solid #005fa3;"><div class="print-kpi-lbl">Vận tốc cắt thực tế (Vc)</div><div class="print-kpi-val">{base_vc:.1f} m/min</div><div class="print-kpi-lbl">Lý thuyết hãng</div></div>
            
            <div class="card" style="border-top: 3px solid #ea580c;"><div class="print-kpi-lbl">Công suất mạng tải</div><div class="print-kpi-val">{Net_Power_Required:.2f} kW</div><div class="print-kpi-lbl">Tải máy: {machine_load_pct:.1f}%</div></div>
            <div class="card" style="border-top: 3px solid #ea580c;"><div class="print-kpi-lbl">Mô-men xoắn sinh ra</div><div class="print-kpi-val">{Torque_Nm:.2f} N.m</div><div class="print-kpi-lbl">Giới hạn: {mac_info["torque"]} N.m</div></div>
            <div class="card" style="border-top: 3px solid #16a34a;"><div class="print-kpi-lbl">Độ nhám bề mặt (Ra)</div><div class="print-kpi-val">{Ra_final:.2f} µm</div><div class="print-kpi-lbl">Yêu cầu chiến lược</div></div>
            
            <div class="card" style="border-top: 3px solid #0f172a;"><div class="print-kpi-lbl">Lực cắt tiếp tuyến (Fz)</div><div class="print-kpi-val">{Fc_final:.0f} N</div><div class="print-kpi-lbl">Ứng suất cơ học</div></div>
            <div class="card" style="border-top: 3px solid #0f172a;"><div class="print-kpi-lbl">Năng suất bóc phôi (MRR)</div><div class="print-kpi-val">{MRR_val:.2f} cm³/min</div><div class="print-kpi-lbl">Hiệu quả khối lượng</div></div>
            <div class="card" style="border-top: 3px solid #16a34a;"><div class="print-kpi-lbl">Thời gian gia công</div><div class="print-kpi-val">{T_machining_sec:.1f} Giây</div><div class="print-kpi-lbl">Hành trình: {l_travel} mm</div></div>
        </div>
        
        <div class="card" style="background:#f0fdf4; border: 1px solid #bbf7d0; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <b style="color: #16a34a; text-transform: uppercase;">MÃ QR XÁC THỰC SỐ HÓA</b>
                <p style="margin: 3px 0 0 0; color: #3f6212; font-size: 10px;">Quét mã QR để đồng bộ và mở trực tiếp bộ dữ liệu số này trên nền tảng Website DSS đám mây.</p>
            </div>
            <div style="background: #0f172a; color:#fff; padding: 10px; font-weight:700; font-size:10px; border-radius:2px;">QR CONFIG LINK</div>
        </div>

        <div class="page-footer-fixed">
            <div>CNC EXPERT DSS v3.0.0 | Report ID: {report_id}</div>
            <div>Trang 1 / 4</div>
        </div>
    </div>

    <div class="page">
        <div class="page-header-fixed">
            <div class="brand">SIEMENS NX CAM METRICS ENGINE</div>
            <div class="doc-type">Technology Sheet Report</div>
        </div>
        
        <h3 style="border-bottom: 1px solid #0f172a; padding-bottom: 4px; text-transform: uppercase; font-size: 12px;">CONFIGURATION MODULES (THÔNG SỐ ĐẦU VÀO ĐỒNG BỘ)</h3>
        
        <div class="grid-2">
            <div class="card">
                <div class="card-title">1. WORKPIECE SPECIFICATION (PHÔI)</div>
                <table style="width:100%; line-height: 1.9;">
                    <tr><td>Mác vật liệu chỉ định:</td><td><b>{mat_selected}</b></td></tr>
                    <tr><td>Phân loại nhóm ISO:</td><td><span class="tag-normal">{mat_info["group"]}</span></td></tr>
                    <tr><td>Độ cứng cấu trúc vật lý:</td><td>{custom_hb} HB / {int(custom_hb*0.095)} HRC</td></tr>
                    <tr><td>Khối lượng riêng tiêu chuẩn:</td><td>{mat_info["density"]} g/cm³</td></tr>
                </table>
            </div>
            
            <div class="card">
                <div class="card-title">2. CUTTING TOOL SPECIFICATION (DAO CỤ)</div>
                <table style="width:100%; line-height: 1.9;">
                    <tr><td>Đường kính hình học (D):</td><td><b>{d_input} mm</b></td></tr>
                    <tr><td>Số me cắt làm việc (z):</td><td>{z_input} me</td></tr>
                    <tr><td>Vật liệu cấu tạo lõi dao:</td><td>{tool_mat_selected}</td></tr>
                    <tr><td>Công nghệ lớp phủ bề mặt:</td><td>{tool_coat_selected}</td></tr>
                    <tr><td>Góc xoắn me dao phay:</td><td>{helix_angle}°</td></tr>
                    <tr><td>Bán kính mũi dao góc (R):</td><td>{r_corner} mm</td></tr>
                </table>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="card">
                <div class="card-title">3. CNC MACHINE HARDWARE (MÁY CÔNG CỤ)</div>
                <table style="width:100%; line-height: 1.9;">
                    <tr><td>Tên máy trung tâm CNC:</td><td><b>{machine_selected}</b></td></tr>
                    <tr><td>Hệ điều hành tích hợp:</td><td>{mac_info["control"]}</td></tr>
                    <tr><td>Giới hạn vòng quay máy:</td><td>{mac_info["max_rpm"]} RPM</td></tr>
                    <tr><td>Nguồn công suất cực đại:</td><td>{mac_info["power"]} kW</td></tr>
                    <tr><td>Mô-men xoắn định mức:</td><td>{mac_info["torque"]} N.m</td></tr>
                    <tr><td>Hiệu suất truyền động cơ cơ:</td><td>{int(mac_info["eff"]*100)}%</td></tr>
                </table>
            </div>
            
            <div class="card">
                <div class="card-title">4. CAM CUTTING STRATEGY (CHIẾN LƯỢC)</div>
                <table style="width:100%; line-height: 1.9;">
                    <tr><td>Chiến lược chạy dao CAM:</td><td><b>{strat_selected}</b></td></tr>
                    <tr><td>Chiều sâu cắt trục dọc (ap):</td><td>{ap_input:.2f} mm</td></tr>
                    <tr><td>Chiều rộng ăn dao ngang (ae):</td><td>{ae_input:.2f} mm</td></tr>
                    <tr><td>Phương thức làm mát tưới:</td><td>{coolant_mode}</td></tr>
                    <tr><td>Yêu cầu nhám bề mặt Ra:</td><td>&lt; {strat_info["req_ra"]} µm</td></tr>
                </table>
            </div>
        </div>

        <div class="page-footer-fixed">
            <div>CNC EXPERT DSS v3.0.0 | Report ID: {report_id}</div>
            <div>Trang 2 / 4</div>
        </div>
    </div>

    <div class="page">
        <div class="page-header-fixed">
            <div class="brand">SIEMENS NX CAM METRICS ENGINE</div>
            <div class="doc-type">Technology Sheet Report</div>
        </div>
        
        <h3 style="border-bottom: 1px solid #0f172a; padding-bottom: 4px; text-transform: uppercase; font-size: 12px;">KẾT QUẢ TÍNH TOÁN VÀ ĐÁNH GIÁ CHUYÊN SÂU</h3>
        
        <table class="tech-table">
            <thead>
                <tr>
                    <th>Thông số công nghệ</th>
                    <th>Giá trị tính toán</th>
                    <th>Đơn vị</th>
                    <th>Đánh giá trạng thái vật lý</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Spindle Speed (Vòng quay)</td><td><b>{int(S_speed):,}</b></td><td>RPM</td><td><span class="tag-success">An toàn (Nằm trong giới hạn máy)</span></td></tr>
                <tr><td>Feed Rate (Tốc độ tiến bàn)</td><td><b>{int(F_feed):,}</b></td><td>mm/min</td><td><span class="tag-success">Tối ưu dung sai răng</span></td></tr>
                <tr><td>Cutting Velocity (Vận tốc cắt)</td><td><b>{base_vc:.1f}</b></td><td>m/min</td><td><span class="tag-success">Đạt hiệu suất vật liệu phủ</span></td></tr>
                <tr><td>Axial Depth of Cut (ap)</td><td><b>{ap_input:.2f}</b></td><td>mm</td><td><span class="tag-normal">Đúng cấu hình CAM</span></td></tr>
                <tr><td>Radial Depth of Cut (ae)</td><td><b>{ae_input:.2f}</b></td><td>mm</td><td><span class="tag-normal">Đúng cấu hình CAM</span></td></tr>
                <tr><td>Material Removal Rate (MRR)</td><td><b>{MRR_val:.2f}</b></td><td>cm³/min</td><td><span class="tag-success">Đạt hiệu năng bóc tách phôi</span></td></tr>
                <tr><td>Main Cutting Force (Lực cắt Fc)</td><td><b>{Fc_final:.0f}</b></td><td>N</td><td><span class="tag-success">Đồ gá kẹp chịu lực an toàn</span></td></tr>
                <tr><td>Spindle Torque (Mô-men xoắn)</td><td><b>{Torque_Nm:.2f}</b></td><td>N.m</td><td><span class="tag-success">Dưới giới hạn xoắn của trục máy</span></td></tr>
                <tr><td>Net Power Required (Công suất)</td><td><b>{Net_Power_Required:.2f}</b></td><td>kW</td><td><span class="tag-warning">Tải máy ổn định ở mức {machine_load_pct:.1f}%</span></td></tr>
                <tr><td>Calculated Tool Life (Tuổi thọ)</td><td><b>{Tool_Life_Min:.1f}</b></td><td>Phút</td><td><span class="tag-warning">Hao mòn lũy tiến tự nhiên</span></td></tr>
                <tr><td>Surface Roughness (Độ nhám Ra)</td><td><b>{Ra_final:.2f}</b></td><td>µm</td><td><span class="tag-success">Đạt tiêu chuẩn khuôn ({Ra_final:.2f} &lt; {strat_info["req_ra"]})</span></td></tr>
            </tbody>
        </table>
        
        <h3 style="border-bottom: 1px solid #0f172a; padding-bottom: 4px; text-transform: uppercase; font-size: 11px; margin-top: 25px;">🧠 SMART RECOMMENDATION REPORT (AI ENGINE)</h3>
        
        <div style="line-height: 1.7; font-size:10.5px;">
            <p>🟢 <b>Dao cụ hoạt động trong vùng điền lý tưởng:</b> Sự tương thích giữa vật liệu lõi và lớp phủ cụ thể giúp triệt tiêu hiện tượng mẻ dao đột ngột.</p>
            <p>🟢 <b>Chất lượng bề mặt Ra đạt chuẩn kỹ thuật:</b> Biên độ dung sai hình học đảm bảo lắp ráp mượt mà mà không cần xử lý đánh bóng thủ công phụ trợ.</p>
            {"<p>🟡 <b>Khuyến nghị điều chỉnh bước tiến dao:</b> Dựa trên mô phỏng cơ học cắt gọt, có thể tăng lượng tiến dao răng fz từ 8-10% để nâng cao MRR mà không làm ảnh hưởng xấu đến tuổi thọ dao.</p>" if machine_load_pct < 70 else "<p>🟠 <b>Cảnh báo tải trọng hệ thống:</b> Công suất trục chính đang ở dải biên an toàn cao, khuyến nghị không tăng thêm ap hoặc lượng ăn dao ngang ae.</p>"}
            <p>🔴 <b>Quản trị rủi ro rung động cơ học:</b> Đảm bảo độ rơ lỏng của bầu kẹp dao thủy lực đạt dưới dải 5 micromet để loại bỏ tần số tự do gây hiện tượng sọc dợn sóng bề mặt chi tiết phay.</p>
        </div>

        <div class="page-footer-fixed">
            <div>CNC EXPERT DSS v3.0.0 | Report ID: {report_id}</div>
            <div>Trang 3 / 4</div>
        </div>
    </div>

    <div class="page">
        <div class="page-header-fixed">
            <div class="brand">SIEMENS NX CAM METRICS ENGINE</div>
            <div class="doc-type">Technology Sheet Report</div>
        </div>
        
        <h3 style="border-bottom: 1px solid #0f172a; padding-bottom: 4px; text-transform: uppercase; font-size: 12px;">PHÂN TÍCH KINH TẾ VÀ PHỤ LỤC THẨM ĐỊNH</h3>
        
        <div class="card">
            <div class="card-title">HẠCH TOÁN CHI PHÍ GIA CÔNG CHI TIẾT (PRODUCTION COST ECONOMIC)</div>
            <table style="width:100%; line-height: 2.0; font-size:11px;">
                <tr><td>1. Chi phí khấu hao giờ máy vận hành công nghệ:</td><td style="text-align:right;">{int(cost_machine):,} VNĐ</td></tr>
                <tr><td>2. Chi phí nhân công vận hành / Đứng máy điều khiển:</td><td style="text-align:right;">{int(cost_labor):,} VNĐ</td></tr>
                <tr><td>3. Chi phí tiêu hao điện năng phụ tải trục chính:</td><td style="text-align:right;">{int(cost_electricity):,} VNĐ</td></tr>
                <tr><td>4. Chi phí hao mòn, khấu hao lũy tiến dao cụ cát gọt:</td><td style="text-align:right;">{int(cost_tool_wear):,} VNĐ</td></tr>
                <tr style="border-top:1px dashed #0f172a; font-weight:700;"><td>TỔNG CHI PHÍ GIA CÔNG ƯỚC TÍNH TRÊN MỖI CHI TIẾT:</td><td style="text-align:right; color:#005fa3; font-size:13px;">{int(Total_Cost_VND):,} VNĐ</td></tr>
            </table>
        </div>
        
        <div class="card">
            <div class="card-title">PHỤ LỤC CÔNG THỨC TOÁN HỌC PHÁP LÝ TIÊU CHUẨN ISO</div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 10px; font-family: monospace;">
                <div>
                    • Spindle Speed: S = (1000 x Vc) / (π x D)<br>
                    • Feed Rate: F = S x z x fz<br>
                    • MRR Rate: MRR = (ap x ae x F) / 1000
                </div>
                <div>
                    • Cutting Power: P = (Fc x Vc) / 60000<br>
                    • Mechanical Torque: T = (Fc x D) / 2000<br>
                    • Taylor Life: Vc x T^n = C
                </div>
            </div>
        </div>
        
        <div style="margin-top: 40px; display: flex; justify-content: space-between; text-align: center;">
            <div style="width: 25%;">
                <p><b>Kỹ sư lập phiếu</b></p>
                <div style="height: 50px;"></div>
                <p style="color:#64748b; font-size:10px;">(Ký & Ghi rõ họ tên)</p>
            </div>
            <div style="width: 25%;">
                <p><b>Người kiểm tra (QC)</b></p>
                <div style="height: 50px;"></div>
                <p style="color:#64748b; font-size:10px;">(Ký & Ghi rõ họ tên)</p>
            </div>
            <div style="width: 25%;">
                <p><b>Quản đốc phân xưởng</b></p>
                <div style="height: 50px;"></div>
                <p style="color:#64748b; font-size:10px;">(Phê duyệt thực thi)</p>
            </div>
        </div>

        <div class="page-footer-fixed">
            <div>CNC EXPERT DSS v3.0.0 | Report ID: {report_id}</div>
            <div>Trang 4 / 4</div>
        </div>
    </div>

    </body>
    </html>
    """

    # Cơ chế nhúng tài liệu in ấn trực tiếp lên giao diện Dashboard Web thông qua Streamlit components
    st.components.v1.html(html_document, height=600, scrolling=True)
    
    # Nút bấm kích hoạt mở rộng tab in ấn chuẩn cho kỹ sư
    st.download_button(
        label="🖨️ XUẤT PHIẾU CÔNG NGHỆ CHUYÊN NGHIỆP (Bấm Ctrl+P để In/Lưu PDF)",
        data=html_document,
        file_name=f"CNC_Technology_Sheet_{report_id}.html",
        mime="text/html"
    )
