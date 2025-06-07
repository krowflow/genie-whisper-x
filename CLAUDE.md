# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Genie Whisper X is a local-first AI voice agent with modular architecture that provides:
- Voice Activity Detection (VAD) and Wake Word Detection
- Speech-to-Text via Whisper (local processing)
- Intent parsing and command execution
- Text-to-Speech for voice feedback
- Real-time UI with waveform visualization
- Optional cloud API integration (OpenAI) that's disabled by default

## Architecture

**Backend (Python 3.11+)**: Voice processing pipeline, WebSocket server, system automation
**Frontend (Tauri + React)**: Real-time UI with waveform HUD, transcript panel, action console
**Communication**: WebSocket for bi-directional real-time data flow
**Security**: Local-first by default, encrypted API key storage, manual cloud toggles

## Core Technologies

- **ASR**: whisper.cpp or faster-whisper (local processing)
- **Wake Word**: Silero or Porcupine for "Hey Genie" detection
- **VAD**: WebRTC + Silero dual system
- **TTS**: Coqui TTS / pyttsx3 (local text-to-speech)
- **UI**: Tauri + React (cross-platform, secure)
- **Backend**: Python with asyncio WebSocket server

## Development Commands

Based on project documentation, the system should launch via:
- `npm run dev` (development mode)
- `start-genie.sh` (production launch script)

## Key Directories

- `/backend/` - All agent logic, modules, and system hooks
- `/ui/` - Tauri + React frontend shell  
- `/websocket/` - Real-time data pipe
- `/memory-bank/` - Development logs, operational records
- `/scripts/` - Utility scripts for model downloads and updates

## Development Principles

- **Modular Design**: Each subsystem (VAD, STT, TTS, NLU, Action, UI) is isolated and replaceable
- **Local-First**: All processing runs offline by default
- **API-Optional**: Cloud services only used when explicitly enabled
- **Real-Time Transparency**: UI shows active modules and system state
- **Hot-Swappable**: Modules can be updated without breaking core functionality

## Success Criteria

- UI shows "Backend Ready" at launch
- Wake word detection logs events
- Live waveform follows microphone input
- STT displays transcript in UI panel
- Command execution with UI confirmation
- TTS provides voice feedback
- Session logs saved to `/memory-bank/`
- Cloud API toggle off by default

## Security Requirements

- No automatic network traffic
- Manual authorization for microphone access
- Local model storage and processing
- Encrypted API key management
- User control over all external requests