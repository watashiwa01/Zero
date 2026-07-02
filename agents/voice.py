import sys
import time

# Try importing dependencies, handle missing ones gracefully
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
        pass

    def speak(self, text):
        # Always output text to standard console
        print(f"Zero: {text}")
        sys.stdout.flush()
        
        if pyttsx3 is not None:
            try:
                # Initialize engine fresh each time to bind to the active playback device
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if voices:
                    engine.setProperty('voice', voices[0].id)
                engine.setProperty('rate', 175) # Set speaking rate
                
                # Short delay to allow Windows to release microphone audio resource/Bluetooth profile lock
                time.sleep(0.3)
                
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[Warning] Voice playback error: {e}", file=sys.stderr)

    def listen_for_speech(self, timeout=5):
        if sr is None:
            # Fallback to console input if speech_recognition package is missing
            return input("You (keyboard): ").strip()
            
        recognizer = sr.Recognizer()
        
        # Test if microphone is accessible
        try:
            mic = sr.Microphone()
        except Exception as e:
            print(f"[Info] Microphone not accessible ({e}). Falling back to keyboard input.")
            return input("You (keyboard): ").strip()

        try:
            with mic as source:
                print("\n[Listening... Speak now]")
                sys.stdout.flush()
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            print("[Processing audio...]")
            sys.stdout.flush()
            
            # Use Google Speech Recognition (free, no API key required)
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
            # Fallback for generic errors (e.g. PyAudio missing)
            if "pyaudio" in str(e).lower() or "no default input device" in str(e).lower():
                print("[Info] PyAudio not installed or no mic detected. Falling back to keyboard.")
            else:
                print(f"[Voice error: {e}]. Falling back to keyboard.")
            return input("You (keyboard): ").strip()
