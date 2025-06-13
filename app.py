import streamlit as st

# ── Page Configuration ──
st.set_page_config(
    page_title="eKYC Video PoC",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Custom Neumorphic + Minimal CSS ──
st.markdown(
    """
    <style>
    /* Global background and font */
    .stApp {
      background: #e0e5ec;
      color: #333;
      font-family: "Segoe UI", Roboto, sans-serif;
    }
    /* Neumorphic card style */
    .neumorphic-card {
      background: #e0e5ec;
      border-radius: 16px;
      box-shadow: 8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    /* Neumorphic button style */
    .neumorphic-button button {
      background: #e0e5ec !important;
      border-radius: 50px !important;
      color: #333 !important;
      padding: 0.6rem 1.2rem !important;
      box-shadow: 4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff !important;
      border: none !important;
    }
    .neumorphic-button button:active {
      box-shadow: inset 2px 2px 4px #a3b1c6, inset -2px -2px 4px #ffffff !important;
    }
    /* Hide default Streamlit header/menu */
    #MainMenu, footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# ── Title & Privacy Note ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.title("🛡️ eKYC Video-Verification PoC")
st.write("🔒 This PoC does **not** store any personal data beyond your session. All uploads are destroyed when you close your browser.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 1: Math Captcha ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 1 of 3: Human Verification")
st.write("💡 Please solve the math captcha to continue.")
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
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 2: Front-of-ID Upload ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 2 of 3: ID Upload")
if captcha_passed:
    uploaded = st.file_uploader(
        "Upload the **front side** of your photo ID (JPEG/PNG/PDF)",
        type=["jpg", "jpeg", "png", "pdf"]
    )
    if uploaded:
        st.success(f"✅ File received: {uploaded.name}")
        st.info("Next: Video recording and verification steps will appear here.")
else:
    st.info("🔒 Complete the captcha above to proceed.")
st.markdown('</div>', unsafe_allow_html=True)
