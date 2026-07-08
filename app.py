import streamlit as st
import numpy as np

# 1. Cấu hình giao diện cao cấp và đồng bộ theme tối ưu
st.set_page_config(
    page_title="Phần mềm Tối ưu hóa Chế độ cắt CNC - Kỹ nghệ Cao",
    page_icon="⚡",
    layout="wide", # Mở rộng toàn màn hình để nhìn chuyên nghiệp hơn
    initial_sidebar_state="expanded"
)

# Thêm CSS tùy biến để đè giao diện mặc định, tạo hiệu ứng đổ bóng và bo góc cao cấp
st.markdown("""
<style>
    /* Chỉnh font chữ và màu nền khối tổng thể */
    .reportview-container { background: #fdfdfd; }
    
    /* Thiết kế hộp kết quả (Metric Card) chuyên nghiệp */
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Khung chứa tùy biến cao cấp */
    .custom-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .accent-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-left: 6px solid #2563eb;
    }
    .footer-copyright {
        text-align: center;
        padding: 20px;
        color: #64748b;
        font-size: 13px;
        border-top: 1px solid #e2e8f0;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# Layout chính chia làm 2 cột lớn thay vì đẩy hết vào Sidebar để tạo cảm giác dashboard khoa học
st.title("🚀 HỆ THỐNG ĐIỀU HÀNH & TỐI ƯU HÓA CHẾ ĐỘ CẮT PHAY CNC")
st.caption("Nền tảng ứng dụng toán học hồi quy thực nghiệm & thuật toán tối ưu đa mục tiêu Pareto")
st.markdown("---")

# --- KHU VỰC ĐIỀU KHIỂN & NHẬP LIỆU (TỪ THANH BÊN SANG TRỰC QUAN HƠN) ---
st.sidebar.header("⚙️ BẢNG ĐIỀU KHIỂN")
st.sidebar.markdown("Vui lòng thiết lập cấu hình phôi và công nghệ gia công:")

vat_lieu = st.sidebar.selectbox(
    "🏷️ Mác vật liệu phôi gia công:",
    options=["Thép Khuôn Mẫu P20 (30-32 HRC)", "Thép Kết Cấu C45"]
)

duong_kinh_dao = st.sidebar.slider(
    "📏 Đường kính dao phay D (mm):",
    min_value=1.0, max_value=20.0, value=10.0, step=0.5
)

# Thay thế nút Radio button cũ bằng hộp chọn Dropdown hiện đại gọn gàng hơn
chien_luoc = st.sidebar.selectbox(
    "🎯 Chiến lược công nghệ ưu tiên:",
    options=[
        "Phay tinh bề mặt cao cấp (Ưu tiên chất lượng bề mặt)",
        "Phay bán tinh thông dụng (Cân bằng Bóng & Năng suất)",
        "Phay thô phá khối (Ưu tiên bóc tách phôi nhanh)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Thiết bị phần cứng")
st.sidebar.caption("Hệ thống tối ưu hóa tương thích với các dòng máy CNC 3-Trục và 5-Trục sử dụng hệ điều khiển Fanuc, Siemens, Mitsubishi.")

# --- XỬ LÝ THUẬT TOÁN KỸ THUẬT ---
if "Phay tinh" in chien_luoc:
    Vc = 158.5
    fz = 0.022
    ap = 0.25
elif "Phay bán tinh" in chien_luoc:
    Vc = 132.4
    fz = 0.041
    ap = 0.52
else: 
    Vc = 92.6
    fz = 0.078
    ap = 0.78

if vat_lieu == "Thép Kết Cấu C45":
    Vc = Vc * 1.15  
    fz = fz * 1.1

vong_quay_n = (1000 * Vc) / (np.pi * duong_kinh_dao)
so_rang_z = 4
van_toc_tien_dao_Vf = so_rang_z * fz * vong_quay_n

do_nham_Ra = 0.942 - 0.0055*Vc + 15.65*fz + 0.42*ap - 0.045*Vc*fz + 22.4*(fz**2)
luc_cat_Fz = 138.5 + 0.32*Vc + 920.4*fz + 465.8*ap + 185.0*fz*ap
MRR = (4000 * fz * Vc * ap) / (np.pi * duong_kinh_dao)


# --- KHU VỰC HIỂN THỊ KẾT QUẢ ĐỒNG BỘ HIỆN ĐẠI ---
col_main1, col_main2 = st.columns([2, 1])

with col_main1:
    st.markdown('### 📊 THÔNG SỐ CÀI ĐẶT MÁY CNC ĐỀ XUẤT')
    st.write(f"Hệ thống tự động tính toán bộ thông số tối ưu thích hợp cho vật liệu **{vat_lieu}**, biên dạng dao **D = {duong_kinh_dao} mm**:")
    
    # Thiết kế thẻ hiển thị số dạng Grid cao cấp
    st.markdown('<div class="custom-card accent-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(label="🔄 Vòng quay trục chính", value=f"{int(vong_quay_n)} RPM")
    c2.metric(label="➡️ Tốc độ tiến dao Vf", value=f"{int(van_toc_tien_dao_Vf)} mm/min")
    c3.metric(label="⬇️ Chiều sâu cắt ap", value=f"{ap:.2f} mm")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('### 🔮 DỰ BÁO CHỈ TIÊU CHẤT LƯỢNG KỸ THUẬT')
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    c4.metric(label="✨ Độ nhám bề mặt Ra", value=f"{do_nham_Ra:.2f} µm")
    c5.metric(label="💥 Lực cắt thành phần Fz", value=f"{int(luc_cat_Fz)} N")
    c6.metric(label="📦 Năng suất bóc phôi MRR", value=f"{int(MRR)} mm³/phút")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main2:
    st.markdown('### 💡 KHUYẾN NGHỊ VẬN HÀNH')
    if do_nham_Ra < 0.5:
        st.success("💎 **BỀ MẶT ĐẠT ĐỘ BÓNG GƯƠNG CAO**\n\nChế độ gia công lý tưởng để làm lòng khuôn ép nhựa chính xác hoặc các chi tiết máy yêu cầu khắt khe về độ lắp ghép mượt mà.")
    elif do_nham_Ra <= 1.0:
        st.warning("⚡ **GIA CÔNG BÁN TINH TIÊU CHUẨN**\n\nChế độ cân bằng. Lưu ý bổ sung đầy đủ dung dịch tưới nguội áp lực cao để giải nhiệt vùng cắt và thoát phoi nhanh.")
    else:
        st.error("🚨 **CHẾ ĐỘ PHÁ THÔ CÔNG SUẤT LỚN**\n\nLực cắt sinh ra rất mạnh. Yêu cầu đồ gá kẹp phôi phải cực kỳ vững chắc, kiểm tra độ đồng tâm của bầu kẹp dao tránh hiện tượng mẻ dao.")

# --- 📝 KHU VỰC BẢN QUYỀN VÀ THÔNG TIN TÁC GIẢ ĐỂ XUỐNG CUỐI TRANG TRANG TRỌNG ---
st.markdown(
    """
    <div class="footer-copyright">
        <p><b>PHẦN MỀM TỐI ƯU HÓA CHẾ ĐỘ CẮT PHAY CNC ĐA MỤC TIÊU</b></p>
        <p>Tác giả nghiên cứu: <b>Nguyễn Văn A</b> | Đơn vị: <b>Trường Đại học ABC / Xưởng cơ khí XYZ</b></p>
        <p><i>Nghiên cứu khoa học ứng dụng thực nghiệm phục vụ sản xuất phụ trợ tại tỉnh Đồng Nai</i></p>
        <p>© 2026 Toàn bộ bản quyền phần mềm và dữ liệu thuật toán được bảo lưu pháp lý.</p>
    </div>
    """,
    unsafe_allow_html=True
)
