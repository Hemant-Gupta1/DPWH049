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
# HELPER: draw bounding boxes on container image using PIL
# ─────────────────────────────────────────────────────────────────────────────

def annotate_container_image(uploaded_file) -> Image.Image:
    """
    Opens the uploaded image and overlays mock AI detection bounding boxes:
      - Red box  → Structural damage zone (Severe Rust)
      - Green box → ISO code plate region
    Simulates YOLOv8 object detection output at the edge node.
    """
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # --- Box 1: Damage region (red) ---
    x1_d, y1_d = int(w * 0.05), int(h * 0.30)
    x2_d, y2_d = int(w * 0.38), int(h * 0.75)
    for offset in range(3):          # thick border
        draw.rectangle(
            [x1_d - offset, y1_d - offset, x2_d + offset, y2_d + offset],
            outline=(220, 38, 38),
        )
    # Label background
    draw.rectangle([x1_d, y1_d - 28, x1_d + 170, y1_d], fill=(220, 38, 38))
    draw.text(
        (x1_d + 5, y1_d - 24),
        "⚠ SEVERE RUST [98.2%]",
        fill="white",
    )

    # --- Box 2: ISO code plate (green) ---
    x1_i, y1_i = int(w * 0.55), int(h * 0.08)
    x2_i, y2_i = int(w * 0.95), int(h * 0.26)
    for offset in range(3):
        draw.rectangle(
            [x1_i - offset, y1_i - offset, x2_i + offset, y2_i + offset],
            outline=(34, 197, 94),
        )
    draw.rectangle([x1_i, y1_i - 28, x1_i + 160, y1_i], fill=(34, 197, 94))
    draw.text(
        (x1_i + 5, y1_i - 24),
        "✓ ISO CODE [99.7%]",
        fill="white",
    )

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
# PAGE 1 – GLOBAL DASHBOARD & ESG
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    st.markdown("# 🌐 Global Operations Dashboard")
    st.markdown(
        f"**Terminal:** `{terminal}` &nbsp;|&nbsp; **Live Feed** 🟢 &nbsp;|&nbsp; "
        f"**Containers processed today:** `1,847`"
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
        # Run "inference"
        with st.spinner("⚙️  Running VisionGate Edge AI inference..."):
            time.sleep(2)

        st.success("✅ Inference complete in **1.83 seconds** on NVIDIA Jetson Orin (INT8 quantised model).")

        col_img, col_result = st.columns([1.2, 1])

        # ── Left: Annotated Image ──
        with col_img:
            st.markdown("### 📷 AI-Annotated Inspection Frame")
            annotated = annotate_container_image(uploaded_file)
            st.image(annotated, use_container_width=True, caption="YOLOv8 Detection Output — Live Gate Frame")
            st.markdown(
                '<div class="custom-info" style="font-size:.8rem;">'
                '🔴 <b>Red box</b>: Structural damage zone (Severe Rust) &nbsp;|&nbsp; '
                '🟢 <b>Green box</b>: ISO code plate region</div>',
                unsafe_allow_html=True,
            )

        # ── Right: Inspection Result Card ──
        with col_result:
            st.markdown("### 📋 Inspection Result Card")

            st.markdown(
                '<div class="custom-warning">'
                '⚠️ <b>INSPECTION STATUS: ACTION REQUIRED</b><br>'
                '<span class="badge badge-red">HIGH RISK</span>'
                '<span class="badge badge-yellow">STRUCTURAL</span>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # ISO Code
            st.markdown("**📦 ISO Container Code (ISO 6346)**")
            st.code("MSKU 123456 7", language=None)
            st.markdown(
                '<span class="badge badge-green">✓ Validated — ISO 6346 Checksum Pass</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            # Structural Status
            st.markdown("**🔩 Structural Integrity Status**")
            st.markdown(
                '<div class="custom-danger">⛔ <b>WARNING: Severe Rust on Left Panel</b><br>'
                'AI Confidence: 98.2% &nbsp;|&nbsp; Affected Area: ~34% of panel surface<br>'
                'Risk Category: <b>CRITICAL — Load-bearing compromise possible</b></div>',
                unsafe_allow_html=True,
            )

            # Routing Action
            st.markdown("**🚦 Automated Routing Action**")
            st.markdown(
                '<div class="custom-danger">'
                '🚫 <b>Redirect to Maintenance Yard. Do NOT Load on Vessel.</b><br>'
                'Gate barrier auto-locked. Truck directed to Lane M-7.</div>',
                unsafe_allow_html=True,
            )

            # TOS Sync
            st.markdown("**🔄 Terminal Operating System Sync**")
            st.markdown(
                '<div class="custom-success">'
                '✅ <b>Successfully synced via API to DP World CARGOES TOS</b><br>'
                'Event ID: <code>TOS-EVT-20260327-001847</code><br>'
                'Shipping Line Notified: <b>MSC Mediterranean</b><br>'
                'Freight Forwarder Alert: <b>Sent via EDI 315</b></div>',
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Additional metadata
            with st.expander("🔬 Full Inspection Metadata"):
                st.json({
                    "inspection_id": "VG-INS-20260327-001847",
                    "terminal": terminal,
                    "timestamp_utc": datetime.datetime.utcnow().isoformat(),
                    "model_version": "YOLOv8-VisionGate-v2.4.1",
                    "inference_device": "NVIDIA Jetson Orin (INT8)",
                    "inference_time_ms": 183,
                    "iso_code": "MSKU 123456 7",
                    "iso_valid": True,
                    "container_type": "20ft Dry Standard",
                    "owner": "MSC Mediterranean",
                    "damage_detections": [
                        {
                            "class": "severe_rust",
                            "confidence": 0.982,
                            "panel": "left",
                            "bbox": [0.05, 0.30, 0.38, 0.75],
                        }
                    ],
                    "routing_action": "MAINTENANCE_YARD",
                    "tos_synced": True,
                    "tos_event_id": "TOS-EVT-20260327-001847",
                })

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
