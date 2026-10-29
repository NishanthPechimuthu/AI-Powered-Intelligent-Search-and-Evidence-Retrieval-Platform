"""LLM Service for generating threat alert content via Qwen AI Endpoints (https://vijay.blk2np.qzz.io)."""
import os
import requests
from typing import Optional
from app.config import settings

class QwenLLMService:
    def __init__(self, base_url: str = settings.QWEN_API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def generate_sms_content(self, camera_id: str, timestamp_str: str, confidence: float) -> str:
        """
        Calls Qwen /text endpoint to generate concise SMS alert content.
        """
        prompt = (
            f"URGENT: Illegal activity / security threat detected on camera {camera_id} at {timestamp_str}. "
            f"Confidence: {confidence * 100:.1f}%. Generate a short, urgent security alert text message (under 160 characters)."
        )
        try:
            url = f"{self.base_url}/text"
            res = requests.post(url, data={"user_prompt": prompt}, timeout=10.0)
            if res.status_code == 200 and res.text and res.text.strip():
                content = res.text.strip()
                # Ensure reasonable length for SMS
                return content[:280]
        except Exception as e:
            print(f"[QwenLLM] Error calling /text endpoint: {e}")

        # Fallback text alert
        return (
            f"⚠️ SECURITY ALERT: Illegal activity detected on camera {camera_id} at {timestamp_str}. "
            f"Confidence: {confidence * 100:.1f}%. Immediate action required!"
        )

    def generate_whatsapp_content(
        self, camera_id: str, timestamp_str: str, confidence: float, image_path: Optional[str] = None
    ) -> str:
        """
        Calls Qwen /image endpoint (multimodal visual reasoning) if image is provided,
        otherwise falls back to /text endpoint.
        """
        prompt = (
            f"Analyze this CCTV evidence frame. Threat / illegal activity detected on camera {camera_id} at {timestamp_str} "
            f"(Confidence: {confidence * 100:.1f}%). Describe the threat clearly and generate an urgent WhatsApp security alert message."
        )

        if image_path and os.path.exists(image_path):
            try:
                url = f"{self.base_url}/image"
                with open(image_path, "rb") as img_file:
                    files = {"image": (os.path.basename(image_path), img_file, "image/jpeg")}
                    data = {"user_prompt": prompt}
                    res = requests.post(url, data=data, files=files, timeout=15.0)
                    if res.status_code == 200 and res.text and res.text.strip():
                        return res.text.strip()
            except Exception as e:
                print(f"[QwenLLM] Error calling /image endpoint: {e}")

        # Fallback to /text if image endpoint fails or no image path
        return self.generate_sms_content(camera_id, timestamp_str, confidence)

llm_service = QwenLLMService()
