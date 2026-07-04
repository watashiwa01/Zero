import os
import sys
import time
import requests
import tempfile
import subprocess

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

class VoiceAgent:
    def __init__(self):
        # Read API key if available
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        # Default beautiful ElevenLabs Voice ID (Rachel)
        self.voice_id = "21m00Tcm4TlvDq8ikWAM" 

    def _play_mp3_native(self, file_path):
        """Plays MP3 using native Windows Media Player COM object via PowerShell."""
        abs_path = os.path.abspath(file_path)
        cmd = [
            "powershell",
            "-Command",
            f"$wmp = New-Object -ComObject WMPlayer.OCX; $wmp.URL = '{abs_path}'; while ($wmp.playState -ne 1) {{ Start-Sleep -Milliseconds 50 }}"
        ]
        subprocess.run(cmd)

    def _speak_elevenlabs(self, text):
        """Fetches voice from ElevenLabs API and plays natively."""
        if not self.api_key:
            return False
            
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=12)
            if response.status_code == 200:
                # Save MP3 audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    f.write(response.content)
                    temp_name = f.name
                
                try:
                    self._play_mp3_native(temp_name)
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_name):
                        try:
                            os.remove(temp_name)
                        except Exception:
                            pass
                return True
            else:
                print(f"[Warning] ElevenLabs returned status code: {response.status_code}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"[Warning] ElevenLabs API error: {e}", file=sys.stderr)
            return False

    def speak(self, text):
        # Always output text to standard console
        print(f"Zero: {text}")
        sys.stdout.flush()
        
        try:
            from core.system.avatar_window import set_avatar_state
            set_avatar_state("speaking")
        except ImportError:
            pass
            
        # Try ElevenLabs first
        played = self._speak_elevenlabs(text)
        
        # Fall back to local SAPI5 Offline TTS
        if not played and pyttsx3 is not None:
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if voices:
                    engine.setProperty('voice', voices[0].id)
                engine.setProperty('rate', 175)
                
                time.sleep(0.3)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[Warning] Local offline TTS error: {e}", file=sys.stderr)

        try:
            from core.system.avatar_window import set_avatar_state
            set_avatar_state("idle")
        except ImportError:
            pass

    def listen_for_speech(self, timeout=5):
        if sr is None:
            return input("You (keyboard): ").strip()
            
        recognizer = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception as e:
            print(f"[Info] Microphone not accessible ({e}). Falling back to keyboard input.")
            return input("You (keyboard): ").strip()

        try:
            with mic as source:
                print("\n[Listening... Speak now]")
                sys.stdout.flush()
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            print("[Processing audio...]")
            sys.stdout.flush()
            
            text = recognizer.recognize_google(audio)
            print(f"You (voice): {text}")
            return text.strip()
            
        except sr.WaitTimeoutError:
            print("[No speech detected (timeout)]")
            return ""
        except sr.UnknownValueError:
            print("[Could not understand audio]")
            return ""
        except sr.RequestError as e:
            print(f"[STT Request Error: {e}]. Falling back to keyboard.")
            return input("You (keyboard): ").strip()
        except Exception as e:
            if "pyaudio" in str(e).lower() or "no default input device" in str(e).lower():
                print("[Info] PyAudio not installed or no mic detected. Falling back to keyboard.")
            else:
                print(f"[Voice error: {e}]. Falling back to keyboard.")
            return input("You (keyboard): ").strip()
