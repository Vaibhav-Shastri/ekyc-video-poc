import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["DLIB_USE_CUDA"] = "0"

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import random
import tempfile
import cv2
import numpy as np
import pytesseract
import pdfplumber

import subprocess
import sys

try:
    from deepface import DeepFace
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "deepface==0.0.79"])
    from deepface import DeepFace

from deepface import DeepFace

st.set_page_config(page_title="eKYC Video PoC", layout="centered")
st.markdown("""
<style>
  .stApp { background: #e0e5ec; color: #333; font-family: Aptos, Calibri, sans-serif; }
  .neumorphic-card { background: #e0e5ec; border-radius: 6px;
    box-shadow:8px 8px 16px #a3b1c6,-8px -8px 16px #ffffff;
    padding:1.5rem; margin-bottom:1.5rem; }
  .neumorphic-button button { background:#e0e5ec!important;
    border-radius:50px!important; color:#333!important;
    padding:0.6rem 1.2rem!important;
    box-shadow:4px 4px 8px #a3b1c6,-4px -4px 8px #ffffff!important;
    border:none!important; }
  .neumorphic-button button:active {
    box-shadow: inset 2px 2px 4px #a3b1c6,
                inset -2px -2px 4px #ffffff!important; }
  #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<script>
const observer = new MutationObserver(() => {
  document.querySelectorAll('input').forEach(input => {
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('autocorrect', 'off');
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('spellcheck', 'false');
  });
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("eKYC Solution PoC for AI-based Video-Verification")
st.write("**NOTE**: This PoC does **not** store any Personal Data, ID Info, or Video beyond this session. All uploads are automatically destroyed when you close your browser window.")
st.info("""
**PoC Usage Notice**  \n\n  
• For Protiviti Internal Testing Only. \n\n  
• This demo is meant to be used **only** on laptop with a webcam and modern browser. Recommended: Chrome browser on Protiviti Company-Issued Laptop. \n\n  
• Mobile devices are not supported at this stage.  Future mobile-PWA support can be added based on user demand. \n\n  
• For Suggestions & Feedback Contact vaibhav.shastri@protivitiglobal.in 
""")
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 1: Captcha ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 1: Human Verification")

if "captcha_q" not in st.session_state:
    a, b = random.randint(1, 9), random.randint(1, 9)
    op = random.choice(["+", "-"])
    st.session_state.captcha_q = f"{a} {op} {b}"
    st.session_state.captcha_a = a + b if op == "+" else a - b
    st.session_state.captcha_passed = False

def make_captcha_img(text):
    width, height = 300, 100
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 64)
                break
            except OSError:
                continue
    else:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - w)//2, (height - h)//2), text, font=font, fill=(0,0,0))
    return img.filter(ImageFilter.GaussianBlur(radius=0.5))

captcha_text = st.session_state.captcha_q
img = make_captcha_img(captcha_text)
buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
st.image(buf, caption="🔒 Solve the captcha above to proceed:")

user = st.text_input("Your answer:")
if st.button("Submit Answer"):
    try:
        if int(user.strip()) == st.session_state.captcha_a:
            st.success("✔️ Correct! You may now upload your ID.")
            st.session_state.captcha_passed = True
        else:
            st.error("❌ Incorrect—please refresh to retry.")
    except ValueError:
        st.error("⚠️ Invalid input—please enter a number.")

st.markdown('</div>', unsafe_allow_html=True)

# ── Step 2: Upload ID ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 2: Upload Front of Your Photo ID")

if not st.session_state.get("captcha_passed"):
    st.info("🔒 Solve the captcha above to proceed.")
else:
    uploaded = st.file_uploader("Upload front of your photo ID (JPEG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"])
    if uploaded:
        st.success(f"✅ File received: {uploaded.name}")
        st.info("🔍 Validating…")

        data = uploaded.read()
        if uploaded.type == "application/pdf":
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pil = pdf.pages[0].to_image(resolution=150).original
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        else:
            arr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not cnts:
            st.error("❌ No card detected—please reupload a clear front image.")
        else:
            x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
            card_img = img[y:y+h, x:x+w]
            st.session_state["card_img"] = card_img

            pil_crop = Image.fromarray(card_img)
            text = pytesseract.image_to_string(pil_crop)
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            name = lines[0] if lines else None

            if not name:
                st.error("❌ Could not extract Name—please try a clearer image.")
            else:
                st.success(f"🔍 Detected Name: **{name}**")
                st.session_state["detected_name"] = name
                st.info("✅ ID validated. Next: Live video in Step 3.")

st.markdown('</div>', unsafe_allow_html=True)

# ── Step 3: Upload Video & Match Face ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 3: Video Verification")

if st.session_state.get("captcha_passed") and st.session_state.get("card_img") is not None:
    video_file = st.file_uploader("Upload a short video (5–10 s, MP4/WEBM)", type=["mp4","webm"])
    if video_file:
        tmp_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_vid.write(video_file.read()); tmp_vid.flush()

        cap = cv2.VideoCapture(tmp_vid.name)
        frame = None
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        while True:
            ret, img = cap.read()
            if not ret: break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces):
                frame = img; break
        cap.release()

        if frame is None:
            st.error("❌ No face detected in the video. Please try again.")
        else:
            tmp_id = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp_frame = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            cv2.imwrite(tmp_id.name, st.session_state["card_img"])
            cv2.imwrite(tmp_frame.name, frame)

            res = DeepFace.verify(img_path1=tmp_id.name, img_path2=tmp_frame.name, model_name="Facenet", enforce_detection=False)
            if res.get("verified", False):
                st.success("🟢 Face match successful!")
            else:
                st.error("🔴 Face does not match ID—please retry.")
else:
    st.info("🔒 Complete Steps 1 & 2 first to unlock video verification.")

st.markdown('</div>', unsafe_allow_html=True)
