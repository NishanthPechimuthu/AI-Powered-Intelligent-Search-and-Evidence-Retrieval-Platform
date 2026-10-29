"""Alert Service: Dispatches Twilio SMS notifications directly using simple Client pattern."""
import os
import time
import threading
from typing import Dict, Any, List, Optional
from twilio.rest import Client

from app.config import settings

class AlertService:
    def __init__(self):
        self.cooldown_seconds: float = 15.0
        self.last_alert_time: Dict[str, float] = {}
        self.alerts_enabled: bool = False  # OFF by default

    def toggle_alerts(self) -> bool:
        self.alerts_enabled = not self.alerts_enabled
        return self.alerts_enabled

    def send_threat_alert_async(self, event_data: Dict[str, Any]):
        """Non-blocking: fires SMS in a background thread."""
        thread = threading.Thread(
            target=self.send_threat_alert,
            args=(event_data,),
            daemon=True,
            name=f"AlertThread-{event_data.get('id', 'unknown')}"
        )
        thread.start()

    def send_threat_alert(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple, direct Twilio SMS dispatch:
        1. Check toggle (OFF by default)
        2. Check DB — send ONLY ONCE per incident
        3. Build alert message
        4. Send SMS via Twilio Client (same pattern as user's sample code)
        """
        if not self.alerts_enabled:
            return {"status": "disabled", "reason": "alerts_toggle_off"}

        from app.services.event_manager import event_manager
        event_id = event_data.get("id")

        # Only ONE alert per incident
        if event_id and event_manager.is_alert_sent(event_id):
            print(f"[AlertService] Alert already sent for {event_id}. Skipping.")
            return {"status": "skipped", "reason": "already_sent"}

        camera_id = event_data.get("camera_id", "CAM-01")
        now = time.time()

        # Per-camera cooldown
        if camera_id in self.last_alert_time:
            if now - self.last_alert_time[camera_id] < self.cooldown_seconds:
                print(f"[AlertService] Cooldown active for {camera_id}. Skipping.")
                return {"status": "skipped", "reason": "cooldown"}

        self.last_alert_time[camera_id] = now

        # Load Twilio credentials directly (same as user's sample code)
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", settings.TWILIO_ACCOUNT_SID)
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", settings.TWILIO_AUTH_TOKEN)
        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", settings.TWILIO_PHONE_NUMBER)

        if not account_sid or not auth_token or not twilio_phone:
            print("[AlertService] Twilio credentials not configured. Skipping.")
            return {"status": "error", "reason": "no_credentials"}

        # Build recipients
        recipients = []
        for num in [settings.TO_NUMBER_1, settings.TO_NUMBER_2]:
            if num and num.strip() and num.strip() not in recipients:
                recipients.append(num.strip())

        if not recipients:
            print("[AlertService] No recipient numbers configured.")
            return {"status": "error", "reason": "no_recipients"}

        # Build alert message
        timestamp_str = event_data.get("detection_timestamp", time.strftime("%H:%M:%S"))
        confidence = float(event_data.get("confidence", 0.0))
        conf_pct = round(confidence * 100, 1)

        sms_body = (
            f"🚨 VIOLENCE ALERT: Physical altercation detected on {camera_id} "
            f"at {timestamp_str}. Confidence: {conf_pct}%. "
            f"Immediate action required! - CCTV Monitor"
        )

        # Initialize Twilio Client (same as user's sample)
        try:
            client = Client(account_sid, auth_token)
        except Exception as e:
            print(f"[AlertService] Failed to create Twilio client: {e}")
            return {"status": "error", "reason": str(e)}

        results = {"sms": []}
        any_success = False

        # Send SMS to each recipient
        for to_num in recipients:
            try:
                message = client.messages.create(
                    from_=twilio_phone.strip(),
                    to=to_num,
                    body=sms_body
                )
                results["sms"].append({"to": to_num, "sid": message.sid, "status": message.status})
                print(f"[AlertService] SMS sent to {to_num} (SID: {message.sid}, Status: {message.status})")
                any_success = True
            except Exception as e:
                error_msg = str(e)
                print(f"[AlertService] Error sending SMS to {to_num}: {error_msg}")
                results["sms"].append({"to": to_num, "error": error_msg})

        # Mark alert as sent in local DB (even if some failed, to prevent spam)
        if event_id:
            event_manager.mark_alert_sent(event_id)
            print(f"[AlertService] Marked incident {event_id} as alerted in DB.")

        return {"status": "success" if any_success else "failed", "results": results}

alert_service = AlertService()
