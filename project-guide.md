🗂️ Genie Whisper X – Project Guide
1. High-Level Architecture
Backend (Python)

Voice capture, VAD, wake word, Whisper STT, command parsing, TTS, system actions, memory/state, WebSocket comms.

Frontend (Tauri + React)

Widgetized UI: waveform HUD, transcript panel, action console, memory tray, API toggle, settings.

Comms Layer

WebSocket server for bi-directional real-time data (Python ↔ UI).

2. Phase 1 Tactical Roadmap
a. Folder Structure Setup

/backend/ – All agent logic, modules, and system hooks

/ui/ – Tauri + React frontend shell

/websocket/ – Real-time data pipe

/memory-bank/ – Logs, dev docs, ops records

/scripts/ – Utility scripts: model download, updates

Root files: launchers, config, requirements, etc.

b. Module Build Order

Voice Capture + VAD

Local-only

Logs activity to memory bank

Wake Word Engine

“Hey Genie” or custom phrase

Whisper STT

Local-only, switchable models (tiny → large)

Intent Parser

Simple regex/NLP initially; can swap for OpenAI on toggle

Command Engine

Executes basic OS actions, logs results

TTS Engine

Local-only first; upgrade to multi-voice later

WebSocket Server

Pipe events/statuses to frontend

UI Frontend

Minimal viable widgets, no wasted pixels

API Toggle (Optional)

Encrypt and securely manage key

3. Dev Workflow Orders
All commits must log to /memory-bank/ with summary, agent, and intent.

All modules are hot-swappable and must be isolated.

Test each module independently before integration.

No Electron, no monolithic Node backends—Tauri is preferred for speed, security, and memory.

4. Security & Offline Ops
All models and actions local; UI notifies user if cloud API is requested.

Secure .env or encrypted API key storage.

Manual toggle for all external requests.

No background network traffic.

5. Agent Success Checkpoints
UI: “Backend Ready” is shown at launch.

Wake word is detected, logs wake event.

Waveform is live and follows mic input.

STT prints transcript to UI panel.

Action engine executes and confirms command in UI.

TTS gives real-time voice feedback.

Logs for each session saved to /memory-bank/.

Cloud API is toggled off by default, tested with dummy key.

