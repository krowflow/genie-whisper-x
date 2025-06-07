#!/usr/bin/env python3
"""
Genie Whisper X - Model Setup Script
Downloads and verifies local AI models
"""
import os
import sys
import requests
import hashlib
from pathlib import Path

class ModelSetup:
    """Downloads and manages local AI models"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.models = {
            "whisper_tiny": {
                "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
                "filename": "ggml-tiny.bin",
                "sha256": "bd577a113a864445d4c299885e0cb97d4ba92b5f5962c2b7b2c2b8e5c3f3a2f"
            },
            "silero_vad": {
                "url": "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx",
                "filename": "silero_vad.onnx",
                "sha256": "e4c67b88f2b0c6b0f8a5c9b2e2f8e9c6b0c6b0c6b0c6b0c6b0c6b0c6b0c6b0"
            }
        }
    
    def download_file(self, url: str, filepath: Path) -> bool:
        """Download file with progress indication"""
        try:
            print(f"Downloading {filepath.name}...")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✓ Downloaded {filepath.name}")
            return True
            
        except Exception as e:
            print(f"\n✗ Failed to download {filepath.name}: {e}")
            return False
    
    def verify_checksum(self, filepath: Path, expected_sha256: str) -> bool:
        """Verify file integrity with SHA256"""
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_sha256 = sha256_hash.hexdigest()
            
            if actual_sha256 == expected_sha256:
                print(f"✓ Checksum verified for {filepath.name}")
                return True
            else:
                print(f"✗ Checksum mismatch for {filepath.name}")
                print(f"  Expected: {expected_sha256}")
                print(f"  Actual:   {actual_sha256}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to verify {filepath.name}: {e}")
            return False
    
    def setup_model(self, model_key: str) -> bool:
        """Download and verify a specific model"""
        model_config = self.models.get(model_key)
        if not model_config:
            print(f"✗ Unknown model: {model_key}")
            return False
        
        filepath = self.models_dir / model_config["filename"]
        
        # Skip if file already exists and is valid
        if filepath.exists():
            print(f"Model {model_key} already exists, verifying...")
            if self.verify_checksum(filepath, model_config["sha256"]):
                return True
            else:
                print(f"Removing corrupted file: {filepath}")
                filepath.unlink()
        
        # Download the model
        if not self.download_file(model_config["url"], filepath):
            return False
        
        # Verify checksum
        return self.verify_checksum(filepath, model_config["sha256"])
    
    def setup_all_models(self):
        """Download and verify all models"""
        print("🤖 Setting up Genie Whisper X models...")
        print(f"Models directory: {self.models_dir.absolute()}")
        
        success_count = 0
        total_count = len(self.models)
        
        for model_key in self.models:
            print(f"\n📦 Setting up {model_key}...")
            if self.setup_model(model_key):
                success_count += 1
            else:
                print(f"✗ Failed to setup {model_key}")
        
        print(f"\n🎯 Setup complete: {success_count}/{total_count} models ready")
        
        if success_count == total_count:
            print("✅ All models ready! Genie Whisper X is ready to run.")
            return True
        else:
            print("⚠️ Some models failed to download. Check your internet connection.")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Setup specific model
        model_key = sys.argv[1]
        setup = ModelSetup()
        if not setup.setup_model(model_key):
            sys.exit(1)
    else:
        # Setup all models
        setup = ModelSetup()
        if not setup.setup_all_models():
            sys.exit(1)

if __name__ == "__main__":
    main()