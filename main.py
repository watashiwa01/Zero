import sys
import os
import time
import threading

# Ensure directory is on PATH so relative package imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.kernel import ZeroKernel
from core.system.avatar_window import start_avatar_gui, set_avatar_state

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_os_thread(voice_mode):
    # Initialize the Zero Kernel inside the background thread
    print("[Kernel] Starting kernel components...")
    kernel = ZeroKernel()
    print("[Kernel] v0.3 — Database, Brain, Decision Engine, Memory, Planner, State initialized.")
    print("=" * 60)
    
    # ── v0.3: Startup Briefing (replaces simple proactive suggestion) ──
    time.sleep(1.0)
    print("\n[Zero — Startup Briefing]")
    briefing = kernel.get_startup_briefing()
    kernel.voice.speak(briefing)
    print("-" * 60)
    
    # Also check for proactive suggestions
    suggestion = kernel.get_proactive_suggestion()
    if suggestion:
        time.sleep(0.5)
        print("\n[Zero — Proactive Suggestion]")
        kernel.voice.speak(suggestion)
        print("-" * 60)

    is_awake = False
    
    while True:
        try:
            if voice_mode:
                if not is_awake:
                    # Passive listening for wake word
                    set_avatar_state("idle")
                    text = kernel.voice.listen_for_speech(timeout=8).lower()
                    if "zero" in text:
                        is_awake = True
                        set_avatar_state("listening")
                        kernel.voice.speak("Yes Varun?")
                else:
                    # Active command listening
                    set_avatar_state("listening")
                    command = kernel.voice.listen_for_speech(timeout=6)
                    if command:
                        if command.lower() in ["stop", "exit", "bye"]:
                            # v0.3: Clean shutdown with session save
                            wrapup = kernel.shutdown()
                            kernel.voice.speak(wrapup)
                            break
                        
                        set_avatar_state("thinking")
                        response = kernel.handle_command(command)
                        kernel.voice.speak(response)
                    else:
                        kernel.voice.speak("Going to sleep.")
                        is_awake = False
            else:
                # Keyboard Mode
                if not is_awake:
                    set_avatar_state("idle")
                    user_input = input("\nzero-os> ").strip()
                    if not user_input:
                        continue
                    
                    if user_input.lower() == "zero":
                        is_awake = True
                        set_avatar_state("listening")
                        print("Zero: Yes Varun? (Awaiting command...)")
                    elif user_input.lower() in ["exit", "quit", "stop", "bye"]:
                        # v0.3: Clean shutdown with session save
                        wrapup = kernel.shutdown()
                        print(wrapup)
                        break
                    else:
                        set_avatar_state("thinking")
                        response = kernel.handle_command(user_input)
                        kernel.voice.speak(response)
                else:
                    set_avatar_state("listening")
                    command = input("zero-os (active)> ").strip()
                    if command:
                        if command.lower() in ["exit", "quit", "stop", "bye"]:
                            # v0.3: Clean shutdown with session save
                            wrapup = kernel.shutdown()
                            print(wrapup)
                            break
                        set_avatar_state("thinking")
                        response = kernel.handle_command(command)
                        kernel.voice.speak(response)
                    else:
                        print("Zero: Going to sleep.")
                        is_awake = False
                        
        except KeyboardInterrupt:
            print("\n[Zero] Emergency shutdown...")
            try:
                kernel.shutdown()
            except Exception:
                pass
            print("Zero: Goodbye Varun. Session saved.")
            break
        except Exception as e:
            print(f"\n[Error] System loop exception: {e}")
            try:
                kernel.state.record_error()
            except Exception:
                pass
            time.sleep(2)

    # Clean shut down when exiting loop
    try:
        import webview
        webview.destroy_window()
    except Exception:
        pass
    os._exit(0)

def main():
    clear_screen()
    print("=" * 60)
    print("            ZERO AUTONOMOUS OPERATING SYSTEM               ")
    print("             v0.3 — Intelligence Upgrade 🧠                ")
    print("=" * 60)
    print()
    print("  Modules: Brain | Memory | Goals | Planner | Reflection   ")
    print("  New: Decision Engine | State Tracker | Session Context   ")
    print()
    
    # Select Interaction Mode
    print("Select Mode:")
    print("1. Voice Mode (Speech Recognition + SAPI5 TTS)")
    print("2. Keyboard Mode (Terminal interface)")
    
    choice = input("\nEnter choice (1 or 2, default is 2): ").strip()
    voice_mode = (choice == "1")
    
    if voice_mode:
        print("\n[Mode] Voice Mode activated. Listening for wake word 'Zero'...")
    else:
        print("\n[Mode] Keyboard Mode activated. Type 'Zero' to wake up the system.")
    
    print("-" * 60)
    print("[GUI] Launching 3D Hologram desktop widget...")
    
    # Setup background loop thread
    os_thread = threading.Thread(target=run_os_thread, args=(voice_mode,), daemon=True)
    
    # Start webview GUI on the main thread
    start_avatar_gui(setup_callback=os_thread.start)

if __name__ == "__main__":
    main()
