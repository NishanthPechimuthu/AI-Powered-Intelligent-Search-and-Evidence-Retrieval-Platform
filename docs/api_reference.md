# Complete API Reference Manual

This document provides complete, verified documentation of all existing API endpoints, WebSocket feeds, and static media routes in the platform, followed by specifications for proposed semantic search and video QA endpoints.

---

## 1. Global API Conventions

- **Base URL**: Default: `http://127.0.0.1:8002` (configurable via `BACKEND_PORT` in `.env`).
- **CORS**: Enabled with `allow_origins=["*"]`, allowing requests from the Next.js frontend (`http://localhost:3000`).
- **Authentication**: Currently open (development/local CCTV appliance mode; zero authentication tokens required).
- **Format**: All JSON responses use standard UTF-8 encoding. Timestamps are formatted as `HH:MM:SS` or ISO-8601 strings.

---

## 2. Verified Active Endpoints

### 2.1 System & Telemetry Endpoints

#### `GET /api/health`
- **Source**: [backend/app/main.py](file:///home/nishanth/Projects/NEXGI/backend/app/main.py#L83-L85)
- **Purpose**: Verifies that the FastAPI process is active and operational.
- **Request Headers**: None.
- **Query / Path Parameters**: None.
- **Response Schema**:
  ```json
  {
    "status": "ok",
    "service": "cctv-violence-monitor"
  }
  ```
- **Status Codes**: `200 OK`.

#### `GET /api/stats`
- **Source**: [backend/app/main.py](file:///home/nishanth/Projects/NEXGI/backend/app/main.py#L87-L97)
- **Purpose**: Returns aggregate system telemetry, resource consumption, and camera throughput.
- **Response Schema**:
  ```json
  {
    "aggregate_fps": 35.4,
    "cpu_percent": 48.2,
    "memory_percent": 62.1,
    "active_cameras": 4,
    "total_events": 12
  }
  ```
- **Status Codes**: `200 OK`.

---

### 2.2 Camera Management & Streaming Endpoints

#### `GET /api/cameras`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L12-L15)
- **Purpose**: Lists all active camera feeds, their current threat status, violence probabilities, and streaming rates.
- **Response Example**:
  ```json
  [
    {
      "camera_id": "CAM-01",
      "name": "Camera 1 (cam01.mp4)",
      "violence_probability": 0.082,
      "status": "NORMAL",
      "last_inference_timestamp": "14:22:10",
      "source_fps": 25.0,
      "inference_fps": 8.7,
      "is_active": true,
      "consecutive_positives": 0,
      "twilio_alert_sent": false
    },
    {
      "camera_id": "CAM-03",
      "name": "Camera 3 (cam03.mp4)",
      "violence_probability": 0.842,
      "status": "VIOLENCE",
      "last_inference_timestamp": "14:22:10",
      "source_fps": 25.0,
      "inference_fps": 9.1,
      "is_active": true,
      "consecutive_positives": 4,
      "twilio_alert_sent": true
    }
  ]
  ```
- **Status Codes**: `200 OK`.

#### `GET /api/cameras/{camera_id}/status`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L86-L92)
- **Path Parameter**: `camera_id` (string, e.g. `CAM-01`).
- **Response**: Single camera status object matching schema above.
- **Error Response**: `404 Not Found` if camera ID does not exist:
  ```json
  {"detail": "Camera not found"}
  ```

#### `GET /api/cameras/{camera_id}/stream`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L108-L117)
- **Purpose**: Live video stream in multipart MJPEG format. Renders directly in standard HTML `<img>` tags.
- **Response Header**: `Content-Type: multipart/x-mixed-replace; boundary=frame`.
- **Payload**: Continuous stream of JPEG frames paced at ~25 FPS.
- **Status Codes**: `200 OK`, `404 Not Found`.

#### `POST /api/cameras/upload`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L37-L76)
- **Purpose**: Ingests a new video file, saves it to `videos/`, assigns a new `CAM-XX` ID, and initializes a dedicated `CameraWorker` thread.
- **Content-Type**: `multipart/form-data`.
- **Form Parameters**:
  - `file`: Video binary (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.m4v`). Required.
  - `name`: Custom camera label (string, optional).
- **Validation**: Rejects invalid extensions with `400 Bad Request`.
- **Response Example**:
  ```json
  {
    "camera_id": "CAM-05",
    "name": "Warehouse West Corridor (feed5.mp4)",
    "violence_probability": 0.0,
    "status": "NORMAL",
    "last_inference_timestamp": "14:25:00",
    "source_fps": 25.0,
    "inference_fps": 0.0,
    "is_active": true,
    "consecutive_positives": 0,
    "twilio_alert_sent": false
  }
  ```

#### `DELETE /api/cameras/{camera_id}`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L78-L84)
- **Query Parameter**: `delete_file` (boolean, default `true`).
- **Purpose**: Terminates worker thread, releases file handles, unregisters feed, and deletes video file from disk if requested.
- **Response**: `{"success": true, "camera_id": "CAM-05"}`.
- **Status Codes**: `200 OK`, `404 Not Found`.

#### `GET /api/cameras/blur-faces` & `POST /api/cameras/blur-faces`
- **Source**: [backend/app/api/cameras.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/cameras.py#L17-L29)
- **Purpose**: Inspects or toggles real-time OpenCV Haar cascade face blurring across live video streams.
- **Query Parameter (POST)**: `enabled` (boolean, optional; if omitted, toggles state).
- **Response**: `{"blur_faces": true}`.

---

### 2.3 Evidence & Incident Event Endpoints

#### `GET /api/events`
- **Source**: [backend/app/api/events.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/events.py#L7-L10)
- **Query Parameter**: `limit` (integer, default `50`, min `1`, max `200`).
- **Response Example**:
  ```json
  [
    {
      "id": "evt_48f91a20",
      "camera_id": "CAM-03",
      "start_timestamp": "14:22:05",
      "detection_timestamp": "14:22:05",
      "end_timestamp": "14:22:15",
      "confidence": 0.842,
      "status": "VIOLENCE",
      "image_path": "/evidence/CAM-03/14-22-05.jpg",
      "clip_path": "/clips/CAM-03/14-22-05.mp4",
      "twilio_alert_sent": 1,
      "created_at": "2026-10-29T14:22:05.120"
    }
  ]
  ```

#### `GET /api/events/{event_id}` & `GET /api/events/{event_id}/evidence`
- **Source**: [backend/app/api/events.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/events.py#L12-L33)
- **Purpose**: Fetches incident details or media paths for a specific incident.
- **Status Codes**: `200 OK`, `404 Not Found`.

#### `POST /api/events/test-alert`
- **Source**: [backend/app/api/events.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/events.py#L35-L58)
- **Query Parameter**: `camera_id` (string, default `"CAM-01"`).
- **Purpose**: Manually tests Twilio SMS/WhatsApp dispatch, Ngrok public image URL generation, and Qwen LLM analysis.
- **Response**:
  ```json
  {
    "status": "triggered",
    "alert_result": {
      "status": "success",
      "results": {
        "sms": [{"to": "+917200524344", "sid": "SM...", "status": "queued"}]
      }
    },
    "event": { ... }
  }
  ```

#### `GET /api/events/alerts/status` & `POST /api/events/alerts/toggle`
- **Source**: [backend/app/api/events.py](file:///home/nishanth/Projects/NEXGI/backend/app/api/events.py#L59-L71)
- **Purpose**: Inspects or toggles global Twilio notification dispatch (default: `false` to avoid unintended SMS consumption).
- **Response**: `{"alerts_enabled": true}`.

---

### 2.4 WebSocket Real-Time Telemetry

#### `WS /ws/live`
- **Source**: [backend/app/main.py](file:///home/nishanth/Projects/NEXGI/backend/app/main.py#L99-L125)
- **Protocol**: Standard WebSocket.
- **Initial Connection Handshake**: Sends full initial snapshot:
  ```json
  {
    "type": "INIT",
    "cameras": [ ... ],
    "events": [ ... ]
  }
  ```
- **Periodic Telemetry Broadcast**: Pushes telemetry every 400 milliseconds:
  ```json
  {
    "type": "STATUS_UPDATE",
    "cameras": [ ... ]
  }
  ```
- **Asynchronous Threat Alerts**: When violence occurs, immediately broadcasts:
  ```json
  {
    "type": "EVENT",
    "data": {
      "id": "evt_91823ab4",
      "camera_id": "CAM-03",
      "confidence": 0.88,
      "image_path": "/evidence/CAM-03/14-22-05.jpg",
      "clip_path": null
    }
  }
  ```

---

## 3. Proposed Endpoints for Semantic Retrieval & Video QA

To complete the natural-language video search and question-answering architecture, the following endpoints are proposed for implementation:

### 3.1 `POST /api/search/frames` (Semantic Vector Retrieval)
- **Purpose**: Embeds a natural language query via a cross-modal encoder (SigLIP), searches the vector index, and returns top-$K$ candidate frames.
- **Request Body**:
  ```json
  {
    "query": "person holding a red backpack",
    "camera_id": "CAM-03",
    "top_k": 5,
    "similarity_threshold": 0.25,
    "start_time": "2026-10-29T14:00:00",
    "end_time": "2026-10-29T15:00:00"
  }
  ```
- **Response Schema**:
  ```json
  {
    "query": "person holding a red backpack",
    "total_candidates": 5,
    "frames": [
      {
        "frame_id": "c03_f004821",
        "camera_id": "CAM-03",
        "timestamp": "14:22:05",
        "similarity_score": 0.742,
        "image_url": "/evidence/CAM-03/frm_c03_004821.jpg"
      }
    ]
  }
  ```

### 3.2 `POST /api/qa/video` (Evidence-Grounded Visual QA)
- **Purpose**: Executes the full pipeline: embeds query $\to$ retrieves top-$K$ frames $\to$ prompts VLM reasoning engine $\to$ returns verified, evidence-grounded answer with timestamp citations.
- **Request Body**:
  ```json
  {
    "question": "What happens when the individual in dark clothing enters the room?",
    "camera_id": "CAM-03",
    "max_evidence_frames": 4
  }
  ```
- **Response Schema**:
  ```json
  {
    "question": "What happens when the individual in dark clothing enters the room?",
    "answer": "At [Frame 1 @ 14:22:05], the individual enters through the door. At [Frame 2 @ 14:22:07], they approach the counter and reach toward an object. By [Frame 3 @ 14:22:11], they conceal the item in their jacket.",
    "direct_observations": [
      "Individual enters room at 14:22:05",
      "Reaches toward desk surface at 14:22:07"
    ],
    "inferred_conclusions": [
      "Subject appears to conceal item prior to exiting"
    ],
    "abstention_flags": [],
    "supporting_evidence": [
      {
        "frame_index": 1,
        "timestamp": "14:22:05",
        "image_url": "/evidence/CAM-03/14-22-05.jpg",
        "relevance_score": 0.812
      }
    ]
  }
  ```
