"""Events API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from app.services.event_manager import event_manager

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("")
def list_events(limit: int = Query(default=50, ge=1, le=200)):
    """Returns recent events ordered by timestamp descending."""
    return event_manager.get_recent_events(limit=limit)

@router.get("/{event_id}")
def get_event(event_id: str):
    """Returns details for a single event."""
    event = event_manager.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/{event_id}/evidence")
def get_event_evidence(event_id: str):
    """Returns evidence image and clip paths for an event."""
    event = event_manager.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "event_id": event["id"],
        "camera_id": event["camera_id"],
        "detection_timestamp": event["detection_timestamp"],
        "confidence": event["confidence"],
        "image_url": event["image_path"],
        "clip_url": event["clip_path"]
    }

@router.post("/test-alert")
def trigger_test_alert(camera_id: str = "CAM-01"):
    """Triggers a test alert via Twilio SMS, WhatsApp, Qwen LLM, and Ngrok tunnel."""
    from app.services.alert_service import alert_service
    import datetime
    import uuid

    mock_event = {
        "id": f"test_{uuid.uuid4().hex[:6]}",
        "camera_id": camera_id,
        "start_timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "detection_timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "end_timestamp": None,
        "confidence": 0.98,
        "status": "VIOLENCE",
        "image_path": f"evidence/{camera_id}/test_frame.jpg",
        "clip_path": None,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    # Run alert synchronously so the response contains the result
    res = alert_service.send_threat_alert(mock_event)
    return {"status": "triggered", "alert_result": res, "event": mock_event}

@router.get("/alerts/status")
def get_alert_status():
    """Returns current status of Twilio SMS/WhatsApp alerts toggle."""
    from app.services.alert_service import alert_service
    return {"alerts_enabled": alert_service.alerts_enabled}

@router.post("/alerts/toggle")
def toggle_alerts():
    """Toggles Twilio SMS/WhatsApp alert dispatching ON/OFF."""
    from app.services.alert_service import alert_service
    enabled = alert_service.toggle_alerts()
    return {"alerts_enabled": enabled}


