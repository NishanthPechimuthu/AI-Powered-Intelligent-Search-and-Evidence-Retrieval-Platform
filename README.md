# AI-Powered Intelligent Search and Evidence Retrieval Platform (NEXGI)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](docs/licensing_analysis.md)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.3-black.svg)](https://nextjs.org/)
[![MoViNet-A0](https://img.shields.io/badge/Model-MoViNet--A0%20(TFLite)-orange.svg)](https://huggingface.co/engares/MoViNet4Violence-Detection)
[![Qwen Vision AI](https://img.shields.io/badge/VLM-Qwen--VL%20Endpoint-purple.svg)](https://github.com/QwenLM/Qwen2.5-VL)

An end-to-end, edge-native intelligent video surveillance, automated violence detection, forensic evidence retrieval, and multimodal reasoning platform. 

The platform continuously monitors multi-camera CCTV streams on local edge compute, detects security threats in real time via streaming 3D convolutional networks, automatically extracts high-resolution evidence snapshots and rolling video clips, dispatches multi-channel alerts with public forensic links, and provides an architectural foundation for natural-language video question answering.

---

## Technical Documentation Index

For deep architectural and implementation specifications, consult the dedicated manuals in [`docs/`](docs/):

- 🏛️ **[System Architecture & Component Verification](docs/architecture.md)**: Full component matrix, request lifecycles, and structural separation between retrieval and reasoning.
- 🔍 **[Embedding & Retrieval System](docs/embedding_and_retrieval.md)**: Cross-modal alignment (SigLIP/CLIP), vector database schemas (Qdrant), and keyframe deduplication.
- 🧠 **[Reasoning Model & Optimization Guide](docs/reasoning_model_and_optimization.md)**: Vision-language task breakdown, forensic prompt architecture, anti-jailbreak directives, QLoRA fine-tuning, and inference quantization.
- 📡 **[Complete API Reference Manual](docs/api_reference.md)**: Verified REST endpoints, WebSockets, MJPEG streaming, request/response schemas, and proposed search routes.
- 📊 **[Evaluation & Benchmarking Strategy](docs/evaluation_and_benchmarking.md)**: Measured CPU baselines, retrieval metrics (Recall@K, MRR, tIoU), and VQA grounding metrics.
- 🛡️ **[Security, Deployment & Operations](docs/security_and_deployment.md)**: Visual prompt injection defense, upload sanitization, systemd daemons, and production deployment.
- ⚖️ **[Open-Source Licensing Analysis](docs/licensing_analysis.md)**: Legal comparative analysis (MIT vs. Apache-2.0) and third-party dependency audit.
- 🗺️ **[Technical Debt & Prioritized Roadmap](docs/roadmap.md)**: Identified system gaps and a phased 5-stage development roadmap.

---

## 1. System Architecture Overview

```text
                        MULTI-CAMERA CCTV FEEDS
         cam01.mp4       cam02.mp4       cam03.mp4       Uploaded Feeds
             │               │               │                  │
             ▼               ▼               ▼                  ▼
        Worker 1        Worker 2        Worker 3           Worker N
       (Thread 1)      (Thread 2)      (Thread 3)         (Thread N)
             │               │               │                  │
             └───────────────┴───────┬───────┴──────────────────┘
                                     ▼
                      Frame Sampling (~5 FPS / stream)
                                     ▼
                       MoViNet-A0 Streaming Model
                          (172x172 RGB Tensor)
                                     ▼
                      Temporal Smoothing State Machine
            [NORMAL] ──> [CANDIDATE] ──> [VIOLENCE] ──> [COOLDOWN]
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
              Normal Status                   Evidence Capture
              (Zero Alert)                            │
                                        ┌─────────────┴─────────────┐
                                        ▼                           ▼
                                    image.jpg                   clip.mp4
                                   (Keyframe)               (10s H.264 Clip)
                                        └─────────────┬─────────────┘
                                                      ▼
                                            local_data/ Storage
                                                      │
         ┌──────────────────────────┬─────────────────┴──────────────────────────┐
         ▼                          ▼                                            ▼
   FastAPI Server            Pyngrok Tunnel                              Twilio & Qwen AI
 (REST + WebSockets)      (Public HTTPS Proof)                       (SMS / WhatsApp Alert)
         │                          │                                            │
         ▼                          └─────────────────────┬──────────────────────┘
  Next.js 16 HUD                                          ▼
 (2x2 Multi-View)                               Security Operations Center
```

---

## 2. Measured Benchmark Results

All figures below are empirically measured under local CPU execution via `scripts/benchmark.py`:

| Metric | Measured Baseline Value | Target Requirement | Evaluation Result |
|---|---|---|---|
| **Camera 1 Throughput** | **8.4 FPS** (93.1 ms latency) | $\ge 5.0$ FPS | Exceeded (168% of target) |
| **Camera 2 Throughput** | **8.7 FPS** (94.8 ms latency) | $\ge 5.0$ FPS | Exceeded (174% of target) |
| **Camera 3 Throughput** | **9.1 FPS** (94.7 ms latency) | $\ge 5.0$ FPS | Exceeded (182% of target) |
| **Camera 4 Throughput** | **9.2 FPS** (93.2 ms latency) | $\ge 5.0$ FPS | Exceeded (184% of target) |
| **Aggregate Inference Rate** | **35.4 FPS** | $\ge 20.0$ FPS | **Passed (177% of target)** |
| **Average Latency per Frame** | **94.0 ms** | $\le 200.0$ ms | Passed |
| **System CPU Utilization** | **~51%** (Multi-core) | $\le 85\%$ | Healthy / Sustainable |
| **Process RAM Footprint** | **~320 MB (0.32 GB)** | $\le 2.0$ GB | Ultra-lightweight |

---

## 3. Pretrained Model Verification & Action Detection

The platform utilizes a pretrained, quantized streaming MoViNet-A0 checkpoint fine-tuned for violence classification:
- **Architecture**: MoViNet-A0 Stream (Mobile Video Network, Google Research)
- **Trained Checkpoint**: [`engares/MoViNet4Violence-Detection`](https://huggingface.co/engares/MoViNet4Violence-Detection)
- **Class Mapping**:
  - `Index 0`: **`Fight`** (Physical altercation probability)
  - `Index 1`: **`No_Fight`** (Normal activity probability)

### Verification Summary (`scripts/verify_model.py`):
- **Normal Activity Footage (`cam01.mp4`)**: Average violence probability: **0.328** (Class: `No_Fight`, 0 false alarms).
- **Physical Altercation Footage (`cam03.mp4`)**: Initial probability: **0.310** $\to$ escalates sustained to **0.782 - 0.841** (Class: `Fight`). Triggers confirmed alert state after $N=3$ consecutive frames.

---

## 4. End-to-End Video Question-Answering Pipeline (Target)

In addition to automated violence detection, the platform architecture supports investigator-driven natural-language video search:

```text
User Question: "What object did the person pick up before running?"
  │
  ▼
SigLIP Cross-Modal Text Encoder (Dim: 1152)
  │
  ▼
Cosine Similarity Search over Video Frame Index (Qdrant / Chroma)
  │
  ▼
Top-K Relevant Candidate Frames + Timestamps (e.g. Frame 1 @ 14:22:05, Frame 2 @ 14:22:09)
  │
  ▼
Temporal Deduplication & Sequential Context Assembly
  │
  ▼
Vision-Language Reasoning Engine (Qwen2.5-VL / Local VLM)
  │
  ▼
Grounded Forensic Answer:
"At [Frame 1 @ 14:22:05], Person A approaches desk. At [Frame 2 @ 14:22:09], Person A picks up a black handheld device."
```

For the full architectural and mathematical breakdown, see [`docs/embedding_and_retrieval.md`](docs/embedding_and_retrieval.md) and [`docs/reasoning_model_and_optimization.md`](docs/reasoning_model_and_optimization.md).

---

## 5. Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint & WebSocket handler
│   │   ├── config.py                # Pydantic Settings & path definitions
│   │   ├── models/
│   │   │   └── movinet/
│   │   │       ├── detector.py      # MoViNet-A0 streaming TFLite runner
│   │   │       ├── model.tflite     # Pretrained streaming weights
│   │   │       └── checkpoints/     # HuggingFace raw checkpoint files
│   │   ├── services/
│   │   │   ├── video_processor.py   # Multi-camera worker orchestrator
│   │   │   ├── camera_worker.py     # Independent thread, smoothing, rolling deque
│   │   │   ├── evidence_manager.py  # JPEG snapshots & FFmpeg H.264 clip encoder
│   │   │   ├── event_manager.py     # SQLite persistence layer
│   │   │   ├── alert_service.py     # Twilio SMS / WhatsApp notification dispatcher
│   │   │   ├── llm_service.py       # Qwen AI multimodal reasoning client
│   │   │   └── tunnel_manager.py    # Pyngrok public HTTPS tunnel manager
│   │   ├── api/
│   │   │   ├── cameras.py           # /api/cameras routes (stream, upload, blur)
│   │   │   └── events.py            # /api/events routes & alert test triggers
│   │   └── schemas/
│   │       └── events.py            # Pydantic data schemas
│   ├── requirements.txt
│   └── run.py                       # Backend launcher script
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Real-time monitoring dashboard
│   │   └── globals.css              # Dark surveillance HUD theme
│   ├── components/
│   │   ├── CameraFeed.tsx           # Live camera tile with probability gauge
│   │   ├── RecentEvents.tsx         # Incident log with evidence modal triggers
│   │   ├── EvidenceModal.tsx        # High-res image & MP4 video clip player
│   │   ├── StatsBar.tsx             # Telemetry banner (throughput, CPU, RAM)
│   │   ├── UploadVideoModal.tsx     # Dynamic drag-and-drop video uploader
│   │   ├── ExpandCameraModal.tsx    # Single-camera focus view modal
│   │   └── DeleteConfirmModal.tsx   # Camera feed removal modal
│   ├── package.json
│   └── tsconfig.json
│
├── docs/                            # Deep Technical Documentation Suite
│   ├── architecture.md              # System architecture & verification matrix
│   ├── embedding_and_retrieval.md   # Cross-modal retrieval & vector index specs
│   ├── reasoning_model_and_optimization.md # VLM prompts, fine-tuning & quantization
│   ├── api_reference.md             # Complete REST, WebSocket & route schemas
│   ├── evaluation_and_benchmarking.md # Metrics, baselines & benchmark commands
│   ├── security_and_deployment.md   # Security hardening, injection defense & setup
│   ├── licensing_analysis.md        # MIT vs. Apache-2.0 comparative analysis
│   └── roadmap.md                   # Phased 5-stage development roadmap
│
├── videos/                          # Video sources (CCTV test footage)
├── local_data/                      # Local generated artifacts (git-ignored)
│   ├── evidence/                    # Event keyframe JPEG snapshots
│   ├── clips/                       # Event 10-second H.264 MP4 clips
│   └── events/events.db             # Local SQLite incident database
│
├── scripts/
│   ├── download_model.py            # Download checkpoint weights & sample videos
│   ├── verify_model.py              # Verify model inference & probability scales
│   ├── benchmark.py                 # Multi-camera concurrency benchmark
│   ├── test_alert.py                # Twilio SMS, WhatsApp & Qwen AI alert tester
│   └── clean_local_data.py          # Safe local artifact cleanup script
│
├── .env.example                     # Environment template
├── .gitignore
└── README.md
```

---

## 6. Quick Start Guide

### Step 1: Environment Setup with `uv` (Python 3.11)
```bash
# Install Python 3.11
uv python install 3.11

# Create and activate virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install backend dependencies
uv pip install -r backend/requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update credentials in `.env`:
```env
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8002

TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15632393112
TO_NUMBER_1=+917200524344
QWEN_API_BASE_URL=https://vijay.blk2np.qzz.io
```

### Step 3: Verify Model & Run Benchmarks
```bash
# Verify MoViNet detector probabilities
python scripts/verify_model.py

# Run 4-camera concurrent inference benchmark
python scripts/benchmark.py

# Optional: Verify Twilio & Qwen alert integration
python scripts/test_alert.py
```

### Step 4: Start Backend Server
```bash
python backend/run.py
```
Backend initializes on `http://127.0.0.1:8002`.

### Step 5: Start Frontend Dashboard
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 7. Open-Source Licensing

This project is recommended for distribution under the **Apache License, Version 2.0**.
See the comprehensive legal review and dependency audit in [`docs/licensing_analysis.md`](docs/licensing_analysis.md).
