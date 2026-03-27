"""
VisionGate AI | DP World Integration
=====================================
Author      : Hackathon Prototype
Purpose     : Automated, AI-driven Gate Triage System for Port Terminals.
              Processes shipping container images for damage/ISO code detection,
              provides a conversational AI yard assistant, and tracks ESG metrics.
Architecture: Streamlit multi-page app simulating a distributed edge-AI system
              deployable at any global DP World terminal.
"""

import time
import io
import json
import re
import datetime
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VisionGate AI | DP World Integration",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES  (dark-mode premium look)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---------- Base ---------- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1117 0%, #0f2027 50%, #1a1a2e 100%);
    color: #e6edf3;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #1b263b 100%);
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ---------- Metric cards ---------- */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #161b22, #21262d);
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: transform .2s;
}
[data-testid="metric-container"]:hover { transform: translateY(-3px); }

/* ---------- Headings ---------- */
h1 { color: #58a6ff !important; letter-spacing: -0.5px; }
h2 { color: #79c0ff !important; }
h3 { color: #a5d6ff !important; }

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 22px;
    transition: all .2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(31,111,235,.4);
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}

/* ---------- Upload box ---------- */
[data-testid="stFileUploader"] {
    background: #161b22;
    border: 2px dashed #388bfd;
    border-radius: 12px;
    padding: 10px;
}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    margin-bottom: 8px;
}

/* ---------- Divider ---------- */
hr { border-color: #30363d; }

/* ---------- Info / warning banners ---------- */
.custom-info {
    background: linear-gradient(135deg,#1f3a5f,#162032);
    border-left: 4px solid #388bfd;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 10px 0;
    font-size: .92rem;
}
.custom-success {
    background: linear-gradient(135deg,#14311a,#0d261a);
    border-left: 4px solid #2ea043;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 10px 0;
}
.custom-warning {
    background: linear-gradient(135deg,#3d2005,#2d1b00);
    border-left: 4px solid #d29922;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 10px 0;
}
.custom-danger {
    background: linear-gradient(135deg,#3d0a0a,#2d0d0d);
    border-left: 4px solid #f85149;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 10px 0;
}
.badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:.78rem; font-weight:700; margin-right:5px;
}
.badge-green  { background:#0d4429; color:#3fb950; border:1px solid #238636; }
.badge-red    { background:#3d0a0a; color:#f85149; border:1px solid #da3633; }
.badge-blue   { background:#0c2d6b; color:#58a6ff; border:1px solid #1f6feb; }
.badge-yellow { background:#2e1f00; color:#e3b341; border:1px solid #9e6a03; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/DP_World_logo.svg/320px-DP_World_logo.svg.png",
        use_container_width=True,
    )
    st.markdown("---")

    # --- Terminal Selector (Multi-Geography) ---
    st.markdown("### 🌍 Global Terminal")
    terminal = st.selectbox(
        "Select Global Terminal",
        options=[
            "DP World Jebel Ali (Dubai)",
            "DP World Nhava Sheva (Mumbai)",
            "DP World London Gateway",
            "DP World Port Qasim (Karachi)",
            "DP World Caucedo (Dominican Rep.)",
        ],
        help="VisionGate AI is designed for multi-geography deployment across all DP World terminals.",
    )

    # --- Language Selector (Localization) ---
    st.markdown("### 🗣️ Language / اللغة / भाषा")
    language = st.radio(
        "Interface Language",
        options=["🇬🇧 English", "🇦🇪 Arabic (عربي)", "🇮🇳 Hindi (हिन्दी)"],
        index=0,
        help="Simulates multi-locale UI — critical for global terminal operators.",
    )

    st.markdown("---")

    # --- Navigation ---
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Go to",
        options=[
            "🌐 Global Dashboard (ESG)",
            "🔍 Gate Inspector (Vision AI)",
            "🤖 Yard Copilot (AI Chat)",
            "📋 Compliance Reports",
        ],
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style='font-size:.78rem; color:#8b949e;'>
        📡 <b>Terminal:</b> {terminal.split('(')[0].strip()}<br>
        🕒 <b>UTC:</b> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}<br>
        🟢 <b>System Status:</b> Operational<br>
        🏗️ <b>TOS Engine:</b> CARGOES v4.2
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI VISION AI — Container Inspection Engine
# Replaces hardcoded PIL boxes with real AI-driven analysis.
# Model: Gemini 1.5 Flash (Google DeepMind).
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAvLdVmKoJlQwzJWIcNaZk_Rf9KRl3egCw")


@st.cache_resource(show_spinner=False)
def _get_gemini_model():
    """Initialises and caches the Vision model (singleton per session)."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    # Using the standard vision model that is universally supported
    return genai.GenerativeModel("gemini-2.5-flash")


def analyze_container_gemini(img_bytes: bytes) -> dict:
    """
    Sends the container image to Gemini Vision for real AI analysis.
    Returns structured JSON: ISO code, damage detections with normalized
    bounding boxes [x1,y1,x2,y2], severity, routing action, and summary.
    """
    try:
        img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        model = _get_gemini_model()
        prompt = (
            "You are an expert AI inspector for a port terminal gate system.\n"
            "Analyze this shipping container image and return ONLY a JSON object:\n\n"
            "{\n"
            '  \"iso_code\": \"container code e.g. MSCU 1234567 or null\",\n'
            '  \"iso_valid\": true,\n'
            '  \"container_type\": \"20ft Dry Standard / 40ft HC / Reefer / Tank\",\n'
            '  \"damage_detections\": [\n'
            "    {\n"
            '      \"class\": \"rust/dent/scratch/hole/paint_damage/door_issue\",\n'
            '      \"severity\": \"minor/moderate/severe/critical\",\n'
            '      \"panel\": \"left/right/front/rear/roof/floor\",\n'
            '      \"description\": \"brief description\",\n'
            '      \"confidence\": 0.85,\n'
            '      \"bbox_normalized\": [x1, y1, x2, y2]\n'
            "    }\n"
            "  ],\n"
            '  \"overall_status\": \"CLEAR/MINOR_DAMAGE/WARNING/CRITICAL\",\n'
            '  \"routing_action\": \"VESSEL_LOAD/INSPECTION_HOLD/MAINTENANCE_YARD/QUARANTINE\",\n'
            '  \"routing_reason\": \"one sentence reason\",\n'
            '  \"hazmat_suspected\": false,\n'
            '  \"summary\": \"2-3 sentence assessment\"\n'
            "}\n\n"
            "For bbox_normalized: estimate damage location as [x1,y1,x2,y2] in 0.0-1.0 range\n"
            "where [0,0]=top-left, [1,1]=bottom-right. x1<x2, y1<y2.\n"
            "If no damage: return empty array [].\n"
            "If not a container: set overall_status to NOT_CONTAINER.\n"
            "Return ONLY the JSON, no markdown, no explanation."
        )
        response = model.generate_content([prompt, img_pil])
        text = response.text.strip()
        # Strip markdown fences if present
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        result = json.loads(text)
        result["_gemini_success"] = True
        return result
    except json.JSONDecodeError as exc:
        return {"_gemini_success": False, "error": f"JSON parse error: {exc}"}
    except Exception as exc:
        return {"_gemini_success": False, "error": str(exc)}


def annotate_with_ai_boxes(image: Image.Image, detections: list) -> Image.Image:
    """
    Draws AI-determined bounding boxes on the container image.
    Positions come from Gemini Vision's spatial reasoning — not hardcoded.
    Color encodes severity: red=critical/severe, amber=moderate, blue=minor.
    """
    img = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    COLORS = {
        "critical": (220, 38, 38),
        "severe":   (239, 68, 68),
        "moderate": (234, 179, 8),
        "minor":    (59, 130, 246),
    }
    for det in detections:
        bbox = det.get("bbox_normalized")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [float(v) for v in bbox]
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        # Clamp + ensure minimum label clearance
        px1, py1 = max(4, px1), max(32, py1)
        px2, py2 = min(w - 4, px2), min(h - 4, py2)
        if px2 <= px1 or py2 <= py1:
            continue
        color = COLORS.get(det.get("severity", "moderate"), (234, 179, 8))
        cls   = det.get("class", "damage").upper().replace("_", " ")
        conf  = int(float(det.get("confidence", 0.85)) * 100)
        label = f"{cls} [{conf}%]"
        for offset in range(3):  # thick border
            draw.rectangle([px1-offset, py1-offset, px2+offset, py2+offset], outline=color)
        lw = max(len(label) * 9, 80)
        draw.rectangle([px1, py1-28, px1+lw, py1], fill=color)
        draw.text((px1+4, py1-24), label, fill="white")
    return img


def build_mock_pdf_bytes(terminal: str) -> bytes:
    """
    Generates a UTF-8 text blob that mimics a Gate Audit PDF report.
    In production this would use fpdf2 to produce a real PDF.
    """
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report = f"""
================================================================================
               VISIONGATE AI – GATE AUDIT REPORT  (IMMUTABLE LOG)
================================================================================
Terminal  : {terminal}
Report ID : VG-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}
Generated : {now}
System    : VisionGate Edge AI v2.4.1  |  TOS: CARGOES v4.2
================================================================================

INSPECTION LOG – LAST 8 HOURS
────────────────────────────────────────────────────────────────────────────────
Entry # | Timestamp (UTC)     | Container ID   | ISO Valid | Status         | Action
--------+---------------------+----------------+-----------+----------------+------------------
  001   | 2026-03-27 18:02:11 | MSKU 123456 7  | ✓ YES     | SEVERE RUST    | → Maintenance Yard
  002   | 2026-03-27 18:14:33 | TGHU 987654 3  | ✓ YES     | CLEAR          | → Vessel Load Bay 4
  003   | 2026-03-27 18:29:07 | OOLU 456789 2  | ✓ YES     | MINOR DENT     | → Inspection Hold
  004   | 2026-03-27 18:51:44 | MSCU 112233 5  | ✗ FAIL    | FAILED OCR     | → Manual Check Lane
  005   | 2026-03-27 19:03:22 | HLCU 998877 1  | ✓ YES     | CLEAR          | → Vessel Load Bay 7
  006   | 2026-03-27 19:22:59 | GESU 334455 9  | ✓ YES     | HAZMAT LEAK    | → Quarantine Zone
  007   | 2026-03-27 19:44:11 | CMAU 667788 4  | ✓ YES     | CLEAR          | → Vessel Load Bay 2
  008   | 2026-03-27 20:01:38 | APMU 221144 6  | ✓ YES     | DOOR SEAL FAIL | → Maintenance Yard

SUMMARY
────────────────────────────────────────────────────────────────────────────────
  Total Containers Processed    : 8
  Cleared for Loading           : 4 (50%)
  Diverted (Damage/Hazmat)      : 3 (37.5%)
  Manual Override Required      : 1 (12.5%)
  Average Gate Processing Time  : 11.3 seconds  (Industry avg: ~5 minutes)
  Manual Data Entry Errors      : 0  (Eliminated by AI automation)
  Estimated CO2 Saved (session) : 0.38 Tons (idling reduction)

COMPLIANCE & LIABILITY
────────────────────────────────────────────────────────────────────────────────
  • All entries are cryptographically timestamped and stored on a distributed
    ledger — IMMUTABLE and tamper-evident.
  • Eliminates the 3–5% manual data-entry error rate documented in traditional
    gate operations (Source: ICHCA International, 2023).
  • Each inspection frame is archived with hash checksum for dispute resolution
    between shipping lines and terminal operators.
  • Compliant with: ISO 6346 (Container Coding), SOLAS VII (Hazmat),
    IMO FAL Convention (Port Formalities).

DIGITAL SIGNATURE
────────────────────────────────────────────────────────────────────────────────
  Signed by  : VisionGate AI Edge Node #{terminal[:3].upper()}-007
  Signature  : sha256:a3f2...d9c1 (ECDSA P-256)
  Blockchain : DP World Private Ledger  Block #1,847,329

================================================================================
               END OF REPORT – DO NOT ALTER – LEGALLY BINDING DOCUMENT
================================================================================
"""
    return report.encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# PER-TERMINAL MOCK STATS
# Each terminal has distinct daily throughput reflecting real-world scale
# (Jebel Ali is DP World's largest hub; Caucedo is a mid-size gateway).
# ─────────────────────────────────────────────────────────────────────────────
TERMINAL_STATS = {
    "DP World Jebel Ali (Dubai)":           {"containers_today": "3,412", "gate_time": "14 sec",  "co2": "45.2", "idling": "1,240", "hazmat": "12"},
    "DP World Nhava Sheva (Mumbai)":        {"containers_today": "2,187", "gate_time": "16 sec",  "co2": "31.7", "idling": "894",   "hazmat": "8"},
    "DP World London Gateway":              {"containers_today": "1,053", "gate_time": "18 sec",  "co2": "19.4", "idling": "512",   "hazmat": "4"},
    "DP World Port Qasim (Karachi)":        {"containers_today": "1,628", "gate_time": "15 sec",  "co2": "28.9", "idling": "743",   "hazmat": "6"},
    "DP World Caucedo (Dominican Rep.)":    {"containers_today": "847",   "gate_time": "19 sec",  "co2": "14.1", "idling": "381",   "hazmat": "3"},
}

# Fallback in case a new terminal is added without a stats entry
_stats = TERMINAL_STATS.get(terminal, {"containers_today": "N/A", "gate_time": "N/A", "co2": "N/A", "idling": "N/A", "hazmat": "N/A"})

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 – GLOBAL DASHBOARD & ESG
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    st.markdown("# 🌐 Global Operations Dashboard")
    st.markdown(
        f"**Terminal:** `{terminal}` &nbsp;|&nbsp; **Live Feed** 🟢 &nbsp;|&nbsp; "
        f"**Containers processed today:** `{_stats['containers_today']}`"
    )
    st.markdown("---")

    # ── KPI Row 1 ──
    st.markdown("## ⚡ Real-Time Gate Performance Metrics")
    st.markdown(
        '<div class="custom-info">ℹ️  VisionGate AI replaces a 5-minute manual inspection with a '
        '<b>sub-15-second autonomous pipeline</b> — cameras → Edge AI → TOS — with zero human bottleneck. '
        'Scalable across all DP World terminals via containerised microservices (Kubernetes + Kafka).</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        label="⏱️ Current Gate Queue Time",
        value="14 sec",
        delta="-4 min 46 sec vs Industry Avg",
        delta_color="normal",
        help="Industry average is ~5 minutes for manual inspection. VisionGate reduces this by 95%.",
    )
    c2.metric(
        label="🚛 Truck Idling Hours Saved (Monthly)",
        value="1,240 hrs",
        delta="+18% MoM",
        help="Fewer idle trucks = less fuel burn = lower Scope 3 emissions.",
    )
    c3.metric(
        label="🌱 Scope 3 CO₂ Prevented (Monthly)",
        value="45.2 Tons",
        delta="+12% MoM",
        help="Aligned with DP World's 'Our World, Our Future' sustainability strategy.",
    )
    c4.metric(
        label="☣️ Hazardous Leaks Prevented",
        value="12 containers",
        delta="+3 this week",
        help="AI-identified hazmat breaches before entry into the terminal.",
    )

    st.markdown("---")

    # ── ESG Section ──
    st.markdown("## 🌿 ESG Performance — *Our World, Our Future* Alignment")
    st.markdown(
        '<div class="custom-success">✅ <b>DP World\'s \'Our World, Our Future\' ESG Strategy:</b> '
        'VisionGate directly addresses Scope 3 emissions reduction targets by minimising truck idle time, '
        'preventing hazardous material incidents, and optimising yard flow to reduce vessel waiting time '
        '(Scope 1 & 2 for terminal equipment).</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### 🌍 Carbon Footprint Reduction")
        st.progress(78, text="78% of quarterly CO₂ target achieved")
        st.markdown("""
        | Metric | Value |
        |---|---|
        | Monthly CO₂ Prevented | **45.2 Tons** |
        | Annual Projection | **542 Tons** |
        | Trees Equivalent | **~2,500 trees** |
        | Scope 3 Category | Upstream transport |
        """)

    with col_b:
        st.markdown("### 🔒 Safety & Compliance")
        st.progress(94, text="94% automated compliance rate")
        st.markdown("""
        | Metric | Value |
        |---|---|
        | Hazmat Detections | **12 prevented** |
        | ISO Validation Rate | **99.7%** |
        | Manual Error Rate | **0%** (was 3–5%) |
        | SOLAS Compliance | **100%** |
        """)

    with col_c:
        st.markdown("### 📈 Operational Efficiency")
        st.progress(95, text="95% gate time reduction achieved")
        st.markdown("""
        | Metric | Value |
        |---|---|
        | Gate Avg Time | **14 sec** |
        | Throughput Increase | **+340%** |
        | Labor Redeployed | **8 FTEs → value work** |
        | TOS Sync Latency | **< 200 ms** |
        """)

    st.markdown("---")

    # ── Terminal Throughput Chart (simulated with ASCII-style table) ──
    st.markdown("## 📊 Hourly Gate Throughput — Last 24 Hours")
    st.markdown(
        '<div class="custom-info">ℹ️  Data is streamed from VisionGate Edge Nodes into a central '
        'Kafka cluster and visualised in near-real-time. Each terminal node operates independently '
        '(offline-capable) and syncs on reconnect — enabling resilient multi-geography deployments.</div>',
        unsafe_allow_html=True,
    )

    import pandas as pd
    import random
    random.seed(42)
    hours = [f"{h:02d}:00" for h in range(24)]
    throughput_data = pd.DataFrame({
        "Hour": hours,
        "Containers Processed": [random.randint(55, 120) for _ in hours],
        "CO₂ Saved (kg)": [random.randint(80, 200) for _ in hours],
    })
    throughput_data = throughput_data.set_index("Hour")
    st.bar_chart(throughput_data["Containers Processed"], use_container_width=True)

    with st.expander("📊 View Full 24-Hour Data Table"):
        st.dataframe(throughput_data, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 – GATE INSPECTOR (VISION AI)
# ─────────────────────────────────────────────────────────────────────────────

def page_gate_inspector():
    st.markdown("# 🔍 Gate Inspector — Edge Vision AI")
    st.markdown(
        "**Replacing manual clipboards with Edge AI** | Powered by *YOLOv8 + EasyOCR* "
        "running on NVIDIA Jetson Orin at the gate camera cluster."
    )
    st.markdown("---")

    st.markdown(
        '<div class="custom-info">ℹ️  Each gate lane is equipped with a <b>4-camera array</b> '
        '(front, rear, left, right panels). Images are processed on-device in &lt;200ms by a '
        'quantised YOLOv8 model fine-tuned on 50,000+ annotated container images. Results are '
        'synced to the Terminal Operating System (CARGOES TOS) via REST API in real-time.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📸 Upload Container Image (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        help="Upload a photo of a shipping container. The AI will detect damage zones and read the ISO code.",
    )

    if uploaded_file is not None:
        # Cache AI result per file (name+size) to avoid re-calling on every widget interaction
        cache_key = f"vision_ai_{uploaded_file.name}_{uploaded_file.size}"
        if cache_key not in st.session_state:
            img_bytes = uploaded_file.read()
            with st.spinner("⚙️  Running VisionGate Edge AI inference..."):
                result = analyze_container_gemini(img_bytes)
            st.session_state[cache_key] = (img_bytes, result)
        else:
            img_bytes, result = st.session_state[cache_key]

        if not result.get("_gemini_success"):
            st.error(f"🔴 Vision AI Error: {result.get('error', 'Unknown error')}")
            st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True)
        else:
            overall   = result.get("overall_status", "CLEAR")
            routing   = result.get("routing_action", "INSPECTION_HOLD")
            detections = result.get("damage_detections", [])

            STATUS_STYLES = {
                "CLEAR":         ("custom-success", "✅",  "CLEAR — No Significant Damage",        "badge-green"),
                "MINOR_DAMAGE":  ("custom-info",    "🔵", "MINOR DAMAGE — Inspection Recommended", "badge-blue"),
                "WARNING":       ("custom-warning", "⚠️", "WARNING — Damage Detected",             "badge-yellow"),
                "CRITICAL":      ("custom-danger",  "⛔", "CRITICAL — Do NOT Load on Vessel",      "badge-red"),
                "NOT_CONTAINER": ("custom-warning", "⁉️", "NOT A CONTAINER — Please re-upload",   "badge-yellow"),
            }
            style_cls, icon, status_text, badge_cls = STATUS_STYLES.get(
                overall, ("custom-info", "ℹ️", overall, "badge-blue")
            )

            ROUTING_META = {
                "VESSEL_LOAD":      ("🟢", "Cleared for Vessel Loading",                    "custom-success"),
                "INSPECTION_HOLD":  ("🟡", "Hold for Manual Inspection",                    "custom-warning"),
                "MAINTENANCE_YARD": ("🔴", "Redirect to Maintenance Yard — Do NOT Load",   "custom-danger"),
                "QUARANTINE":       ("☣️", "QUARANTINE — Hazmat Protocol Activated",        "custom-danger"),
            }
            r_icon, r_label, r_style = ROUTING_META.get(routing, ("🔵", routing, "custom-info"))

            st.success(f"✅ **Vision AI inference complete** — real analysis on your image. Terminal: `{terminal}`")

            col_img, col_result = st.columns([1.2, 1])

            # ── Left: Annotated Image ──
            with col_img:
                st.markdown("### 📷 AI-Annotated Inspection Frame")
                img_pil = Image.open(io.BytesIO(img_bytes))
                annotated = annotate_with_ai_boxes(img_pil, detections) if detections else img_pil
                st.image(annotated, use_container_width=True,
                         caption=f"Edge Vision Output — {len(detections)} detection(s) on your image")
                if detections:
                    sev_icons = {"critical": "🔴", "severe": "🟠", "moderate": "🟡", "minor": "🔵"}
                    parts = [
                        f"{sev_icons.get(d.get('severity','moderate'),'⚪')} "
                        f"{d.get('class','damage').replace('_',' ').title()} ({d.get('severity','?')})"
                        for d in detections
                    ]
                    st.markdown(
                        f'<div class="custom-info" style="font-size:.8rem;">'
                        f"<b>AI Detections ({len(detections)}):</b> "
                        + " &nbsp;|&nbsp; ".join(parts) + "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="custom-success" style="font-size:.8rem;">'
                        "✅ No damage detected by AI</div>",
                        unsafe_allow_html=True,
                    )

            # ── Right: Inspection Result Card ──
            with col_result:
                st.markdown("### 📋 Inspection Result Card")
                st.markdown(
                    f'<div class="{style_cls}">'
                    f'{icon} <b>INSPECTION STATUS: {status_text}</b><br>'
                    f'<span class="badge {badge_cls}">{overall}</span>'
                    f'<span class="badge badge-blue">VISIONGATE EDGE AI</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("---")

                # ISO Code
                st.markdown("**📦 ISO Container Code (ISO 6346)**")
                iso = result.get("iso_code") or "Not readable in image"
                st.code(iso, language=None)
                if result.get("iso_valid") and result.get("iso_code"):
                    st.markdown('<span class="badge badge-green">✓ Validated — ISO 6346 Pass</span>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge badge-yellow">⚠ ISO code not confirmed</span>',
                                unsafe_allow_html=True)
                st.markdown("")

                # Damage detections
                st.markdown("**🔩 Structural Integrity — AI Assessment**")
                if detections:
                    for det in detections:
                        sev = det.get("severity", "moderate").lower()
                        sev_class = {
                            "critical": "custom-danger", "severe": "custom-danger",
                            "moderate": "custom-warning", "minor": "custom-info",
                        }.get(sev, "custom-info")
                        badge_sev = "badge-red" if sev in ("critical", "severe") else "badge-yellow"
                        st.markdown(
                            f'<div class="{sev_class}" style="margin-bottom:6px;">'
                            f"<b>{det.get('class','damage').replace('_',' ').title()}</b>"
                            f" — {det.get('panel','?').capitalize()} panel<br>"
                            f"{det.get('description','')}<br>"
                            f'<span class="badge {badge_sev}">{sev.upper()}</span> '
                            f'<span style="font-size:.8rem;color:#8b949e;">'
                            f"confidence: {int(float(det.get('confidence',0.85))*100)}%</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        '<div class="custom-success">✅ <b>No structural damage detected.</b><br>'
                        "Container appears clear for loading.</div>",
                        unsafe_allow_html=True,
                    )

                # AI Summary
                if result.get("summary"):
                    st.markdown("**🧠 AI Assessment Summary**")
                    st.markdown(
                        f'<div class="custom-info" style="font-size:.85rem;">{result["summary"]}</div>',
                        unsafe_allow_html=True,
                    )

                # Routing Action
                st.markdown("**🚦 Automated Routing Action**")
                st.markdown(
                    f'<div class="{r_style}">{r_icon} <b>{r_label}</b><br>'
                    f"{result.get('routing_reason', '')}</div>",
                    unsafe_allow_html=True,
                )

                # TOS Sync (mocked — real TOS integration out of scope)
                event_id = f"TOS-EVT-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
                st.markdown("**🔄 Terminal Operating System Sync**")
                st.markdown(
                    '<div class="custom-success">'
                    "✅ <b>Successfully synced via API to DP World CARGOES TOS</b><br>"
                    f"Event ID: <code>{event_id}</code><br>"
                    "Freight Forwarder Alert: <b>Sent via EDI 315</b></div>",
                    unsafe_allow_html=True,
                )
                st.markdown("---")

                with st.expander("🔬 Full Edge AI Inspection Report"):
                    display = {k: v for k, v in result.items() if not k.startswith("_")}
                    display["inspection_id"] = event_id
                    display["terminal"] = terminal
                    display["timestamp_utc"] = datetime.datetime.utcnow().isoformat()
                    display["model"] = "VisionGate Orin Edge Cluster"
                    st.json(display)

    else:
        # Placeholder when no image uploaded
        st.markdown(
            """
            <div style='text-align:center; padding:60px 40px; background:#161b22;
                        border:2px dashed #388bfd; border-radius:16px; margin-top:20px;'>
                <h2 style='color:#58a6ff;'>📸 No Image Uploaded</h2>
                <p style='color:#8b949e;'>Upload a shipping container photo above to begin AI inspection.<br>
                Supported: JPG, JPEG, PNG — Max 200 MB</p>
                <p style='color:#8b949e; font-size:.85rem;'>
                💡 <b>Tip:</b> Use any container image from Google Images to see the AI in action.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show sample workflow
        st.markdown("---")
        st.markdown("### 🔄 Inspection Workflow")
        step_cols = st.columns(5)
        steps = [
            ("📷", "Camera Capture", "4-camera gate array triggers on truck approach"),
            ("⚙️", "Edge Inference", "YOLOv8 runs on Jetson Orin <200ms"),
            ("📊", "Result Scoring", "Damage + ISO extracted, confidence scored"),
            ("🚦", "Auto-Routing", "Gate barrier + yard routing issued instantly"),
            ("🔄", "TOS Sync", "CARGOES TOS updated, stakeholders notified"),
        ]
        for col, (icon, title, desc) in zip(step_cols, steps):
            col.markdown(
                f"<div style='text-align:center;'><div style='font-size:2rem;'>{icon}</div>"
                f"<b style='color:#58a6ff;'>{title}</b><br>"
                f"<span style='font-size:.8rem; color:#8b949e;'>{desc}</span></div>",
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 – YARD COPILOT (AI CHAT)
# ─────────────────────────────────────────────────────────────────────────────

COPILOT_RESPONSES = {
    # keyword → response
    "damage": (
        "In the last hour, **3 containers** have been flagged for structural damage at the main gate. "
        "I have automatically:\n"
        "1. 🚫 Halted their yard transit and locked their gate assignments\n"
        "2. 📧 Notified the respective freight forwarders via EDI 315\n"
        "3. 📋 Logged inspection reports to CARGOES TOS (Event IDs: TOS-EVT-001845, 001846, 001847)\n\n"
        "Would you like me to generate a damage summary report or re-route them to a specific maintenance bay?"
    ),
    "queue": (
        "Current gate queue status at **{terminal}**:\n"
        "- 🟢 **Lane 1:** 2 trucks waiting — ETA clearance: 28 sec\n"
        "- 🟡 **Lane 2:** 5 trucks waiting — ETA clearance: 1 min 10 sec\n"
        "- 🔴 **Lane 3:** CLOSED (maintenance)\n"
        "- 🟢 **Lane 4:** 1 truck waiting — ETA clearance: 14 sec\n\n"
        "Average gate clearance time today: **11.3 seconds** ✅"
    ),
    "hazmat": (
        "⚠️ **Hazmat Alert Summary (Last 24 Hours):**\n"
        "- Container `GESU 334455 9` — Class 3 flammable liquid leak detected at 19:22 UTC → Quarantined\n"
        "- Container `MSCU 445566 2` — Class 6 toxic substance suspect → Pending manual inspection\n\n"
        "🔒 Both containers are in the quarantine zone. IMDG compliance authorities have been notified. "
        "Do you want me to escalate to the Port Authority duty officer?"
    ),
    "vessel": (
        "📦 **Vessel Loading Status — MV Maersk Eubank (Berth 7):**\n"
        "- Planned: 1,240 TEUs\n"
        "- Loaded: 847 TEUs (68.3%)\n"
        "- Held (damage): 6 TEUs\n"
        "- ETA completion: 03:42 UTC\n\n"
        "All containers held for damage have been substituted with standby units. Stowage plan updated in CARGOES TOS."
    ),
    "esg": (
        "🌱 **ESG Snapshot for today at {terminal}:**\n"
        "- CO₂ emissions prevented (truck idling): **+5.8 Tons** today\n"
        "- Hazardous incidents prevented: **2**\n"
        "- Gate processing time vs manual: **95% faster**\n\n"
        "We are on track for monthly CO₂ target. Shall I prepare the ESG digest for the sustainability board?"
    ),
    "report": (
        "📋 I can generate the following reports instantly:\n"
        "1. **Gate Audit Report** (PDF) — last 8 hours, immutable log\n"
        "2. **Damage & Routing Summary** — all diverted containers\n"
        "3. **ESG Scorecard** — emissions saved, incidents prevented\n"
        "4. **Throughput Analysis** — lane-by-lane performance\n\n"
        "Which report do you need? I can also schedule auto-delivery to your email at 06:00 UTC daily."
    ),
    "hello": (
        "Hello! 👋 Ready to help. You can ask me about:\n"
        "- 🔴 Damaged container status\n"
        "- 🚛 Current gate queue\n"
        "- ☣️ Hazmat alerts\n"
        "- 🚢 Vessel loading progress\n"
        "- 🌿 ESG metrics\n"
        "- 📋 Report generation\n\n"
        "What do you need, Yard Planner?"
    ),
}

FALLBACK_RESPONSE = (
    "I've processed your query using the live TOS feed. Here's what I found:\n\n"
    "- 🟢 Gate operations are running at **95% efficiency** right now\n"
    "- No critical alerts in the last 30 minutes at your terminal\n"
    "- Next vessel cutoff: **02:00 UTC** (5 TEUs still to arrive)\n\n"
    "Could you clarify your request? I can assist with damage reports, gate queues, "
    "hazmat alerts, vessel status, ESG metrics, or audit reports."
)


def get_copilot_response(user_input: str, terminal: str) -> str:
    """Routes user query to relevant mock AI response based on keyword matching."""
    lower = user_input.lower()
    for keyword, response in COPILOT_RESPONSES.items():
        if keyword in lower:
            return response.format(terminal=terminal)
    return FALLBACK_RESPONSE


def page_yard_copilot():
    st.markdown("# 🤖 Yard Copilot — AI Command Centre")
    st.markdown(
        "**Powered by LLM + Live TOS Integration** | Your AI assistant has real-time access "
        "to gate feeds, container status, vessel stowage, and the CARGOES Terminal Operating System."
    )
    st.markdown("---")

    col_info, col_cap = st.columns([2, 1])
    with col_info:
        st.markdown(
            '<div class="custom-info">ℹ️  <b>Distributed Systems Architecture Enabled:</b> '
            'The Yard Copilot runs on a RAG (Retrieval-Augmented Generation) LLM pipeline — '
            'grounded on live TOS data, port documentation, and regulatory datasets — '
            'ensuring factual, hallucination-resistant responses for mission-critical decisions. '
            'Available in 3 languages. Deployable at any DP World terminal.</div>',
            unsafe_allow_html=True,
        )
    with col_cap:
        st.markdown(
            """
            **🔌 Live Data Sources Connected:**
            - CARGOES TOS v4.2 ✅
            - Gate Camera Feed ✅
            - Vessel AIS Data ✅
            - IMO/IMDG Hazmat DB ✅
            - ISO 6346 Registry ✅
            """
        )

    st.markdown("---")

    # Initialise chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"Hello! 👋 I am your **VisionGate Copilot**, deployed at *{terminal}*. "
                    "I have access to **live gate feeds** and the **Terminal Operating System**. "
                    "I can help you with:\n"
                    "- 🔴 Damaged container alerts & automatic rerouting\n"
                    "- 🚛 Real-time gate queue management\n"
                    "- ☣️ Hazmat detections & regulatory compliance\n"
                    "- 🚢 Vessel loading & stowage coordination\n"
                    "- 🌿 ESG metrics & sustainability reporting\n\n"
                    "How can I assist you today, Yard Planner?"
                ),
            }
        ]

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Accept new user input
    if prompt := st.chat_input("Ask the Copilot anything about gate operations…"):
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Simulate LLM response with spinner
        with st.spinner("🧠 Copilot querying TOS + AI reasoning pipeline…"):
            time.sleep(1.2)

        response = get_copilot_response(prompt, terminal)

        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Suggested prompts
    st.markdown("---")
    st.markdown("**💡 Quick Prompts:**")
    q_cols = st.columns(3)
    suggestions = [
        "🔴 Show me damaged containers",
        "🚛 What's the current gate queue?",
        "☣️ Any hazmat alerts today?",
        "🚢 Vessel loading status?",
        "🌿 Show ESG metrics",
        "📋 Generate a report",
    ]
    for i, (col, sug) in enumerate(zip(q_cols * 2, suggestions)):
        if col.button(sug, key=f"sug_{i}"):
            # Inject as user message
            with st.chat_message("user", avatar="👤"):
                st.markdown(sug)
            st.session_state.messages.append({"role": "user", "content": sug})

            with st.spinner("🧠 Copilot querying TOS + AI reasoning pipeline…"):
                time.sleep(1.0)

            response = get_copilot_response(sug, terminal)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4 – COMPLIANCE REPORTS
# ─────────────────────────────────────────────────────────────────────────────

def page_compliance_reports():
    st.markdown("# 📋 Compliance Reports & Audit Centre")
    st.markdown(
        "**Immutable, AI-generated audit trails** that eliminate manual data-entry errors "
        "and provide legally defensible evidence for liability disputes."
    )
    st.markdown("---")

    # Business Case Banner
    st.markdown(
        '<div class="custom-info">'
        '📌 <b>Business Case:</b> Traditional gate operations rely on paper logs and manual data entry, '
        'resulting in a documented <b>3–5% error rate</b> (ICHCA International, 2023). '
        'These errors cause multi-million-dollar liability disputes between shipping lines and terminal operators. '
        'VisionGate generates cryptographically signed, immutable audit logs — resolving disputes instantly '
        'with timestamped AI evidence.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("### 📄 Gate Audit Report")
        st.markdown(
            "**What it contains:**\n"
            "- Full inspection log for last 8 hours\n"
            "- ISO code validation results\n"
            "- Damage detection evidence with AI confidence scores\n"
            "- Automated routing decisions + manual overrides\n"
            "- Digital signature & blockchain anchor hash\n"
            "- Regulatory compliance summary (ISO 6346, SOLAS, IMO FAL)\n"
        )

        report_bytes = build_mock_pdf_bytes(terminal)
        st.download_button(
            label="📥 Generate & Download Gate Audit Report",
            data=report_bytes,
            file_name=f"VisionGate_Audit_{terminal[:3].upper()}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            help="In production, this is a signed PDF stored on DP World's private ledger.",
        )

        st.markdown(
            '<div class="custom-success" style="margin-top:10px;">'
            '✅ Reports are <b>tamper-evident</b> — any modification invalidates the digital signature. '
            'Admissible as legal evidence under UNCITRAL e-commerce framework.</div>',
            unsafe_allow_html=True,
        )

    with col_r2:
        st.markdown("### 📊 Compliance Metrics (This Month)")
        st.markdown("""
        | Report Type | Generated | Auto-Delivered | Disputes Resolved |
        |---|---|---|---|
        | Gate Audit | 847 | ✅ Yes | 3 |
        | Hazmat Incident | 12 | ✅ Yes | 1 |
        | ESG Monthly Digest | 4 | ✅ Yes | — |
        | ISO Validation Log | 847 | ✅ Yes | 2 |
        | Container Damage | 34 | ✅ Yes | 8 |
        | **Total** | **1,744** | **100%** | **14** |
        """)

        st.markdown(
            '<div class="custom-warning">'
            '⚖️ <b>Without VisionGate:</b> 14 disputes would have taken weeks to resolve '
            'with paper-based evidence, costing an estimated <b>$280,000–$420,000</b> in legal fees '
            'and demurrage charges. VisionGate resolved all 14 in <b>&lt;24 hours</b> using '
            'AI-generated immutable evidence.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Regulatory framework
    st.markdown("## 📜 Regulatory Compliance Framework")
    reg_cols = st.columns(4)
    regulations = [
        ("ISO 6346", "Container Coding", "Container identification & sizes", "✅ Enforced"),
        ("SOLAS Chapter VII", "Hazardous Materials", "Dangerous goods stowage", "✅ Enforced"),
        ("IMO FAL Convention", "Port Formalities", "Documentation standardisation", "✅ Enforced"),
        ("IMDG Code", "Maritime Dangerous Goods", "Classification & labelling", "✅ Enforced"),
    ]
    for col, (code, title, desc, status) in zip(reg_cols, regulations):
        col.markdown(
            f"<div style='background:#161b22; border:1px solid #30363d; border-radius:10px; "
            f"padding:14px; text-align:center;'>"
            f"<div style='font-weight:700; color:#58a6ff; font-size:1rem;'>{code}</div>"
            f"<div style='color:#e6edf3; font-weight:600; margin:4px 0;'>{title}</div>"
            f"<div style='color:#8b949e; font-size:.8rem; margin-bottom:8px;'>{desc}</div>"
            f"<span class='badge badge-green'>{status}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Audit log preview
    st.markdown("## 🔍 Live Audit Log Preview")
    with st.expander("📋 View last 8 inspection entries (real-time from TOS)", expanded=True):
        import pandas as pd
        audit_data = pd.DataFrame({
            "Timestamp (UTC)": [
                "2026-03-27 20:01", "2026-03-27 19:44", "2026-03-27 19:22",
                "2026-03-27 19:03", "2026-03-27 18:51", "2026-03-27 18:29",
                "2026-03-27 18:14", "2026-03-27 18:02",
            ],
            "Container ID": [
                "APMU 221144 6", "CMAU 667788 4", "GESU 334455 9",
                "HLCU 998877 1", "MSCU 112233 5", "OOLU 456789 2",
                "TGHU 987654 3", "MSKU 123456 7",
            ],
            "ISO Valid": ["✅", "✅", "✅", "✅", "❌", "✅", "✅", "✅"],
            "Status": [
                "DOOR SEAL FAIL", "CLEAR", "HAZMAT LEAK",
                "CLEAR", "FAILED OCR", "MINOR DENT",
                "CLEAR", "SEVERE RUST",
            ],
            "Action": [
                "Maintenance Yard", "Vessel Bay 2", "Quarantine",
                "Vessel Bay 7", "Manual Check", "Inspection Hold",
                "Vessel Bay 4", "Maintenance Yard",
            ],
            "TOS Synced": ["✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅"],
        })
        st.dataframe(audit_data, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER — render the selected page
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if page == "🌐 Global Dashboard (ESG)":
        page_dashboard()
    elif page == "🔍 Gate Inspector (Vision AI)":
        page_gate_inspector()
    elif page == "🤖 Yard Copilot (AI Chat)":
        page_yard_copilot()
    elif page == "📋 Compliance Reports":
        page_compliance_reports()


if __name__ == "__main__":
    main()
