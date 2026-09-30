import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# =========================================================
# CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="Tính lãi tiền gửi tiết kiệm",
    page_icon="💰",
    layout="wide"
)

# =========================================================
# CSS GIAO DIỆN
# =========================================================
st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 25px;
    }

    .result-card {
        padding: 20px;
        border-radius: 12px;
        background-color: #f7f7f7;
        border: 1px solid #ddd;
        text-align: center;
    }

    .result-title {
        font-size: 15px;
        color: #666;
        margin-bottom: 8px;
    }

    .result-value {
        font-size: 25px;
        font-weight: 700;
    }

    .formula-box {
        background-color: #f5f5f5;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HÀM ĐỊNH DẠNG TIỀN
# =========================================================
def format_money(value):
    """
    Định dạng số tiền theo VNĐ.
    Ví dụ: 10000000 -> 10.000.000 ₫
    """
    value = Decimal(str(value)).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )
    return f"{value:,.0f}".replace(",", ".") + " ₫"


def format_percent(value):
    return f"{value:.2f}%"


# =========================================================
# TÍNH LÃI ĐƠN
# =========================================================
def calculate_simple(principal, annual_rate, months, payout_type):
    """
    principal: số tiền gốc
    annual_rate: lãi suất %/năm
    months: kỳ hạn theo tháng
    payout_type: monthly / quarterly / maturity

    Công thức:
        I = P * r * t

    Trong đó:
        P = tiền gốc
        r = lãi suất năm dạng thập phân
        t = số năm
    """

    rate = annual_rate / 100
    years = months / 12

    total_interest = principal * rate * years
    total_amount = principal + total_interest

    # Xác định số kỳ
    if payout_type == "monthly":
        period_count = months
        period_months = 1
        period_interest = total_interest / period_count

    elif payout_type == "quarterly":
        period_count = months / 3
        period_months = 3
        period_interest = total_interest / period_count

    else:
        period_count = 1
        period_months = months
        period_interest = total_interest

    # Tạo bảng chi tiết
    schedule = []

    for i in range(1, int(period_count) + 1):
        if payout_type == "monthly":
            current_month = i

        elif payout_type == "quarterly":
            current_month = i * 3

        else:
            current_month = months

        accumulated_interest = period_interest * i
        balance = principal + accumulated_interest

        schedule.append({
            "Kỳ": i,
            "Thời gian": f"Tháng {int(current_month)}",
            "Tiền gốc": principal,
            "Lãi kỳ này": period_interest,
            "Tổng lãi": accumulated_interest,
            "Số dư gốc + lãi": balance
        })

    return {
        "period_interest": period_interest,
        "total_interest": total_interest,
        "total_amount": total_amount,
        "schedule": pd.DataFrame(schedule)
    }


# =========================================================
# TÍNH LÃI KÉP
# =========================================================
def calculate_compound(principal, annual_rate, months, payout_type):
    """
    Lãi kép:
        A = P * (1 + r/n)^(n*t)

    Trong đó:
        P = tiền gốc
        r = lãi suất năm
        n = số lần ghép lãi trong năm
        t = số năm

    Quy ước:
        - Hàng tháng: ghép lãi 12 lần/năm
        - Hàng quý: ghép lãi 4 lần/năm
        - Cuối kỳ: ghép lãi 1 lần vào cuối kỳ
    """

    rate = annual_rate / 100

    # -----------------------------------------------------
    # Trường hợp lãnh lãi hàng tháng
    # -----------------------------------------------------
    if payout_type == "monthly":

        period_rate = rate / 12
        period_count = months

        balance = principal
        schedule = []

        for i in range(1, period_count + 1):
            opening_balance = balance
            interest = opening_balance * period_rate
            balance = opening_balance + interest

            schedule.append({
                "Kỳ": i,
                "Thời gian": f"Tháng {i}",
                "Tiền gốc đầu kỳ": opening_balance,
                "Lãi kỳ này": interest,
                "Tổng lãi": balance - principal,
                "Số dư gốc + lãi": balance
            })

        total_amount = balance
        total_interest = total_amount - principal

        first_period_interest = (
            schedule[0]["Lãi kỳ này"] if schedule else 0
        )

    # -----------------------------------------------------
    # Trường hợp lãnh lãi hàng quý
    # -----------------------------------------------------
    elif payout_type == "quarterly":

        period_rate = rate / 4

        # Số quý đầy đủ + phần tháng còn lại
        full_quarters = months // 3
        remaining_months = months % 3

        balance = principal
        schedule = []
        period_number = 0

        # Ghép lãi theo từng quý
        for q in range(1, full_quarters + 1):
            period_number += 1

            opening_balance = balance
            interest = opening_balance * period_rate
            balance = opening_balance + interest

            schedule.append({
                "Kỳ": period_number,
                "Thời gian": f"Quý {q} - tháng {q * 3}",
                "Tiền gốc đầu kỳ": opening_balance,
                "Lãi kỳ này": interest,
                "Tổng lãi": balance - principal,
                "Số dư gốc + lãi": balance
            })

        # Nếu còn 1 hoặc 2 tháng thì tính phần thời gian còn lại
        if remaining_months > 0:

            period_number += 1

            opening_balance = balance

            # Lãi cho số tháng còn lại
            interest = (
                opening_balance
                * rate
                * (remaining_months / 12)
            )

            balance = opening_balance + interest

            schedule.append({
                "Kỳ": period_number,
                "Thời gian": f"{remaining_months} tháng cuối",
                "Tiền gốc đầu kỳ": opening_balance,
                "Lãi kỳ này": interest,
                "Tổng lãi": balance - principal,
                "Số dư gốc + lãi": balance
            })

        total_amount = balance
        total_interest = total_amount - principal

        first_period_interest = (
            schedule[0]["Lãi kỳ này"] if schedule else 0
        )

    # -----------------------------------------------------
    # Trường hợp lãnh lãi cuối kỳ
    # -----------------------------------------------------
    else:

        # Chỉ ghép lãi một lần vào cuối kỳ
        years = months / 12

        total_amount = principal * (1 + rate * years)
        total_interest = total_amount - principal

        first_period_interest = total_interest

        schedule = [{
            "Kỳ": 1,
            "Thời gian": f"Cuối kỳ - {months} tháng",
            "Tiền gốc đầu kỳ": principal,
            "Lãi kỳ này": total_interest,
            "Tổng lãi": total_interest,
            "Số dư gốc + lãi": total_amount
        }]

    return {
        "period_interest": first_period_interest,
        "total_interest": total_interest,
        "total_amount": total_amount,
        "schedule": pd.DataFrame(schedule)
    }


# =========================================================
# TIÊU ĐỀ
# =========================================================
st.markdown(
    '<div class="main-title">💰 TÍNH LÃI GỬI TIẾT KIỆM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Tính toán tiền lãi theo phương pháp lãi đơn và lãi kép'
    '</div>',
    unsafe_allow_html=True
)

# =========================================================
# KHU VỰC NHẬP THÔNG TIN
# =========================================================
st.sidebar.header("⚙️ Thông tin tiền gửi")

principal = st.sidebar.number_input(
    "Số tiền gửi (VNĐ)",
    min_value=100000,
    value=10000000,
    step=100000,
    format="%d"
)

months = st.sidebar.number_input(
    "Kỳ hạn (tháng)",
    min_value=1,
    max_value=120,
    value=12,
    step=1
)

interest_rate = st.sidebar.number_input(
    "Lãi suất (%/năm)",
    min_value=0.0,
    max_value=100.0,
    value=5.0,
    step=0.1,
    format="%.2f"
)

interest_type = st.sidebar.selectbox(
    "Phương pháp tính lãi",
    [
        "Lãi đơn",
        "Lãi kép"
    ]
)

payout_type = st.sidebar.selectbox(
    "Hình thức lãnh lãi",
    [
        "Hàng tháng",
        "Hàng quý",
        "Cuối kỳ"
    ]
)

# Chuyển lựa chọn sang mã xử lý
payout_map = {
    "Hàng tháng": "monthly",
    "Hàng quý": "quarterly",
    "Cuối kỳ": "maturity"
}

selected_payout = payout_map[payout_type]

# =========================================================
# NÚT TÍNH TOÁN
# =========================================================
calculate_button = st.sidebar.button(
    "🧮 TÍNH TIỀN LÃI",
    use_container_width=True
)

# =========================================================
# HIỂN THỊ THÔNG TIN ĐẦU VÀO
# =========================================================
st.subheader("📌 Thông tin khoản tiền gửi")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Tiền gửi",
        format_money(principal)
    )

with col2:
    st.metric(
        "Kỳ hạn",
        f"{months} tháng"
    )

with col3:
    st.metric(
        "Lãi suất",
        format_percent(interest_rate)
    )

with col4:
    st.metric(
        "Hình thức",
        payout_type
    )

st.divider()

# =========================================================
# TÍNH TOÁN
# =========================================================
if calculate_button:

    # ---------------------------------------------
    # TÍNH LÃI ĐƠN
    # ---------------------------------------------
    if interest_type == "Lãi đơn":
        result = calculate_simple(
            principal,
            interest_rate,
            months,
            selected_payout
        )

        formula = "I = P × r × t"

    # ---------------------------------------------
    # TÍNH LÃI KÉP
    # ---------------------------------------------
    else:
        result = calculate_compound(
            principal,
            interest_rate,
            months,
            selected_payout
        )

        formula = "A = P × (1 + r/n)^(n×t)"

    # =====================================================
    # KẾT QUẢ
    # =====================================================
    st.subheader("📊 Kết quả tính toán")

    c1, c2, c3 = st.columns(3)

    # Lãi định kỳ
    with c1:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-title">
                    Lãi phát sinh định kỳ (kỳ đầu)
                </div>
                <div class="result-value">
                    {format_money(result["period_interest"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Tổng lãi
    with c2:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-title">
                    Tổng tiền lãi
                </div>
                <div class="result-value">
                    {format_money(result["total_interest"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Tổng tiền
    with c3:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-title">
                    Tổng gốc + lãi
                </div>
                <div class="result-value">
                    {format_money(result["total_amount"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # =====================================================
    # CÔNG THỨC
    # =====================================================
    st.subheader("📝 Công thức áp dụng")

    st.markdown(
        f"""
        <div class="formula-box">
            <b>Phương pháp:</b> {interest_type}<br><br>
            <b>Công thức:</b> {formula}
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # GHI CHÚ
    # =====================================================
    if interest_type == "Lãi đơn":

        st.info(
            "💡 Lãi đơn: tiền lãi được tính trên số tiền gốc ban đầu "
            "và không cộng lãi vào vốn để tiếp tục sinh lãi."
        )

    else:

        if selected_payout == "monthly":
            st.info(
                "💡 Lãi kép hàng tháng: tiền lãi mỗi tháng được cộng vào "
                "số dư để tiếp tục sinh lãi vào tháng sau."
            )

        elif selected_payout == "quarterly":
            st.info(
                "💡 Lãi kép hàng quý: tiền lãi được cộng vào vốn sau mỗi quý."
            )

        else:
            st.info(
                "💡 Với lựa chọn cuối kỳ, toàn bộ lãi được tính và cộng "
                "vào số tiền gốc tại thời điểm đáo hạn."
            )

    # =====================================================
    # BẢNG CHI TIẾT
    # =====================================================
    st.subheader("📋 Chi tiết tiền lãi theo từng kỳ")

    df = result["schedule"].copy()

    # Định dạng tiền
    money_columns = [
        col for col in df.columns
        if "Tiền" in col or "Lãi" in col or "Số dư" in col
    ]

    for col in money_columns:
        df[col] = df[col].apply(format_money)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # TÓM TẮT
    # =====================================================
    st.subheader("📌 Tóm tắt")

    st.write(
        f"Với số tiền gửi **{format_money(principal)}**, "
        f"kỳ hạn **{months} tháng**, "
        f"lãi suất **{interest_rate:.2f}%/năm**, "
        f"theo hình thức **{payout_type}** và phương pháp **{interest_type}**:"
    )

    st.markdown(
        f"""
        **Tổng tiền lãi:** {format_money(result["total_interest"])}  
        
        **Tổng số tiền nhận được:** {format_money(result["total_amount"])}
        """
    )

else:

    # =====================================================
    # MÀN HÌNH BAN ĐẦU
    # =====================================================
    st.info(
        "👈 Nhập thông tin khoản tiền gửi ở thanh bên trái "
        "và nhấn **TÍNH TIỀN LÃI** để xem kết quả."
    )

    st.subheader("📖 Hướng dẫn sử dụng")

    st.markdown("""
    **Bước 1:** Nhập số tiền muốn gửi.

    **Bước 2:** Nhập kỳ hạn gửi theo số tháng.

    **Bước 3:** Nhập lãi suất (%/năm).

    **Bước 4:** Chọn phương pháp:
    - Lãi đơn
    - Lãi kép

    **Bước 5:** Chọn hình thức lãnh lãi:
    - Hàng tháng
    - Hàng quý
    - Cuối kỳ

    **Bước 6:** Nhấn **TÍNH TIỀN LÃI** để xem kết quả.
    """)

    st.warning(
        "Lưu ý: Lãi suất được hiểu là lãi suất danh nghĩa theo năm. "
        "Đây là công cụ tính toán minh họa, không phản ánh chính sách "
        "lãi suất hoặc cách làm tròn thực tế của từng ngân hàng."
    )
