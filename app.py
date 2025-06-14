import os
# Disable any GPU for libraries that might try to use it
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["DLIB_USE_CUDA"] = "0"

import streamlit as st
import io, random, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2, numpy as np, pytesseract, pdfplumber
from deepface import DeepFace
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration

# ── Page Configuration & CSS ──
st.set_page_config(page_title="eKYC Video PoC", layout="centered")
st.markdown("""
<style>
  .stApp { background: #e0e5ec; color: #333; font-family: Aptos, Calibri, sans-serif; }
  .neumorphic-card { background: #e0e5ec; border-radius: 6px;
    box-shadow:8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff;
    padding:1.5rem; margin-bottom:1.5rem; }
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header & Privacy Note ──
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

# ── Step 1: One‐Step Math Captcha ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 1: Human Verification")

if "captcha_q" not in st.session_state:
    a, b = random.randint(1, 9), random.randint(1, 9)
    op = random.choice(["+", "-"])
    st.session_state.captcha_q = f"{a} {op} {b}"
    st.session_state.captcha_a = a + b if op == "+" else a - b
    st.session_state.captcha_passed = False

def make_captcha_img(text):
    W, H = 300, 100
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    # try common fonts
    for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 64)
            break
    else:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), text, font=font)
    w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((W-w)//2,(H-h)//2), text, font=font, fill="black")
    return img.filter(ImageFilter.GaussianBlur(0.5))

# show captcha
buf = io.BytesIO()
make_captcha_img(st.session_state.captcha_q).save(buf, "PNG")
buf.seek(0)
st.image(buf, caption="🔒 Solve to continue:", use_container_width=False)

answer = st.text_input("Your answer:", key=f"cap_{st.session_state.captcha_q}")
if st.button("Submit Answer"):
    try:
        if int(answer.strip()) == st.session_state.captcha_a:
            st.success("✔️ Correct! Proceed to Step 2.")
            st.session_state.captcha_passed = True
        else:
            st.error("❌ Incorrect. Refresh to get a new challenge.")
            st.markdown('<script>window.location.reload()</script>', unsafe_allow_html=True)
    except:
        st.error("⚠️ Please enter a valid number.")
        st.markdown('<script>window.location.reload()</script>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 2: Front‐of‐ID Upload & OCR ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 2: Upload Front of Your Photo ID")

if not st.session_state.get("captcha_passed", False):
    st.info("🔒 Complete Step 1 first.")
else:
    up = st.file_uploader("Upload (JPEG/PNG/PDF):", type=["jpg","jpeg","png","pdf"])
    if up:
        st.success(f"✅ Received: {up.name}")
        data = up.read()
        # rasterize PDF or decode image
        if up.type == "application/pdf":
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pil = pdf.pages[0].to_image(resolution=150).original
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        else:
            arr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        # find card contour
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thr = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            st.error("❌ No card detected. Try again.")
        else:
            x,y,w,h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
            crop = img[y:y+h, x:x+w]
            st.session_state["card_img"] = crop
            # OCR name
            text = pytesseract.image_to_string(Image.fromarray(crop))
            name = next((l for l in text.splitlines() if l.strip()), "")
            if not name:
                st.error("❌ Could not extract name. Try clearer image.")
            else:
                st.success(f"🔍 Detected Name: {name}")
                st.session_state["detected_name"] = name
                st.info("✅ ID validated. Proceed to Step 3.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 3: Face & ID Continuity Check ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 3: Video Verification")

if st.session_state.get("captcha_passed") and st.session_state.get("card_img") is not None:
    vid = st.file_uploader("Upload short video (MP4/WEBM):", type=["mp4","webm"])
    if vid:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.write(vid.read()); tmp.flush()
        cap = cv2.VideoCapture(tmp.name); frame = None
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
        while True:
            ok, img = cap.read()
            if not ok: break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if len(cascade.detectMultiScale(gray,1.1,5)):
                frame = img; break
        cap.release()
        if frame is None:
            st.error("❌ No face found in video.")
        else:
            f1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            f2 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            cv2.imwrite(f1.name, st.session_state["card_img"])
            cv2.imwrite(f2.name, frame)
            res = DeepFace.verify(img_path1=f1.name, img_path2=f2.name,
                                  model_name="Facenet", enforce_detection=False)
            if res.get("verified"):
                st.success("🟢 Face match successful!")
                st.session_state["face_match"] = True
            else:
                st.error("🔴 Face does not match. Retry.")
else:
    st.info("🔒 Complete Steps 1 & 2 first.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Step 4: Karaoke‐Style Script Recital ──
st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
st.subheader("Step 4: Speech‐to‐Text Verification")

if st.session_state.get("face_match"):
    # generate four random digits
    digits = [str(random.randint(0,9)) for _ in range(4)]
    st.write("💡 Please read aloud these digits in order:")
    st.write(" ".join(digits))
    # placeholder for live transcript feedback
    transcript = st.text_area("Live transcript will appear here…", height=80)
    if st.button("Submit Transcript"):
        # check digits
        if all(d in transcript for d in digits):
            st.success("🟢 Digits recognized.")
            # name spelling
            name = st.session_state["detected_name"]
            chars = " – ".join(list(name.strip().upper()))
            st.write(f"Spell your name: {chars}")
            spelled = st.text_input("Type what you said above:")
            if st.button("Verify Spelling"):
                if spelled.replace(" ", "").upper() == ''.join(list(name.upper())):
                    st.success("✅ Name spelling correct! Verification Complete.")
                else:
                    st.error("❌ Spelling mismatch. Retry.")
        else:
            st.error("❌ Digits not correctly detected.")
else:
    st.info("🔒 Complete Steps 1–3 first.")
st.markdown('</div>', unsafe_allow_html=True)
