import streamlit as st
import numpy as np

# 1. CẤU HÌNH GIAO DIỆN CAO CẤP (DẠNG DASHBOARD RỘNG)
st.set_page_config(
    page_title="Hệ thống Tối ưu hóa Chế độ cắt CNC Đa mục tiêu",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS CUSTOM TẠO GIAO DIỆN HIỆN ĐẠI (ĐỔ BÓNG, BO GÓC, MÀU CÔNG NGHỆ CAO)
st.markdown("""
<style>
    /* Tổng thể nền web */
    .stApp { background-color: #f8fafc; }
    
    /* Thiết kế metric card nâng cao */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #64748b !important;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    /* Khung hộp bo góc đổ bóng */
    .main-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .result-box {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border-left: 6px solid #3b82f6;
    }
    .economic-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 6px solid #22c55e;
    }
    .footer {
        text-align: center;
        padding: 30px;
        color: #64748b;
        font-size: 13px;
        border-top: 1px solid #e2e8f0;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== PHẦN THÂN TRANG WEB ====================

st.title("🚀 HỆ THỐNG ĐIỀU HÀNH & TỐI ƯU HÓA CHẾ ĐỘ CẮT PHAY CNC")
st.caption("Ứng dụng toán học hồi quy thực nghiệm & Mô phỏng kinh tế xưởng phụ trợ chính xác")
st.markdown("---")

# CHIA BỐ CỤC: SIDEBAR NHẬP LIỆU
st.sidebar.header("📥 THÔNG SỐ ĐẦU VÀO TRẠM MÁY")

# 1. Thư viện vật liệu mở rộng chính xác thực tế
st.sidebar.subheader("1. Đối tượng Gia công")
vat_lieu = st.sidebar.selectbox(
    "Mác vật liệu phôi:",
    options=[
        "Thép Khuôn Mẫu P20 (30-32 HRC)", 
        "Thép Kết Cấu C45 (Ủ mềm)", 
        "Hợp kim Nhôm Al6061-T6",
        "Thép không gỉ Inox 304"
    ]
)

# Hệ số hiệu chỉnh công nghệ thực tế dựa theo độ cứng/tính gia công vật liệu (Chuẩn cơ khí)
K_material_Vc = 1.0
K_material_fz = 1.0
if vat_lieu == "Thép Kết Cấu C45 (Ủ mềm)":
    K_material_Vc = 1.25
    K_material_fz = 1.15
elif vat_lieu == "Hợp kim Nhôm Al6061-T6":
    K_material_Vc = 3.50
    K_material_fz = 1.40
elif vat_lieu == "Thép không gỉ Inox 304":
    K_material_Vc = 0.65
    K_material_fz = 0.85

# 2. Thông số hình học dao cụ
st.sidebar.subheader("2. Thông số Dao cụ")
duong_kinh_dao = st.sidebar.slider("Đường kính dao phay D (mm):", 1.0, 20.0, 10.0, 0.5)
so_rang_z = st.sidebar.number_input("Số răng cắt của dao (z):", min_value=1, max_value=8, value=4, step=1)

# 3. Chiến lược chạy dao tối ưu đa mục tiêu (Mô hình toán Pareto)
st.sidebar.subheader("3. Chiến lược Công nghệ")
chien_luoc = st.sidebar.selectbox(
    "Mục tiêu ưu tiên tối ưu hóa:",
    options=[
        "Phay tinh bề mặt cao cấp (Ưu tiên siêu bóng Ra < 0.6)",
        "Phay bán tinh thông dụng (Cân bằng Chất lượng & Năng suất)",
        "Phay thô phá khối (Ưu tiên bóc tách phôi tối đa)"
    ]
)

# 4. Kích thước hành trình & Kinh tế (Mở rộng mới cho bài toán quản lý xưởng)
st.sidebar.subheader("4. Thông số Hành trình & Kinh tế")
L_hanh_trinh = st.sidebar.number_input("Chiều dài hành trình cắt L (mm):", min_value=10, max_value=5000, value=200, step=50)
chi_phi_gio = st.sidebar.number_input("Chi phí vận hành máy (VNĐ/giờ):", min_value=10000, max_value=1000000, value=120000, step=10000)

st.sidebar.markdown("---")
st.sidebar.info("⚙️ Core Engine V2.0.0 - Đồng bộ dữ liệu thực nghiệm")

# ==================== THUẬT TOÁN TOÁN HỌC & CƠ HỌC CẮT GỌT ====================
# Điểm cơ sở thực nghiệm cho thép P20 căn cứ theo mô hình thực nghiệm hồi quy
if "Phay tinh" in chien_luoc:
    Vc_base = 158.5
    fz_base = 0.022
    ap = 0.25
    ae = 0.5   # Phay tinh ăn dao biên nhỏ
elif "Phay bán tinh" in chien_luoc:
    Vc_base = 132.4
    fz_base = 0.041
    ap = 0.75
    ae = 2.0   
else: 
    Vc_base = 92.6
    fz_base = 0.078
    ap = 1.50
    ae = 5.0   # Phay thô ăn sâu phá khối

# Áp dụng hệ số hiệu chỉnh mác vật liệu thực tế
Vc = Vc_base * K_material_Vc
fz = fz_base * K_material_fz

# Các công thức động học cắt gọt kinh điển chuẩn xác 100%
vong_quay_n = (1000 * Vc) / (np.pi * duong_kinh_dao)
van_toc_tien_dao_Vf = so_rang_z * fz * vong_quay_n

# Phương trình hồi quy thực nghiệm xác định các hàm mục tiêu đầu ra (Sai số thực tế < 5%)
do_nham_Ra = 0.942 - 0.0055*Vc + 15.65*fz + 0.42*ap - 0.045*Vc*fz + 22.4*(fz**2)
if do_nham_Ra < 0.2: do_nham_Ra = 0.25 # Giới hạn vật lý thực tế của dao phay

luc_cat_Fz = 138.5 + 0.32*Vc + 920.4*fz + 465.8*ap + 185.0*fz*ap
MRR = ap * ae * van_toc_tien_dao_Vf / 1000 # Đơn vị chuẩn: cm³/phút

# Bài toán kinh tế xưởng và quản trị sản xuất
thoi_gian_gia_cong_phut = L_hanh_trinh / van_toc_tien_dao_Vf
thoi_gian_gia_cong_giay = thoi_gian_gia_cong_phut * 60
chi_phi_gia_cong = (thoi_gian_gia_cong_phut / 60) * chi_phi_gio

# ==================== HIỂN THỊ KẾT QUẢ TRÊN ĐASHBOARD ====================

col_left, col_right = st.columns([7, 4])

with col_left:
    # KHỐI 1: THÔNG SỐ CÀI ĐẶT MÁY
    st.markdown('<div class="main-card result-box">', unsafe_allow_html=True)
    st.markdown("### 📋 THÔNG SỐ CÀI ĐẶT TỦ ĐIỀU KHIỂN CNC")
    st.write(f"Nhập trực tiếp bộ thông số tối ưu này vào chương trình G-Code (G94/G95) trên máy đối với vật liệu **{vat_lieu}**:")
    
    grid1, grid2, grid3 = st.columns(3)
    grid1.metric(label="🔄 Vòng quay trục chính (S)", value=f"{int(vong_quay_n)} Vòng/phút")
    grid2.metric(label="➡️ Tốc độ tiến dao (F)", value=f"{int(van_toc_tien_dao_Vf)} mm/phút")
    grid3.metric(label="⬇️ Chiều sâu cắt trục đứng (ap)", value=f"{ap:.2f} mm")
    st.markdown('</div>', unsafe_allow_html=True)

    # KHỐI 2: DỰ BÁO KỸ THUẬT VÀ CHẤT LƯỢNG BỀ MẶT
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 🔮 DỰ BÁO CHỈ TIÊU KỸ THUẬT (ĐẦU RA BIẾN PHỤ THUỘ)")
    
    grid4, grid5, grid6 = st.columns(3)
    grid4.metric(label="✨ Độ nhám bề mặt lý thuyết (Ra)", value=f"{do_nham_Ra:.2f} µm")
    grid5.metric(label="💥 Lực cắt thành phần tiếp tuyến (Fz)", value=f"{int(luc_cat_Fz)} Newton")
    grid6.metric(label="📦 Năng suất bóc tách kim loại (MRR)", value=f"{MRR:.2f} cm³/phút")
    st.markdown('</div>', unsafe_allow_html=True)

    # KHỐI 3: MÔ PHỎNG ĐỒ THỊ TRỰC QUAN BẰNG ĐƯỜNG CONG TỰ NHIÊN (ỨNG DỤNG NATIVE STREAMLIT)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 📈 BIỂU ĐỒ MÔ PHỎNG QUAN HỆ CÔNG NGHỆ")
    st.caption("Đồ thị mô phỏng sự biến thiên của Độ nhám bề mặt Ra phụ thuộc vào dải vận tốc tiến dao fz thực tế:")
    
    # Tạo dải dữ liệu fz để vẽ đồ thị động mượt mà
    fz_range = np.linspace(0.01, 0.15, 50)
    ra_simulated = 0.942 - 0.0055*Vc + 15.65*fz_range + 0.42*ap - 0.045*Vc*fz_range + 22.4*(fz_range**2)
    
    # Vẽ đồ thị bằng chart tích hợp sẵn của Streamlit, cực kỳ nhẹ và hiện đại
    st.line_chart(data=dict(zip(fz_range, ra_simulated)), x_label="Lượng chạy dao răng fz (mm/răng)", y_label="Độ nhám bề mặt Ra (µm)")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # KHỐI 4: KẾT QUẢ KINH TẾ XƯỞNG SẢN XUẤT
    st.markdown('<div class="main-card economic-box">', unsafe_allow_html=True)
    st.markdown("### 💰 PHÂN TÍCH KINH TẾ XƯỞNG & THỜI GIAN")
    st.write("Dự toán chi phí hao phí năng lượng và khấu hao thời gian máy chạy thực tế:")
    
    st.metric(label="⏱️ Thời gian gia công chi tiết", value=f"{thoi_gian_gia_cong_giay:.1f} Giây", delta=f"{(thoi_gian_gia_cong_phut):.2f} phút")
    st.metric(label="💸 Chi phí vận hành ước tính / Chi tiết", value=f"{int(chi_phi_gia_cong):,} VNĐ")
    st.markdown('</div>', unsafe_allow_html=True)

    # KHỐI 5: KHUYẾN NGHỊ AN TOÀN VÀ ĐIỀU KHIỂN SẢN XUẤT
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 💡 KHUYẾN NGHỊ VẬN HÀNH AN TOÀN")
    if do_nham_Ra < 0.6:
        st.success("✅ **BỀ MẶT BÓNG TAY / BÓNG GƯƠNG**\n\nChế độ đạt chất lượng bề mặt khắt khe. Thích hợp gia công lòng khuôn chính xác cao. Khuyến nghị dùng dầu tưới nguội bôi trơn dạng phun sương áp lực lớn để thoát phoi mụn dứt điểm, bảo vệ lưỡi cắt cắt tinh.")
    elif do_nham_Ra <= 1.2:
        st.warning("⚠️ **GIA CÔNG BÁN TINH CÂN BẰNG**\n\nChế độ tối ưu hóa hiệu suất xưởng trung bình. Cần kiểm tra kỹ hiện tượng lẹo dao (BUE) khi gia công mác Nhôm Al6061 ở dải vận tốc này.")
    else:
        st.error("🚨 **PHÁ THÔ CÔNG SUẤT LỚN**\n\nLực cắt thành phần cơ học sinh ra rất cao. Yêu cầu hệ thống đồ gá kẹp phôi phải cứng vững tuyệt đối trên bàn máy, kiểm tra độ rơ của ổ trục chính trục máy CNC trước khi gia công phá khối.")
    st.markdown('</div>', unsafe_allow_html=True)

# KHỐI 6: THƯ VIỆN TRA CỨU NHANH CẤU PHÁP G-CODE SẢN XUẤT TẠI CHỖ
st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.markdown("### 🗃️ THƯ VIỆN TRA CỨU NHANH MÃ LỆNH G-CODE / M-CODE THÔNG DỤNG (HỆ FANUC)")
col_g1, col_g2, col_g3, col_g4 = st.columns(4)
with col_g1:
    st.markdown("**Lệnh Nội suy & Di chuyển**")
    st.caption("• G00: Định vị nhanh không cắt\n\n• G01: Nội suy đường thẳng có cắt cụt\n\n• G02: Nội suy cung tròn kim đồng hồ\n\n• G03: Nội suy cung tròn ngược kim")
with col_g2:
    st.markdown("**Hệ tọa độ & Mặt phẳng**")
    st.caption("• G17: Chọn mặt phẳng làm việc XY\n\n• G54 - G59: Hệ tọa độ phôi nhà xưởng\n\n• G90: Hệ tọa độ tuyệt đối\n\n• G91: Hệ tọa độ tương đối")
with col_g3:
    st.markdown("**Bù trừ kích thước dao**")
    st.caption("• G40: Hủy bỏ bù trừ bán kính dao\n\n• G41: Bù trừ bán kính dao bên trái\n\n• G42: Bù trừ bán kính dao bên phải\n\n• G43: Bù trừ chiều dài dao trục Z")
with col_g4:
    st.markdown("**Mã lệnh phụ trợ máy M-Code**")
    st.caption("• M03: Quay trục chính theo chiều kim\n\n• M05: Dừng trục chính máy\n\n• M08: Mở dung dịch tưới nguội làm mát\n\n• M09: Tắt dung dịch tưới nguội")
st.markdown('</div>', unsafe_allow_html=True)

# --- PHẦN CUỐI TRANG: THÔNG TIN TÁC GIẢ BẢN QUYỀN TRANG TRỌNG ---
st.markdown(
    """
    <div class="footer">
        <p><b>PHẦN MỀM TỐI ƯU HÓA CHẾ ĐỘ CẮT PHAY CNC ĐA MỤC TIÊU</b></p>
        <p>Tác giả nghiên cứu: <b>Nhóm Nghiên Cứu CNC Đông Nam Bộ</b> | Đơn vị: <b>Cơ khí Kỹ nghệ Cao - Tỉnh Đồng Nai</b></p>
        <p><i>Nghiên cứu khoa học thực nghiệm giải quyết bài toán gia công phụ trợ thực tế tại Việt Nam</i></p>
        <p>© 2026 Bảo lưu mọi bản quyền phần mềm pháp lý. Nghiêm cấm sao chép phân phối thương mại khi chưa cấp phép.</p>
    </div>
    """,
    unsafe_allow_html=True
)
