import streamlit as st
import joblib
import numpy as np
import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# Set background CSS
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1497493292307-31c376b6e479");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .block-container {
        background-color: rgba(0, 0, 0, 0.85);
        padding: 2rem;
        border-radius: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load model
model = joblib.load('loan_approval_model.pkl')

st.title("🏦 Loan Approval Predictor")
st.write("Fill the form below to check if your loan might be approved.")

# User input form
gender = st.selectbox("Gender", ["Male", "Female", "Other"])
married = st.selectbox("Married", ["Yes", "No"])
dependents = st.selectbox("Dependents", ["0", "1", "2", "3", "More Than 3"])
education = st.selectbox("Education", ["Graduate", "Not Graduate"])
self_employed = st.selectbox("Self Employed", ["Yes", "No"])
applicant_income = st.number_input("Applicant Income", min_value=0)
coapplicant_income = st.number_input("Coapplicant Income", min_value=0)
loan_amount = st.number_input("Loan Amount (in actual amount, ₹)", min_value=0)
loan_amount_term_in_Months = st.number_input("Loan Term (Months)", min_value=0)
credit_history = st.selectbox("Credit History", ["1", "0"])
property_area = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])

# Encode inputs
def encode_inputs():
    gender_val = 1 if gender == "Male" else 0
    married_val = 1 if married == "Yes" else 0
    dependents_val = 3 if dependents == "More Than 3" else int(dependents)
    education_val = 1 if education == "Graduate" else 0
    self_emp_val = 1 if self_employed == "Yes" else 0
    credit_hist_val = int(credit_history)
    prop_area_val = {"Rural": 0, "Semiurban": 1, "Urban": 2}[property_area]
    return np.array([[gender_val, married_val, dependents_val, education_val,
                      self_emp_val, applicant_income, coapplicant_income,
                      loan_amount, loan_amount_term_in_Months, credit_hist_val,
                      prop_area_val]])

# Button
if st.button("Check Loan Status"):
    if applicant_income == 0 or loan_amount == 0 or loan_amount_term_in_Months == 0:
        st.warning("⚠️ Please fill all required numeric fields with values greater than 0.")
    else:
        input_data = encode_inputs()
        prediction = model.predict(input_data)[0]

        if prediction == 1:
            result_msg = "✅ Loan is likely to be APPROVED!"
            st.success(result_msg)
        else:
            result_msg = "❌ Loan is likely to be REJECTED."
            st.error(result_msg)

        # Summary
        with st.expander("📋 Applicant Summary"):
            st.markdown(f"""
            - **Gender**: {gender}  
            - **Married**: {married}  
            - **Dependents**: {dependents}  
            - **Education**: {education}  
            - **Self Employed**: {self_employed}  
            - **Applicant Income**: ₹{applicant_income:,}  
            - **Coapplicant Income**: ₹{coapplicant_income:,}  
            - **Loan Amount**: ₹{loan_amount:,}
            - **Loan Term**: {loan_amount_term_in_Months} months  
            - **Credit History**: {'Good' if credit_history == '1' else 'Bad'}  
            - **Property Area**: {property_area}  
            """)

            # ===== PDF Generation =====
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'ttf/DejaVuSans-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'ttf/DejaVuSans.ttf'))

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ---------- BANK ICON + TITLE ----------
        emoji_image = "Images/Bank_Image.png"  # Your emoji PNG path
        icon_width = 40
        icon_height = 40
        icon_x = (width - icon_width) / 2
        icon_y = height - 80

        # Draw Bank Image
        c.drawImage(ImageReader(emoji_image), icon_x, icon_y, width=icon_width, height=icon_height, mask='auto')

        # Title Below Bank Image
        title_y = icon_y - 20
        c.setFont("DejaVuSans-Bold", 20)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2, title_y, "Loan Prediction Report")

        # ---------- RESULT STAMP IMAGE + MESSAGE ON SAME LINE ----------
        if prediction == 1:
            result_image = "Images/approved_stamp.png"
            result_text = "Congratulations! Your loan is likely to be APPROVED!"
            color = colors.green
        else:
            result_image = "Images/rejected_stamp.png"
            result_text = "Unfortunately, your loan is likely to be REJECTED."
            color = colors.red

        # Set positions
        result_y = height - 210
        stamp_width = 25
        stamp_height = 25
        margin_x = 60

        # Draw result image (left side)
        c.drawImage(result_image, margin_x, result_y, width=stamp_width, height=stamp_height, mask='auto')

        # Draw result text right next to image
        c.setFont("DejaVuSans-Bold", 14)
        c.setFillColor(color)
        c.drawString(margin_x + stamp_width + 10, result_y + 5, result_text)
        c.setFillColor(colors.black)

        # ---------- APPLICANT DETAILS ----------
        details = [
            "",
            "Applicant Details:",
            f"• Gender: {gender}",
            f"• Married: {married}",
            f"• Dependents: {dependents}",
            f"• Education: {education}",
            f"• Self Employed: {self_employed}",
            f"• Applicant Income: ₹{applicant_income:,}",
            f"• Coapplicant Income: ₹{coapplicant_income:,}",
            f"• Loan Amount: ₹{loan_amount:,}",
            f"• Loan Term: {loan_amount_term_in_Months} months",
            f"• Credit History: {'Good' if credit_history == '1' else 'Bad'}",
            f"• Property Area: {property_area}",
        ]

        details_y = result_y - 50
        for line in details:
            c.drawString(margin_x, details_y, line)
            details_y -= 18

        # ---------- FOOTER ----------
        c.setFont("DejaVuSans", 10)
        c.setFillColor(colors.grey)
        c.drawRightString(width - 40, 52, "Generated by Loan Approval App")
        c.drawRightString(width - 40, 40, "by Ashish")

        c.showPage()
        c.save()
        buffer.seek(0)

        # Download button
        st.download_button(
            label="📄 Download Report",
            data=buffer,
            file_name="loan_report.pdf",
            mime="application/pdf"
        )
