import streamlit as st
import numpy as np
import pandas as pd
import json

# ==========================================
# 1. INITIAL SYSTEM CONFIGURATION & UI THEME
# ==========================================
st.set_page_config(
    page_title="Industrial CNC Cutting Parameter Decision Support System (DSS)",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nhúng phông chữ Inter/Roboto và định dạng CSS Công nghiệp (Màu sắc Siemens/Fusion 360)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    
    * { font-family: 'IBM Plex Sans', sans-serif; }
    
    /* Cấu trúc Theme màu Công nghiệp */
    .stApp { background-color: #f1f5f9; }
    
    /* Thiết kế Thẻ KPI chuyên nghiệp */
    .kpi-card {
        background: #ffffff;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .kpi-title { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #0f172a; margin: 4px 0; }
    .kpi-unit { font-size: 12px; color: #94a3b8; font-weight: 500; }
    
    /* Trạng thái màu sắc KPI */
    .status-normal { border-left: 4px solid #2563eb; }
    .status-success { border-left: 4px solid #16a34a; }
    .status-warning { border-left: 4px solid #ea580c; }
    .status-danger { border-left: 4px solid #dc2626; }
    
    /* Khung Module thiết kế CAM */
    .module-box {
        background: #ffffff;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .module-header {
        font-size: 14px; font-weight: 700; color: #1e293b;
        border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; margin-bottom: 15px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* Khung khuyến nghị AI */
    .ai-box {
        background: #fafafa;
        border-radius: 6px;
        padding: 15px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State để lưu trữ lịch sử tính toán (10 lần gần nhất)
if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 2. INTERNAL RELATIONAL INDUSTRIAL DATABASES
# ==========================================

# A. Workpiece Material Database (Theo chuẩn ISO / ASM Handbook)
MATERIAL_DB = {
    "ISO P01 (Thép kết cấu C45)": {"group": "ISO P", "hb": 180, "hrc": 15, "kc1": 1500, "mc": 0.25, "base_vc": 180, "base_fz": 0.08},
    "ISO P05 (Thép khuôn mẫu P20)": {"group": "ISO P", "hb": 300, "hrc": 32, "kc1": 1900, "mc": 0.26, "base_vc": 130, "base_fz": 0.05},
    "ISO M02 (Thép không gỉ Inox 304)": {"group": "ISO M", "hb": 200, "hrc": 20, "kc1": 2200, "mc": 0.23, "base_vc": 90, "base_fz": 0.04},
    "ISO N01 (Hợp kim nhôm Al6061-T6)": {"group": "ISO N", "hb": 95, "hrc": 0, "kc1": 700, "mc": 0.15, "base_vc": 450, "base_fz": 0.12}
}

# B. Cutting Tool Coating & Material Database (Theo chuẩn Sandvik Coromant)
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

# C. Machine Tool Configuration Database (Tiêu chuẩn trung tâm gia công)
MACHINE_DB = {
    "Makino F5 (High-Speed VMC)": {"power": 15.0, "torque": 124.0, "max_rpm": 20000, "eff": 0.85, "control": "Fanuc Professional 6"},
    "Mazak VCN-530C": {"power": 18.5, "torque": 195.0, "max_rpm": 12000, "eff": 0.88, "control": "Mazatrol SmoothG"},
    "Haas VF-2SS": {"power": 22.4, "torque": 122.0, "max_rpm": 15000, "eff": 0.82, "control": "Haas NextGen"},
    "DMG MORI CMX 1100V": {"power": 13.0, "torque": 102.0, "max_rpm": 12000, "eff": 0.87, "control": "Siemens CELOS"}
}

# D. Chiến lược chạy dao CAM nâng cao (Advanced Milling Strategies)
STRATEGY_DB = {
    "Roughing (Phá thô hiệu suất cao)": {"k_ap": 1.5, "k_ae": 0.6, "req_ra": 6.3},
    "Semi Finishing (Gia công bán tinh)": {"k_ap": 0.5, "k_ae": 0.2, "req_ra": 3.2},
    "Finishing (Gia công tinh bề mặt)": {"k_ap": 0.1, "k_ae": 0.05, "req_ra": 0.8},
    "Adaptive Milling (Phay thích nghi - Trochoidal)": {"k_ap": 2.0, "k_ae": 0.1, "req_ra": 4.5},
    "Slot Milling (Phay rãnh kín)": {"k_ap": 0.5, "k_ae": 1.0, "req_ra": 3.2},
    "Face Milling (Phay khỏa mặt đầu)": {"k_ap": 0.2, "k_ae": 0.75, "req_ra": 1.6}
}

# ==========================================
# 3. HEADER SECTION
# ==========================================
st.markdown("<h2 style='margin:0; color:#0f172a;'>CNC EXPERT CAM PRO: DECISION SUPPORT SYSTEM</h2>", unsafe_allow_html=True)
st.caption("Hệ thống Hỗ trợ Quyết định Thiết lập & Tối ưu hóa Chế độ cắt Phay CNC đa mục tiêu tiêu chuẩn Công nghiệp v3.0")
st.markdown("---")

# ==========================================
# 4. APPLICATION LAYOUT & INPUT MODULES
# ==========================================
col_sidebar, col_dashboard = st.columns([1, 3])

with col_sidebar:
    st.markdown("### 📥 CONFIGURATION MODULES")
    
    # MODULE A: WORKPIECE MATERIAL
    with st.container():
        st.markdown('<div class="module-box">', unsafe_allow_html=True)
        st.markdown('<div class="module-header">Module A: Đối tượng Vật liệu phôi</div>', unsafe_allow_html=True)
        mat_selected = st.selectbox("Chọn mác vật liệu:", list(MATERIAL_DB.keys()))
        mat_info = MATERIAL_DB[mat_selected]
        
        # Cho phép người dùng tùy chỉnh độ cứng phôi thực tế
        custom_hb = st.number_input("Độ cứng thực tế (HB):", min_value=50, max_value=700, value=int(mat_info["hb"]))
        st.markdown(f"**Nhóm ISO:** `{mat_info['group']}` | **Độ cứng tương đương:** `{int(custom_hb*0.095)} HRC`")
        st.markdown('</div>', unsafe_allow_html=True)

    # MODULE B: CUTTING TOOL CONFIGURATION
    with st.container():
        st.markdown('<div class="module-box">', unsafe_allow_html=True)
        st.markdown('<div class="module-header">Module B: Hình học & Vật liệu dao</div>', unsafe_allow_html=True)
        tool_mat_selected = st.selectbox("Vật liệu lõi dao:", list(TOOL_MATERIAL_DB.keys()))
        tool_coat_selected = st.selectbox("Lớp phủ bề mặt dao:", list(TOOL_COATING_DB.keys()))
        
        c_t1, c_t2 = st.columns(2)
        d_input = c_t1.number_input("Đường kính D (mm):", min_value=0.5, max_value=50.0, value=12.0, step=0.5)
        z_input = c_t2.number_input("Số me cắt (z):", min_value=1, max_value=12, value=4, step=1)
        
        c_t3, c_t4 = st.columns(2)
        helix_angle = c_t3.slider("Góc xoắn me (°):", 15, 60, 35)
        r_corner = c_t4.number_input("Bán kính mũi R (mm):", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
        st.markdown('</div>', unsafe_allow_html=True)

    # MODULE C: MILLING STRATEGY & TECHNOLOGY
    with st.container():
        st.markdown('<div class="module-box">', unsafe_allow_html=True)
        st.markdown('<div class="module-header">Module C: Chiến lược gia công</div>', unsafe_allow_html=True)
        strat_selected = st.selectbox("Chiến lược công nghệ CAM:", list(STRATEGY_DB.keys()))
        strat_info = STRATEGY_DB[strat_selected]
        
        coolant_mode = st.radio("Chế độ tưới nguội dung dịch:", ["Flood (Tưới dung dịch tràn)", "MQL (Phun sương tối thiểu)", "Dry (Cắt nguội khô)"])
        
        st.markdown("**Thông số lớp cắt cơ sở:**")
        c_s1, c_s2 = st.columns(2)
        ap_calculated = d_input * strat_info["k_ap"]
        ae_calculated = d_input * strat_info["k_ae"]
        ap_input = c_s1.number_input("Chiều sâu trục đứng ap (mm):", min_value=0.05, max_value=100.0, value=float(ap_calculated), step=0.1)
        ae_input = c_s2.number_input("Chiều rộng ăn dao ngang ae (mm):", min_value=0.05, max_value=100.0, value=float(ae_calculated), step=0.1)
        st.markdown('</div>', unsafe_allow_html=True)

    # MODULE D: CNC MACHINE TOOL SPECIFICATION
    with st.container():
        st.markdown('<div class="module-box">', unsafe_allow_html=True)
        st.markdown('<div class="module-header">Module D: Cấu hình trạm máy CNC</div>', unsafe_allow_html=True)
        machine_selected = st.selectbox("Trung tâm gia công CNC:", list(MACHINE_DB.keys()))
        mac_info = MACHINE_DB[machine_selected]
        st.markdown(f"**Hệ điều khiển:** `{mac_info['control']}` | **Vòng quay tối đa:** `{mac_info['max_rpm']} RPM`")
        st.markdown('</div>', unsafe_allow_html=True)

    # MODULE E: OPERATION PROCESS COST & OPERATION LENGTH
    with st.container():
        st.markdown('<div class="module-box">', unsafe_allow_html=True)
        st.markdown('<div class="module-header">Module E: Hành trình & Kinh tế xưởng</div>', unsafe_allow_html=True)
        l_travel = st.number_input("Chiều dài hành trình cắt L (mm):", min_value=1, max_value=10000, value=500)
        hourly_cost = st.number_input("Chi phí vận hành (VNĐ/Giờ):", min_value=1000, max_value=5000000, value=150000, step=10000)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. CORE COMPUTATION ENGINE (PROCESS PHYSICS)
# ==========================================

# Áp dụng các hệ số điều chỉnh phi tuyến tính để lấy thông số Vc và fz mục tiêu
base_vc = mat_info["base_vc"] * TOOL_MATERIAL_DB[tool_mat_selected]["factor_vc"] * TOOL_COATING_DB[tool_coat_selected]["factor_vc"]
base_fz = mat_info["base_fz"] * TOOL_COATING_DB[tool_coat_selected]["factor_life"]

# Hiệu chỉnh theo chế độ tưới nguội thực tế
if coolant_mode == "Dry (Cắt nguội khô)":
    base_vc *= 0.85
elif coolant_mode == "MQL (Phun sương tối thiểu)":
    base_vc *= 1.10

# Cho phép người dùng tinh chỉnh trực tiếp Vc và fz (Advanced input)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ ĐIỀU CHỈNH TRỰC TIẾP CHẾ ĐỘ CẮT BASE")
vc_final = st.sidebar.number_input("Tốc độ cắt Vc (m/min):", min_value=5.0, max_value=2000.0, value=float(base_vc))
fz_final = st.sidebar.number_input("Lượng chạy dao răng fz (mm/z):", min_value=0.001, max_value=2.000, value=float(base_fz), format="%.3f")

# Động học cắt gọt (Kinematics Calculation)
S_speed = (1000 * vc_final) / (np.pi * d_input)
F_feed = S_speed * z_input * fz_final

# Tính toán chiều dày phôi cắt trung bình hm (Cơ học cắt gọt nâng cao)
hm = fz_final * np.sqrt(ae_input / d_input) if ae_input < d_input else fz_final

# Tính toán lực cắt cơ học dựa trên áp lực cắt riêng đặc trưng của vật liệu kc (Specific Cutting Force)
# Công thức Kienzle: kc = kc1 * (hm ** -mc)
hm_clamped = max(hm, 0.001)
kc = mat_info["kc1"] * (hm_clamped ** -mat_info["mc"])
Fc = kc * ap_input * ae_input * (F_feed / (S_speed * z_input)) / d_input * 1000 # Lực tiếp tuyến xấp xỉ cơ sở
Fc_final = max(Fc * 0.1, 50.0) # Đảm bảo biên độ vật lý thực tế không bị triệt tiêu

# Tính toán Mô-men xoắn (Torque) và Công suất cắt gọt thực tế (Cutting Power)
Torque_Nm = (Fc_final * (d_input / 2)) / 1000
Power_kW = (Fc_final * vc_final) / 60000
Net_Power_Required = Power_kW / mac_info["eff"]

# Đánh giá tải máy CNC (Machine Load %)
machine_load_pct = (Net_Power_Required / mac_info["power"]) * 100

# Năng suất bóc tách kim loại (Material Removal Rate)
MRR_val = (ap_input * ae_input * F_feed) / 1000 # cm³/min

# Tính toán thời gian cắt gọt công nghệ (Machining Time)
T_machining_min = l_travel / F_feed
T_machining_sec = T_machining_min * 60

# Tính toán tuổi thọ dao gọt (Tool Life) dựa trên phương trình mở rộng Taylor
# V * T^n = C -> Giả định n=0.25 cho carbide, C tính theo dữ liệu thiết kế hãng
n_taylor = 0.25
C_taylor = base_vc * (60 ** n_taylor)
Tool_Life_Min = (C_taylor / vc_final) ** (1 / n_taylor) if vc_final > 0 else 240

# Bài toán chi phí sản xuất xưởng (Production Cost Economics)
Cost_part_VND = (T_machining_min / 60) * hourly_cost
Tool_wear_cost = (T_machining_min / Tool_Life_Min) * 850000 # Giả định giá trị dao trung bình 850,000đ
Total_Cost_VND = Cost_part_VND + Tool_wear_cost

# Dự báo chất lượng độ nhám bề mặt lý thuyết Ra (Theoretical Surface Roughness)
# Công thức hình học lý thuyết: Ra = (fz^2) / (32 * R_corner)
if r_corner > 0:
    Ra_theoretical = (fz_final ** 2) / (32 * r_corner) * 1000 # Đổi sang micromet
else:
    Ra_theoretical = (fz_final ** 2) / (32 * 0.05) * 1000 # Giả định bán kính lưỡi cắt siêu nhỏ

# Đồng bộ hệ số ảnh hưởng độ rung động và biến dạng vật liệu thực tế lên Ra
Ra_final = Ra_theoretical * (1.5 if strat_selected == "Roughing (Phá thô hiệu suất cao)" else 1.1)

# Lưu thông số vào Session State History để theo dõi biểu đồ so sánh lịch sử
history_item = {
    "Vật liệu": mat_selected, "Dao D": d_input, "Chiến lược": strat_selected,
    "S (RPM)": int(S_speed), "F (mm/min)": int(F_feed), "Ra (µm)": round(Ra_final, 2),
    "Power (kW)": round(Net_Power_Required, 2), "Cost (VNĐ)": int(Total_Cost_VND)
}
if history_item not in st.session_state.history:
    st.session_state.history.append(history_item)
    if len(st.session_state.history) > 10:
        st.session_state.history.pop(0)

# ==========================================
# 6. DASHBOARD OUTPUT - INDUSTRIAL KPI CARDS
# ==========================================
with col_dashboard:
    st.markdown("### 📊 DECISION SUPPORT DASHBOARD SYSTEM")
    
    # HÀNG KPI 1: ĐỘNG HỌC VÀ CƠ HỌC CẮT CHÍNH
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        status_s = "status-danger" if S_speed > mac_info["max_rpm"] else "status-success"
        st.markdown(f"""
        <div class="kpi-card {status_s}">
            <div class="kpi-title">🔄 Tốc độ trục chính (S)</div>
            <div class="kpi-value">{int(S_speed):,}</div>
            <div class="kpi-unit">Vòng/Phút (RPM)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("S = (1000 × Vc) / (π × D)")
            st.caption("Trong đó: Vc là tốc độ cắt (m/min), D là đường kính dao phay (mm).")

    with r1_c2:
        st.markdown(f"""
        <div class="kpi-card status-normal">
            <div class="kpi-title">➡️ Tốc độ bàn máy (Feed)</div>
            <div class="kpi-value">{int(F_feed):,}</div>
            <div class="kpi-unit">mm/Phút (min)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("F = S × z × fz")
            st.caption("Trong đó: S là vòng quay (RPM), z là số răng cắt, fz là lượng chạy dao răng (mm/z).")

    with r1_c3:
        status_l = "status-danger" if machine_load_pct > 100 else ("status-warning" if machine_load_pct > 80 else "status-success")
        st.markdown(f"""
        <div class="kpi-card {status_l}">
            <div class="kpi-title">⚡ Công suất mạng tải (P)</div>
            <div class="kpi-value">{Net_Power_Required:.2f}</div>
            <div class="kpi-unit">KiloWatt (kW)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("P_net = (Fc × Vc) / (60000 × η)")
            st.caption("Trong đó: Fc là lực cắt cơ học (N), Vc là tốc độ cắt, η là hiệu suất truyền động động cơ máy máy.")

    with r1_c4:
        st.markdown(f"""
        <div class="kpi-card status-normal">
            <div class="kpi-title">🌀 Mô-men xoắn trục chính</div>
            <div class="kpi-value">{Torque_Nm:.2f}</div>
            <div class="kpi-unit">Newton-Meter (N.m)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("T = (Fc × D) / 2000")
            st.caption("Mô-men ứng suất cơ học sinh ra tại tâm trục chính trong quá trình bóc tách lớp phôi.")

    # HÀNG KPI 2: CHẤT LƯỢNG, NĂNG SUẤT VÀ KINH TẾ XƯỞNG
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    
    with r2_c1:
        status_ra = "status-success" if Ra_final <= strat_info["req_ra"] else "status-danger"
        st.markdown(f"""
        <div class="kpi-card {status_ra}">
            <div class="kpi-title">✨ Độ nhám bề mặt (Ra)</div>
            <div class="kpi-value">{Ra_final:.2f}</div>
            <div class="kpi-unit">Micromet (µm)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("Ra ≈ (fz²) / (32 × R_corner) × 1000")
            st.caption("Độ nhám hình học lý thuyết bề mặt sau phay phụ thuộc chặt chẽ vào lượng tiến dao răng và bán kính góc mũi dao.")

    with r2_c2:
        st.markdown(f"""
        <div class="kpi-card status-normal">
            <div class="kpi-title">📦 Năng suất bóc phôi (MRR)</div>
            <div class="kpi-value">{MRR_val:.2f}</div>
            <div class="kpi-unit">cm³/Phút (min)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("MRR = (ap × ae × F) / 1000")
            st.caption("Thể tích kim loại được bóc tách và chuyển đổi thành phôi thoát ra ngoài trong một đơn vị thời gian.")

    with r2_c3:
        st.markdown(f"""
        <div class="kpi-card status-normal">
            <div class="kpi-title">⏱️ Thời gian gia công</div>
            <div class="kpi-value">{T_machining_sec:.1f}</div>
            <div class="kpi-unit">Giây (s)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("Tm = L / F")
            st.caption("Thời gian chạy dao công nghệ để đi hết quãng đường hành trình cơ học chỉ định.")

    with r2_c4:
        st.markdown(f"""
        <div class="kpi-card economic-box">
            <div class="kpi-title">💸 Tổng chi phí / Chi tiết</div>
            <div class="kpi-value">{int(Total_Cost_VND):,}</div>
            <div class="kpi-unit">Việt Nam Đồng (VNĐ)</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("ⓘ Công thức toán"):
            st.code("Cost = Cost_Machine + Cost_Tool_Wear")
            st.caption("Hệ thống tích hợp toán kinh tế gồm chi phí khấu hao giờ máy vận hành công nghệ và chi phí mài mòn thay thế mảnh cắt dao cụ.")

    # ==========================================
    # 7. CHUYÊN GIA KHUYẾN NGHỊ - RECOMENDATION AI ENGINE
    # ==========================================
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown("#### 🧠 INDUSTRIAL CONSULTING AI ENGINE (HỆ KHUYẾN NGHỊ THÔNG MINH)")
    
    warnings = []
    solutions = []
    
    if machine_load_pct > 100:
        warnings.append(f"❌ **Quá tải trục chính máy CNC ({machine_load_pct:.1f}%):** Công suất yêu cầu vượt giới hạn nguồn phát của trạm máy `{machine_selected}`.")
        solutions.append("- **Giải pháp kỹ thuật:** Hãy chủ động giảm chiều sâu cắt `ap` hoặc hạ tốc độ chạy dao bàn máy `F` xuống từ 15-20%.")
    elif machine_load_pct < 30:
        warnings.append(f"ℹ️ **Hiệu suất máy chưa tối ưu ({machine_load_pct:.1f}%):** Máy đang chạy dưới dải công suất động cơ hữu ích cực đại.")
        solutions.append("- **Khuyến nghị công nghệ:** Có thể tăng chiều rộng ăn dao ngang `ae` hoặc nâng tốc độ chạy dao để bóc tách kim loại nhanh hơn, tối ưu tiến độ nhà xưởng.")

    if Ra_final > strat_info["req_ra"]:
        warnings.append(f"⚠️ **Độ nhám Ra vượt tiêu chuẩn kỹ thuật thiết kế ({Ra_final:.2f} µm > Yêu cầu {strat_info['req_ra']} µm):** Bề mặt chi tiết thô ráp không đạt thông số bản vẽ CAM.")
        solutions.append("- **Giải pháp kỹ thuật:** Hãy giảm lượng tiến dao răng `fz` hoặc đổi sang chủng loại dao cụ có bán kính mũi đỉnh `R_corner` lớn hơn.")
        
    if Tool_Life_Min < 30:
        warnings.append(f"🚨 **Tuổi thọ dao cụ suy giảm nghiêm trọng ({Tool_Life_Min:.1f} phút):** Tốc độ mài mòn quá nhanh do ma sát sinh nhiệt vượt ngưỡng vật lý.")
        solutions.append("- **Giải pháp kỹ thuật:** Chuyển đổi phương thức tưới nguội sang hệ phun sương áp lực lớn `MQL` hoặc sử dụng dòng dao phủ công nghệ cao `TiAlN/AlTiN` của Sandvik Coromant.")

    if len(warnings) == 0:
        st.success("🎯 **Hệ thống đánh giá trạng thái thiết lập lý tưởng:** Chế độ cắt cân bằng hoàn hảo giữa động học máy, tuổi thọ lưỡi cắt cụt và biên độ chi phí kinh tế xưởng.")
    else:
        for w in warnings: st.markdown(w)
        st.markdown("##### 🛠️ BIỆN PHÁP XỬ LÝ CÔNG NGHỆ ĐỀ XUẤT TỪ CHUYÊN GIA INTERN:")
        for s in solutions: st.markdown(s)
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 8. MÔ PHỎNG HỒI QUY PHI TUYẾN - MULTI-CHART INTERACTIVE LAB
    # ==========================================
    st.markdown("### 📈 INDUSTRIAL CHART GRAPH LAB (MÔ PHỎNG ĐA BIẾN)")
    
    tab_c1, tab_c2, tab_c3 = st.tabs(["Biểu đồ Chất lượng bề mặt", "Biểu đồ Cơ học Cắt gọt", "Biểu đồ Phân tích Lịch sử DSS"])
    
    with tab_c1:
        fz_vector = np.linspace(0.01, 0.25, 40)
        ra_vector = ((fz_vector ** 2) / (32 * (r_corner if r_corner > 0 else 0.1))) * 1000
        chart_data_ra = pd.DataFrame({"Lượng chạy dao răng fz (mm/z)": fz_vector, "Độ nhám bề mặt Ra (µm)": ra_vector}).set_index("Lượng chạy dao răng fz (mm/z)")
        st.line_chart(chart_data_ra, y_label="Độ nhám Ra (µm)")
        st.caption("Đồ thị phi tuyến tính thể hiện tốc độ tăng trưởng của độ nhám bề mặt khi tăng bước tiến dao bàn máy.")
        
    with tab_c2:
        ap_vector = np.linspace(0.1, ap_input * 2, 40)
        fc_vector = [max(kc * a * ae_input * (F_feed / (S_speed * z_input)) / d_input * 1000 * 0.1, 50.0) for a in ap_vector]
        chart_data_fc = pd.DataFrame({"Chiều sâu cắt ap (mm)": ap_vector, "Lực cắt chính Fc (N)": fc_vector}).set_index("Chiều sâu cắt ap (mm)")
        st.line_chart(chart_data_fc, y_label="Lực cắt cơ học Fc (Newton)")
        st.caption("Mối quan hệ đồng biến tuyến tính giữa chiều sâu cắt lớp kim loại và ứng suất lực phát sinh đè lên đài dao.")

    with tab_c3:
        if st.session_state.history:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True)
            st.caption("Bảng dữ liệu lưu trữ vết của hệ thống DSS hỗ trợ so sánh đối chiếu giữa các lần cấu hình thông số khác nhau.")
        else:
            st.info("Chưa có dữ liệu lịch sử ghi nhận trong phiên chạy hiện tại.")

    # ==========================================
    # 9. EXPORT REPORT REPORT & DATA INTERCHANGE
    # ==========================================
    st.markdown("### 💾 EXPORT TECHNOLOGY SHEET (XUẤT PHIẾU CÔNG NGHỆ)")
    
    report_data = {
        "Project": "CNC OPERATOR DATA REPORT",
        "Material": mat_selected,
        "Hardness_HB": int(custom_hb),
        "Tool_Diameter_mm": d_input,
        "Spindle_Speed_RPM": int(S_speed),
        "Feed_Rate_mm_min": int(F_feed),
        "Calculated_Ra_um": round(Ra_final, 2),
        "Estimated_Power_kW": round(Net_Power_Required, 2),
        "Total_Cost_VND": int(Total_Cost_VND)
    }
    
    ex_c1, ex_c2, ex_c3 = st.columns(3)
    
    # Xuất định dạng JSON Công nghiệp
    json_str = json.dumps(report_data, indent=4, ensure_ascii=False)
    ex_c1.download_button(label="📥 Xuất tệp dữ liệu cấu hình (JSON)", data=json_str, file_name="cnc_dss_report.json", mime="application/json")
    
    # Xuất định dạng CSV cho Excel
    df_export = pd.DataFrame([report_data])
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    ex_c2.download_button(label="📊 Xuất bảng biểu báo cáo xưởng (CSV)", data=csv_data, file_name="cnc_dss_sheet.csv", mime="text/csv")
    
    # Nút in báo cáo nhanh dạng phiếu xưởng gia công
    if ex_c3.button("🖨️ Kích hoạt lệnh In phiếu công nghệ tại chỗ"):
        st.toast("Đang đồng bộ lệnh in hệ thống...", icon="⚙️")
        st.json(report_data)

    # ==========================================
    # 10. INDUSTRIAL G-CODE INTERACTIVE LIBRARY
    # ==========================================
    st.markdown("---")
    st.markdown("### 🗃️ THƯ VIỆN ĐIỀU KHIỂN & LẬP TRÌNH G-CODE / M-CODE TOÀN DIỆN")
    
    G_CODE_LIB = {
        "G00": "Định vị chạy dao nhanh không cắt cắt (Rapid positioning) - Dao chuyển động tăng tốc tối đa của trục máy để đến điểm chờ.",
        "G01": "Nội suy đường thẳng cắt gọt theo lượng tiến chạy dao cấu hình (Linear interpolation).",
        "G02": "Nội suy cung tròn biên dạng theo chiều quay kim đồng hồ (Circular interpolation CW).",
        "G03": "Nội suy cung tròn biên dạng ngược chiều quay kim đồng hồ (Circular interpolation CCW).",
        "G17": "Lựa chọn mặt phẳng làm việc chính tạo bởi trục tọa độ X và Y (XY Plane selection).",
        "G40": "Hủy bỏ toàn bộ các lệnh cấu hình bù trừ bán kính đỉnh dao phay trước đó.",
        "G41": "Kích hoạt chức năng bù trừ bán kính dao cụ về phía bên trái đường cắt biên dạng CAM.",
        "G42": "Kích hoạt chức năng bù trừ bán kính dao cụ về phía bên phải đường cắt biên dạng CAM.",
        "G43": "Bù trừ giá trị chiều dài hình học dao phay theo trục đứng Z (Kết hợp mã H).",
        "G54": "Lựa chọn hệ tọa độ làm việc của phôi số 1 cài đặt thực tế trên bàn máy gia công.",
        "M03": "Lệnh điều khiển trục chính quay theo chiều kim đồng hồ (Spindle ON Forward).",
        "M05": "Lệnh dừng hoàn toàn chuyển động quay của trục chính trung tâm gia công.",
        "M06": "Chấp hành lệnh tự động thay đổi dao cụ của đài ổ tích dao (Tool Change).",
        "M08": "Mở hệ thống phun dung dịch làm mát / tưới nguội làm mát vùng không gian cắt gọt.",
        "M30": "Kết thúc toàn bộ chương trình gia công lập trình và tự động quay ngược về dòng lệnh đầu."
    }
    
    search_query = st.text_input("🔍 Bộ lọc tìm kiếm nhanh mã lệnh lập trình máy CNC:", "")
    
    col_g_view1, col_g_view2 = st.columns(2)
    count = 0
    for code, desc in G_CODE_LIB.items():
        if search_query.upper() in code or search_query.lower() in desc.lower():
            target_col = col_g_view1 if count % 2 == 0 else col_g_view2
            with target_col:
                st.markdown(f"**`{code}`** — *{desc}*")
            count += 1
