import streamlit as st

# — Page Config —
st.set_page_config(
    page_title="eKYC Video PoC",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# — Header & Instructions —
st.title("🛡️ eKYC Video-Verification PoC")
st.info("💡 Step 1 of 3: Solve the math captcha to begin.")

# — 1) Math Captcha —
captcha_question = "9 - 2 = ?"
captcha_answer = st.text_input(f"Solve: {captcha_question}", key="captcha")

captcha_passed = False
if captcha_answer:
    try:
        if int(captcha_answer.strip()) == 7:
            st.success("✔️ Correct! You may now upload your ID.")
            captcha_passed = True
        else:
            st.error("❌ Incorrect—please try again.")
    except ValueError:
        st.error("⚠️ Please enter a valid number.")

# — 2) Front-of-ID Upload —
if captcha_passed:
    st.info("💡 Step 2 of 3: Upload the **front** of your photo ID (JPEG/PNG/PDF).")
    uploaded = st.file_uploader(
        "Upload front of your photo ID",
        type=["jpg", "jpeg", "png", "pdf"]
    )
    if uploaded:
        st.write("✅ File received:", uploaded.name)
        # Placeholder for next steps
        st.info("Next: Video recording and verification will appear here.")

else:
    # Keep uploader disabled until captcha is correct
    st.info("🔒 Complete the captcha above to proceed.")
