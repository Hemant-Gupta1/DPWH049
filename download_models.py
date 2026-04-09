"""
VisionGate AI - Model Download Script
======================================
Downloads the pre-trained YOLOv8 container damage detection model
from Roboflow Universe and saves it to the models/ directory.

Usage:
    python download_models.py

This script uses the Roboflow SDK to download a curated container
damage detection dataset and trains a YOLOv8 nano model on it.
The trained weights are saved to: models/container_damage_yolov8.pt

Prerequisites:
    pip install roboflow ultralytics
"""

import os
import sys
import shutil


def download_and_train():
    """
    Downloads a container damage detection dataset from Roboflow Universe
    and fine-tunes a YOLOv8 nano model on it.
    """
    # Create models directory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)
    output_path = os.path.join(models_dir, "container_damage_yolov8.pt")

    if os.path.exists(output_path):
        print("[OK] Model already exists at: " + output_path)
        print("     Delete it and re-run this script to retrain.")
        return

    print("=" * 60)
    print("  VisionGate AI - YOLOv8 Model Setup")
    print("=" * 60)

    # Step 1: Download dataset from Roboflow
    print("\n[Step 1] Downloading container damage dataset from Roboflow...")
    try:
        from roboflow import Roboflow

        rf = Roboflow(api_key="YOUR_ROBOFLOW_API_KEY")  # Public datasets work with any key
        project = rf.workspace("containers-damage-detection").project("container-damage-detection-1owma")
        version = project.version(1)
        dataset = version.download("yolov8")
        dataset_location = dataset.location
        print("   [OK] Dataset downloaded to: " + dataset_location)
    except Exception as e:
        print("\n[WARN] Roboflow download failed: " + str(e))
        print("       Falling back to using base YOLOv8n model (COCO-pretrained)...")
        print("       This model can still detect general objects. For best results,")
        print("       set your Roboflow API key in this script.\n")

        # Fallback: use the base YOLOv8 nano model
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")  # Downloads COCO-pretrained model
            # Save it directly as our model
            shutil.copy("yolov8n.pt", output_path)
            print("[OK] Base YOLOv8n model saved to: " + output_path)
            print("     Note: This uses COCO classes. Fine-tune on a container dataset for best results.")
        except Exception as e2:
            print("[ERROR] Failed to download base model: " + str(e2))
            sys.exit(1)
        return

    # Step 2: Train YOLOv8 on the dataset
    print("\n[Step 2] Training YOLOv8 on container damage dataset...")
    print("         This may take 10-30 minutes depending on your hardware.\n")
    try:
        from ultralytics import YOLO

        model = YOLO("yolov8n.pt")  # Start from COCO-pretrained nano model

        results = model.train(
            data=os.path.join(dataset_location, "data.yaml"),
            epochs=25,          # Sufficient for fine-tuning
            imgsz=640,
            batch=16,
            patience=5,         # Early stopping
            save=True,
            project=models_dir,
            name="training_run",
            exist_ok=True,
            verbose=True,
        )

        # Step 3: Copy best weights to final location
        best_weights = os.path.join(models_dir, "training_run", "weights", "best.pt")
        if os.path.exists(best_weights):
            shutil.copy(best_weights, output_path)
            print("\n[OK] Trained model saved to: " + output_path)
        else:
            # Fallback to last.pt
            last_weights = os.path.join(models_dir, "training_run", "weights", "last.pt")
            if os.path.exists(last_weights):
                shutil.copy(last_weights, output_path)
                print("\n[OK] Trained model saved to: " + output_path)
            else:
                print("[ERROR] Training completed but no weights file found.")
                sys.exit(1)

        print("\n" + "=" * 60)
        print("  [OK] Model setup complete!")
        print("  Model path: " + output_path)
        print("  You can now run: streamlit run app.py")
        print("=" * 60)

    except Exception as e:
        print("\n[ERROR] Training failed: " + str(e))
        print("        Falling back to base YOLOv8n model...")
        try:
            base_model_path = "yolov8n.pt"
            if os.path.exists(base_model_path):
                shutil.copy(base_model_path, output_path)
            else:
                from ultralytics import YOLO
                YOLO("yolov8n.pt")  # This downloads it
                shutil.copy("yolov8n.pt", output_path)
            print("[OK] Base YOLOv8n model saved to: " + output_path)
        except Exception as e2:
            print("[ERROR] Complete failure: " + str(e2))
            sys.exit(1)


if __name__ == "__main__":
    download_and_train()
