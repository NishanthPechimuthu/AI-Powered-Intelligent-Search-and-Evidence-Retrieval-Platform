"""Ngrok Tunnel Manager for sharing evidence image links publicly."""
import os
import requests
from typing import Optional
from pyngrok import ngrok
from app.config import settings

class TunnelManager:
    def __init__(self):
        self.public_url: Optional[str] = None

    def get_base_url(self) -> Optional[str]:
        """Returns the active public ngrok base URL, initializing if needed."""
        # 1. Check if configured explicitly in env
        if settings.NGROK_BASE_URL and settings.NGROK_BASE_URL.strip():
            return settings.NGROK_BASE_URL.strip().rstrip("/")

        # 2. Check cached public URL
        if self.public_url:
            return self.public_url

        # 3. Query local ngrok client API if ngrok is already running
        try:
            res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1.5)
            if res.status_code == 200:
                tunnels = res.json().get("tunnels", [])
                for t in tunnels:
                    pub = t.get("public_url")
                    if pub and pub.startswith("https"):
                        self.public_url = pub.rstrip("/")
                        return self.public_url
                    elif pub and not self.public_url:
                        self.public_url = pub.rstrip("/")
        except Exception:
            pass

        # 4. Attempt starting an ngrok tunnel via pyngrok
        try:
            if settings.NGROK_AUTHTOKEN and settings.NGROK_AUTHTOKEN.strip():
                ngrok.set_auth_token(settings.NGROK_AUTHTOKEN.strip())
            
            tunnel = ngrok.connect(settings.BACKEND_PORT, "http")
            self.public_url = tunnel.public_url.rstrip("/")
            print(f"[TunnelManager] Opened ngrok tunnel: {self.public_url}")
            return self.public_url
        except Exception as e:
            print(f"[TunnelManager] Notice: Could not auto-start ngrok tunnel: {e}")
            return None

    def get_public_image_url(self, image_relative_path: str) -> Optional[str]:
        """
        Converts a relative image path (e.g. CAM-01/evt_123.jpg or evidence/CAM-01/evt_123.jpg)
        into a publicly accessible HTTPS ngrok URL.
        """
        base_url = self.get_base_url()
        if not base_url:
            return None

        clean_path = image_relative_path.strip().lstrip("/")
        if not clean_path.startswith("evidence/"):
            clean_path = f"evidence/{clean_path}"

        return f"{base_url}/{clean_path}"

tunnel_manager = TunnelManager()
