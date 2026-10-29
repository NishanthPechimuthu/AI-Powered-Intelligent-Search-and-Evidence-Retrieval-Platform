"""Test script for verifying Qwen LLM, Ngrok Tunnel, and Twilio SMS/WhatsApp Alerting."""
import os
import sys
import cv2
import numpy as np

# Ensure backend directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.config import settings, EVIDENCE_DIR
from app.services.llm_service import llm_service
from app.services.tunnel_manager import tunnel_manager
from app.services.alert_service import alert_service

def main():
    print("=====================================================")
    print("  NEXGI Security System - Alert Verification Test   ")
    print("=====================================================")
    print(f"Twilio Account SID: {settings.TWILIO_ACCOUNT_SID[:6]}... (Configured: {bool(settings.TWILIO_ACCOUNT_SID)})")
    print(f"Twilio Phone Number: {settings.TWILIO_PHONE_NUMBER}")
    print(f"Recipient 1: {settings.TO_NUMBER_1}")
    print(f"Recipient 2: {settings.TO_NUMBER_2}")
    print(f"Qwen LLM API Base URL: {settings.QWEN_API_BASE_URL}")
    print("-----------------------------------------------------")

    # 1. Create a dummy evidence image frame if none exists
    test_cam_dir = os.path.join(EVIDENCE_DIR, "CAM-01")
    os.makedirs(test_cam_dir, exist_ok=True)
    test_img_path = os.path.join(test_cam_dir, "test_frame.jpg")

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "CCTV VIOLENCE DETECTED", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    cv2.putText(frame, "CAM-01 | THREAT CONFIDENCE: 98.5%", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(test_img_path, frame)
    print(f"[OK] Generated test evidence frame at: {test_img_path}")

    # 2. Test Ngrok Tunnel Manager
    print("\n--- Testing Ngrok Tunnel Manager ---")
    pub_image_url = tunnel_manager.get_public_image_url("CAM-01/test_frame.jpg")
    print(f"Public Image Proof URL: {pub_image_url}")

    # 3. Test Qwen LLM Text & Image Endpoints
    print("\n--- Testing Qwen LLM Endpoints ---")
    print("Calling Qwen /text endpoint for SMS...")
    sms_text = llm_service.generate_sms_content("CAM-01", "12:34:56", 0.985)
    print(f"Generated SMS Content:\n  -> {sms_text}")

    print("\nCalling Qwen /image endpoint for WhatsApp...")
    wa_text = llm_service.generate_whatsapp_content("CAM-01", "12:34:56", 0.985, test_img_path)
    print(f"Generated WhatsApp Content:\n  -> {wa_text}")

    # 4. Test Full Alert Dispatch via Twilio
    print("\n--- Testing Twilio SMS & WhatsApp Dispatcher ---")
    event_data = {
        "id": "test_evt_001",
        "camera_id": "CAM-01",
        "start_timestamp": "12:34:56",
        "detection_timestamp": "12:34:56",
        "end_timestamp": None,
        "confidence": 0.985,
        "status": "VIOLENCE",
        "image_path": "evidence/CAM-01/test_frame.jpg",
        "created_at": "2026-10-09T09:30:00"
    }

    result = alert_service.send_threat_alert(event_data)
    print(f"\nAlert Dispatch Result:\n{result}")

if __name__ == "__main__":
    main()
