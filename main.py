import sys
import os
import time

# Ensure directory is on PATH so relative package imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.kernel import ZeroKernel

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("=" * 60)
    print("                 ZERO AUTONOMOUS OPERATING SYSTEM             ")
    print("                     Milestone 1 - Foundation                 ")
    print("=" * 60)
    
    # Initialize the Zero Kernel
    print("[Kernel] Starting kernel components...")
    kernel = ZeroKernel()
    print("[Kernel] Database, Brain, Planner, and System Agents initialized.")
    print("=" * 60)
    
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
        print("Note: In Keyboard Mode, you can also type commands directly!")
    
    print("-" * 60)
    
    # Proactive Suggestion check on boot
    boot_suggestion = kernel.get_proactive_suggestion()
    if boot_suggestion:
        time.sleep(1)
        print("\n[Proactive Planner]")
        kernel.voice.speak(boot_suggestion)
        print("-" * 60)

    is_awake = False
    
    while True:
        try:
            if voice_mode:
                if not is_awake:
                    # Passive listening for wake word
                    text = kernel.voice.listen_for_speech(timeout=8).lower()
                    if "zero" in text:
                        is_awake = True
                        kernel.voice.speak("Yes Varun?")
                else:
                    # Active command listening
                    command = kernel.voice.listen_for_speech(timeout=6)
                    if command:
                        if command.lower() in ["stop", "exit", "bye"]:
                            kernel.voice.speak("Goodbye Varun.")
                            break
                        
                        response = kernel.handle_command(command)
                        kernel.voice.speak(response)
                    else:
                        # Go back to sleep if no audio is heard/processed
                        kernel.voice.speak("Going to sleep.")
                        is_awake = False
            else:
                # Keyboard Mode
                if not is_awake:
                    user_input = input("\nzero-os> ").strip()
                    if not user_input:
                        continue
                    
                    if user_input.lower() == "zero":
                        is_awake = True
                        print("Zero: Yes Varun? (Awaiting command...)")
                    elif user_input.lower() in ["exit", "quit", "stop", "bye"]:
                        print("Zero: Goodbye Varun.")
                        break
                    else:
                        # Allow direct command execution in keyboard mode
                        response = kernel.handle_command(user_input)
                        print(f"Zero: {response}")
                else:
                    command = input("zero-os (active)> ").strip()
                    if command:
                        if command.lower() in ["exit", "quit", "stop", "bye"]:
                            print("Zero: Goodbye Varun.")
                            break
                        response = kernel.handle_command(command)
                        print(f"Zero: {response}")
                    else:
                        # Return to passive mode if enter is pressed on empty input
                        print("Zero: Going to sleep.")
                        is_awake = False

        except KeyboardInterrupt:
            print("\nZero: Shutting down. Goodbye Varun.")
            break
        except Exception as e:
            print(f"\n[Error] System loop exception: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
