"""
PRODUCTION ARCHITECTURE: EDGE INFERENCE MODULE (REAL ML IMPLEMENTATION)
=======================================================================
This module handles LOCAL machine learning inference for damage detection
and ISO code extraction using real ML models:

1. Ultralytics YOLOv8 — Fine-tuned on a container damage dataset for
   structural anomaly detection (rust, dent, hole, scratch, etc.).
2. EasyOCR — Lightweight PyTorch-based OCR for extracting ISO 6346
   container codes from the captured gate camera images.

The ML results from this module are then passed ALONGSIDE the original
images to the Gemini API for enhanced reasoning, summary generation,
weather-contextual analysis, and cargo document cross-referencing.

Pipeline:
    Image → YOLOv8 (damage bboxes) + EasyOCR (ISO code)
        → Structured JSON + Original Images → Gemini API → Enhanced Result
"""

import io
import re
import os
import logging
import numpy as np

try:
    from PIL import Image
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ─── Default model path ───
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "container_damage_yolov8.pt")


class EdgeVisionProcessor:
    """
    Handles local edge-inference for the VisionGate AI gate portal.
    Uses real YOLOv8 for damage detection and EasyOCR for ISO code reading.

    If models fail to load (missing files, deps), self.available = False
    and all methods return graceful empty results — allowing the app to
    fall back to Gemini-only analysis seamlessly.
    """

    # ── Severity mapping from YOLO class names ──
    # Maps detected damage class names to our 4-tier severity schema.
    SEVERITY_MAP = {
        "hole":          "critical",
        "major-damage":  "critical",
        "major_damage":  "critical",
        "crack":         "severe",
        "rust":          "severe",
        "corrosion":     "severe",
        "dent":          "moderate",
        "deformation":   "moderate",
        "scratch":       "minor",
        "paint-damage":  "minor",
        "paint_damage":  "minor",
        "minor-damage":  "minor",
        "minor_damage":  "minor",
        "stain":         "minor",
    }

    # ── ISO 6346 regex pattern ──
    # Matches container codes like MSCU 1234567, TEMU1234567, etc.
    ISO_PATTERN = re.compile(r'[A-Z]{3,4}\s?\d{6,7}\s?\d?')

    def __init__(self, yolo_model_path: str = None):
        """
        Initializes the edge inference processor.
        Attempts to load YOLOv8 and EasyOCR models into memory.

        Args:
            yolo_model_path: Path to the YOLOv8 .pt weights file.
                             Defaults to 'models/container_damage_yolov8.pt'.
        """
        self.yolo_model_path = yolo_model_path or DEFAULT_MODEL_PATH
        self.yolo_model = None
        self.ocr_reader = None
        self.available = False
        self._load_models()

    def _load_models(self):
        """
        Safely attempts to load the YOLOv8 and EasyOCR models.
        Sets self.available = True only if at least YOLO loads successfully.
        """
        # ── Load YOLOv8 ──
        try:
            if os.path.exists(self.yolo_model_path):
                from ultralytics import YOLO
                self.yolo_model = YOLO(self.yolo_model_path)
                logger.info(f"YOLOv8 model loaded from: {self.yolo_model_path}")
                self.available = True
            else:
                logger.warning(
                    f"YOLOv8 weights not found at '{self.yolo_model_path}'. "
                    f"Run 'python download_models.py' to download the model. "
                    f"Falling back to Gemini-only analysis."
                )
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")

        # ── Load EasyOCR ──
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR reader initialized (English, CPU mode).")
        except Exception as e:
            logger.warning(f"EasyOCR failed to load: {e}. OCR will be skipped.")

    # ─────────────────────────────────────────────────────────────────────
    # YOLO DAMAGE DETECTION
    # ─────────────────────────────────────────────────────────────────────

    def run_yolo_damage_detection(self, image_bytes: bytes, view: int = 1) -> list:
        """
        Runs YOLOv8 inference on a single container image to detect
        structural damage (rust, dents, holes, scratches, etc.).

        Args:
            image_bytes: Raw image bytes from the uploaded file.
            view: Which camera view this image represents (1 or 2).

        Returns:
            List of detection dicts, each containing:
              - class: damage type (e.g., 'rust', 'dent')
              - severity: mapped severity ('minor'/'moderate'/'severe'/'critical')
              - confidence: float 0.0-1.0
              - bbox_normalized: [x1, y1, x2, y2] in 0.0-1.0 range
              - panel: estimated panel location
              - view: camera view number (1 or 2)
              - description: auto-generated description string
        """
        detections = []
        if not self.yolo_model:
            return detections

        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_w, img_h = pil_image.size

            # Run YOLO prediction
            results = self.yolo_model.predict(
                source=pil_image,
                conf=0.25,       # Confidence threshold
                iou=0.45,        # NMS IoU threshold
                save=False,
                verbose=False,
            )

            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    # Extract class name
                    cls_id = int(box.cls.item())
                    cls_name = self.yolo_model.names.get(cls_id, f"class_{cls_id}")
                    conf = float(box.conf.item())

                    # Get bounding box in xyxy format and normalize to 0.0-1.0
                    xyxy = box.xyxy[0].tolist()
                    x1_norm = max(0.0, min(1.0, xyxy[0] / img_w))
                    y1_norm = max(0.0, min(1.0, xyxy[1] / img_h))
                    x2_norm = max(0.0, min(1.0, xyxy[2] / img_w))
                    y2_norm = max(0.0, min(1.0, xyxy[3] / img_h))

                    # Map severity from class name
                    severity = self.SEVERITY_MAP.get(
                        cls_name.lower().replace(" ", "_"),
                        "moderate"
                    )

                    # Estimate panel location from bbox position
                    cx = (x1_norm + x2_norm) / 2
                    cy = (y1_norm + y2_norm) / 2
                    panel = self._estimate_panel(cx, cy)

                    detections.append({
                        "view": view,
                        "class": cls_name.lower().replace(" ", "_"),
                        "severity": severity,
                        "confidence": round(conf, 3),
                        "bbox_normalized": [
                            round(x1_norm, 4),
                            round(y1_norm, 4),
                            round(x2_norm, 4),
                            round(y2_norm, 4),
                        ],
                        "panel": panel,
                        "description": f"YOLOv8 detected {cls_name} damage ({severity}) "
                                       f"on {panel} panel with {conf:.0%} confidence.",
                    })

            logger.info(f"YOLO inference on View {view}: {len(detections)} detections.")
        except Exception as e:
            logger.warning(f"YOLO inference failed on View {view}: {e}")

        return detections

    @staticmethod
    def _estimate_panel(cx: float, cy: float) -> str:
        """Estimates which container panel a detection is on based on bbox center."""
        if cx < 0.3:
            return "left"
        elif cx > 0.7:
            return "right"
        elif cy < 0.3:
            return "roof"
        elif cy > 0.7:
            return "floor"
        else:
            return "front"

    # ─────────────────────────────────────────────────────────────────────
    # EASYOCR — ISO 6346 CODE EXTRACTION
    # ─────────────────────────────────────────────────────────────────────

    def run_ocr_extraction(self, image_bytes: bytes) -> dict:
        """
        Runs EasyOCR on a container image to extract the ISO 6346 code.

        Args:
            image_bytes: Raw image bytes from the uploaded file.

        Returns:
            Dict containing:
              - iso_code: Extracted ISO code string, or None if not found
              - iso_valid: Whether the code matches ISO 6346 format
              - raw_texts: All text regions detected by OCR
        """
        result = {"iso_code": None, "iso_valid": False, "raw_texts": []}

        if not self.ocr_reader:
            return result

        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            np_image = np.array(pil_image)

            # Run EasyOCR
            ocr_results = self.ocr_reader.readtext(np_image)

            all_texts = []
            for (bbox, text, conf) in ocr_results:
                all_texts.append({"text": text, "confidence": round(float(conf), 3)})

            result["raw_texts"] = all_texts

            # Search for ISO 6346 pattern in all detected text
            full_text = " ".join([t["text"] for t in all_texts])
            iso_match = self.ISO_PATTERN.search(full_text.upper())

            if iso_match:
                iso_code = iso_match.group(0).strip()
                result["iso_code"] = iso_code
                result["iso_valid"] = True
                logger.info(f"EasyOCR extracted ISO code: {iso_code}")
            else:
                logger.info(f"EasyOCR found no ISO code. Raw texts: {[t['text'] for t in all_texts]}")

        except Exception as e:
            logger.warning(f"EasyOCR inference failed: {e}")

        return result

    # ─────────────────────────────────────────────────────────────────────
    # FULL DUAL-VIEW INSPECTION PIPELINE
    # ─────────────────────────────────────────────────────────────────────

    def run_dual_view_inspection(self, img_bytes_1: bytes, img_bytes_2: bytes) -> dict:
        """
        Complete dual-view ML inspection pipeline:
        1. YOLOv8 on both images → damage detections (tagged view:1 / view:2)
        2. EasyOCR on both images → best ISO code from either view
        3. Merges everything into a structured JSON payload

        Args:
            img_bytes_1: Raw bytes for View 1 (Left / Front Panel).
            img_bytes_2: Raw bytes for View 2 (Right / Rear Panel).

        Returns:
            Dict containing:
              - ml_detections: list of all YOLO detections across both views
              - ml_iso_code: best ISO code from OCR (or None)
              - ml_iso_valid: whether ISO code was validated
              - ml_ocr_view1: full OCR results from view 1
              - ml_ocr_view2: full OCR results from view 2
              - ml_overall_status: preliminary status based on worst detection
              - ml_model_info: metadata about the ML models used
        """
        # ── Run YOLO on both views ──
        detections_v1 = self.run_yolo_damage_detection(img_bytes_1, view=1)
        detections_v2 = self.run_yolo_damage_detection(img_bytes_2, view=2)
        all_detections = detections_v1 + detections_v2

        # ── Run OCR on both views ──
        ocr_v1 = self.run_ocr_extraction(img_bytes_1)
        ocr_v2 = self.run_ocr_extraction(img_bytes_2)

        # Pick the best ISO code (prefer one that's valid, then higher confidence)
        best_iso = None
        best_valid = False
        if ocr_v1.get("iso_valid"):
            best_iso = ocr_v1["iso_code"]
            best_valid = True
        elif ocr_v2.get("iso_valid"):
            best_iso = ocr_v2["iso_code"]
            best_valid = True

        # ── Determine preliminary overall status from ML detections ──
        severity_rank = {"critical": 4, "severe": 3, "moderate": 2, "minor": 1}
        worst_severity = 0
        for det in all_detections:
            rank = severity_rank.get(det.get("severity", "minor"), 1)
            worst_severity = max(worst_severity, rank)

        status_map = {0: "CLEAR", 1: "MINOR_DAMAGE", 2: "WARNING", 3: "CRITICAL", 4: "CRITICAL"}
        ml_overall_status = status_map.get(worst_severity, "CLEAR")

        return {
            "ml_detections": all_detections,
            "ml_iso_code": best_iso,
            "ml_iso_valid": best_valid,
            "ml_ocr_view1": ocr_v1,
            "ml_ocr_view2": ocr_v2,
            "ml_overall_status": ml_overall_status,
            "ml_detection_count": len(all_detections),
            "ml_model_info": {
                "yolo_model": os.path.basename(self.yolo_model_path) if self.yolo_model else "not_loaded",
                "ocr_engine": "EasyOCR v1.7+ (PyTorch, CPU)",
                "yolo_available": self.yolo_model is not None,
                "ocr_available": self.ocr_reader is not None,
            }
        }
