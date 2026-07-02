import random

class PersonalityManager:
    def __init__(self):
        pass

    def get_system_prompt_addition(self):
        return (
            "\nPersonality rules:\n"
            "- Always call the user 'Varun'.\n"
            "- Maintain a helpful, intelligent, proactive tone.\n"
            "- Anticipate Varun's next steps and offer suggestions."
        )

    def enhance_response(self, response_text, action_type=None, params=None, context=None):
        if not response_text:
            return "Yes, Varun?"
            
        enhanced = response_text
        
        # Ensure Varun is addressed if not already present
        if "varun" not in enhanced.lower():
            greetings = ["Certainly, Varun. ", "Of course, Varun. ", "Done, Varun. "]
            if action_type in ["open_app", "close_app", "create_folder", "store_memory"]:
                enhanced = random.choice(greetings) + enhanced
            else:
                if enhanced.endswith("."):
                    enhanced = enhanced[:-1] + ", Varun."
                else:
                    enhanced = enhanced + ", Varun."

        # Proactive Action-Specific Additions
        if action_type == "open_app":
            app_name = params.get("app_name", "").lower() if params else ""
            if "chrome" in app_name:
                enhanced += " Would you like me to open your usual ML study tabs or search for something?"
            elif "spotify" in app_name:
                enhanced += " Playing some music to help you focus."
            elif "code" in app_name or "vscode" in app_name:
                enhanced += " Ready to write some code! Which project are we working on?"
                
        elif action_type == "check_battery":
            if context and "battery_percent" in context:
                percent = context["battery_percent"]
                plugged = context.get("power_plugged", True)
                if percent < 20 and not plugged:
                    enhanced += " Varun, your battery is running quite low. I recommend connecting your charger or closing power-heavy apps."

        elif action_type == "check_wifi":
            if context and context.get("internet_status") == "offline":
                enhanced += " Since you are offline, would you like me to run 'turn on wifi' to reconnect?"

        elif action_type == "store_memory":
            enhanced += " I will recall this whenever you ask about it."

        return enhanced
