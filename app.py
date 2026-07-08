import streamlit as st
import numpy as np

# 1. Cấu hình giao diện trang Web
st.set_page_config(
    page_title="Phần mềm Tối ưu CNC - Bản quyền tác giả",
    page_icon="⚙️",
    layout="centered"
)

# --- 🌟 KHU VỰC BẢN QUYỀN TÁC GIẢ 🌟 ---
st.markdown("""
<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px;">
    <h4 style="margin: 0; color: #1f77b4;">📝 THÔNG TIN BẢN QUYỀN & TÁC GIẢ</h4>
    <p style="margin: 5px 0 0 0; font-size: 14px;">
        <b>Tác giả nghiên cứu:</b> Nhóm Nghiên Cứu CNC (Bạn có thể đổi tên bạn sau nhé)<br>
        <b>Đơn vị công tác:</b> Tỉnh Đồng Nai<br>
        <b>Đề tài:</b> Nghiên cứu tối ưu hóa đa mục tiêu chế độ cắt trong phay CNC<br>
        <i>© 2026 Bảo lưu mọi bản quyền. Nghiêm cấm sao chép dưới mọi hình thức thương mại.</i>
    </p>
</div>
""", unsafe_allow_html=True)

# 2. Tiêu đề chính của trang web
st.title("⚙️ HỆ THỐNG TRA CỨU & TỐI ƯU HÓA CHẾ ĐỘ CẮT PHAY CNC")
st.subheader("Ứng dụng toán học hồi quy thực nghiệm cho các xưởng cơ khí phụ trợ Đông Nam Bộ")
st.markdown("---")

# 3. Thanh bên (Sidebar) để người dùng nhập thông số đầu vào
st.sidebar.header("📥 THÔNG SỐ ĐẦU VÀO")

vat_lieu = st.sidebar.selectbox(
    "1. Chọn mác vật liệu phôi:",
    options=["Thép Khuôn Mẫu P20 (30-32 HRC)", "Thép Kết Cấu C45"]
)

duong_kinh_dao = st.sidebar.number_input(
    "2. Đường kính dao phay D (mm):",
    min_value=1.0, max_value=20.0, value=10.0, step=1.0
)

chien_luoc = st.sidebar.radio(
    "3. Chọn chiến lược gia công ưu tiên:",
    options=[
        "Phay tinh bề mặt cao cấp (Ưu tiên bề mặt siêu bóng)",
        "Phay bán tinh thông dụng (Cân bằng Bóng & Năng suất)",
        "Phay thô phá khối (Ưu tiên bóc tách phôi nhanh)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("📌 Sản phẩm độc quyền của Nhóm nghiên cứu - Đồng Nai, 2026.")

# 4. Xử lý thuật toán dựa trên điểm nghiệm Pareto đã nghiên cứu
if chien_luoc == "Phay tinh bề mặt cao cấp (Ưu tiên bề mặt siêu bóng)":
    Vc = 158.5
    fz = 0.022
    ap = 0.25
elif chien_luoc == "Phay bán tinh thông dụng (Cân bằng Bóng & Năng suất)":
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

# 5. Tính toán các thông số kỹ thuật đầu ra
vong_quay_n = (1000 * Vc) / (np.pi * duong_kinh_dao)
so_rang_z = 4
van_toc_tien_dao_Vf = so_rang_z * fz * vong_quay_n

do_nham_Ra = 0.942 - 0.0055*Vc + 15.65*fz + 0.42*ap - 0.045*Vc*fz + 22.4*(fz**2)
luc_cat_Fz = 138.5 + 0.32*Vc + 920.4*fz + 465.8*ap + 185.0*fz*ap
MRR = (4000 * fz * Vc * ap) / (np.pi * duong_kinh_dao)

# 6. Hiển thị kết quả ra màn hình trang web
st.header("📋 THÔNG SỐ CÀI ĐẶT MÁY CNC ĐỀ XUẤT")
st.write(f"Dựa trên các thuật toán tối ưu đa mục tiêu, dưới đây là bộ thông số khuyến nghị cài đặt trực tiếp vào tủ điều khiển của máy phay CNC đối với vật liệu **{vat_lieu}**, sử dụng dao **D = {duong_kinh_dao} mm**:")

col1, col2, col3 = st.columns(3)
col1.metric(label="🔄 Vòng quay trục chính (n)", value=f"{int(vong_quay_n)} vòng/phút")
col2.metric(label="➡️ Tốc độ tiến dao (Vf)", value=f"{int(van_toc_tien_dao_Vf)} mm/phút")
col3.metric(label="⬇️ Chiều sâu cắt (ap)", value=f"{ap:.2f} mm")

st.markdown("---")

# 7. Hiển thị dự báo kỹ thuật
st.header("🔮 ĐÁNH GIÁ & DỰ BÁO KỸ THUẬT")
st.write("Các chỉ tiêu chất lượng và vận hành dự kiến đạt được (Sai số thực nghiệm < 6%):")

col4, col5, col6 = st.columns(3)
col4.metric(label="✨ Độ nhám bề mặt dự tính (Ra)", value=f"{do_nham_Ra:.2f} µm")
col5.metric(label="💥 Lực cắt thành phần (Fz)", value=f"{int(luc_cat_Fz)} N")
col6.metric(label="📦 Năng suất bóc phôi (MRR)", value=f"{int(MRR)} mm³/phút")

st.markdown("### 💡 Lời khuyên vận hành an toàn cho nhà xưởng:")
if do_nham_Ra < 0.5:
    st.success("✅ Bề mặt chi tiết đạt độ bóng gương cao. Thích hợp cho các bề mặt lắp ghép lòng khuôn chính xác của khuôn ép nhựa.")
elif do_nham_Ra <= 1.0:
    st.warning("⚠️ Bề mặt đạt độ bóng trung bình. Thích hợp cho gia công bán tinh, cần kiểm tra dung dịch tưới nguội để tránh sinh nhiệt.")
else:
    st.error("🚨 Lực cắt lớn và độ nhám cao. Chế độ này chỉ dùng để phá thô dầm/phôi khối. Cần đảm bảo đồ gá kẹp (Ê-tô) cực kỳ vững chắc để tránh bật phôi.")
