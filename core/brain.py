import requests
import json
import re

class BrainAgent:
    def __init__(self, model_name="qwen2.5", ollama_url="http://localhost:11434/api/chat"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.system_prompt = (
            "You are Zero, Varun's autonomous local operating system. "
            "You help Varun manage his local machine, organize memories, track tasks, and accomplish goals.\n"
            "Format your reply as a JSON object with three keys:\n"
            "1. 'action': The category of request. One of: 'open_app', 'close_app', 'store_memory', 'recall_memory', 'check_battery', 'check_wifi', 'create_folder', 'chat'.\n"
            "2. 'params': A dictionary of parameters for the action (e.g. {'app_name': 'chrome'} for 'open_app', {'content': 'exam is on Monday'} for 'store_memory', {'query': 'exam'} for 'recall_memory', {'folder_path': 'path'} for 'create_folder', or empty {}).\n"
            "3. 'response': A conversational text reply to tell Varun.\n\n"
            "Example outputs:\n"
            '{"action": "open_app", "params": {"app_name": "chrome"}, "response": "Opening Google Chrome."}\n'
            '{"action": "store_memory", "params": {"content": "Varun\'s ML exam is on Monday"}, "response": "I\'ve saved that memory for you."}\n'
            '{"action": "recall_memory", "params": {"query": "exam"}, "response": "Let me look up your exams."}\n'
            '{"action": "chat", "params": {}, "response": "Hello Varun! How can I help you today?"}\n\n'
            "Strictly return only valid JSON, without any markdown formatting wrappers."
        )

    def process_input(self, user_input):
        user_input_clean = user_input.strip()
        
        # 1. Attempt local Ollama generation
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input_clean}
                ],
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "").strip()
                parsed = self._clean_and_parse_json(content)
                if parsed:
                    return parsed
        except Exception:
            # Fall through to rule-based fallback if Ollama is offline or requests timeout
            pass

        # 2. Rule-Based Fallback Engine (Runs locally, fast, 100% reliable)
        return self._rule_based_fallback(user_input_clean)

    def _clean_and_parse_json(self, json_str):
        try:
            # Remove markdown code block surrounds if present
            cleaned = re.sub(r"^```(json)?\s*", "", json_str, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception:
            return None

    def _rule_based_fallback(self, text):
        text_lower = text.lower()
        
        # Open Application rule
        open_match = re.search(r"\b(open|launch|start)\s+([a-z0-9\s\._\-]+)", text_lower)
        if open_match:
            app_name = open_match.group(2).strip()
            return {
                "action": "open_app",
                "params": {"app_name": app_name},
                "response": f"Opening {app_name}."
            }
            
        # Close Application rule
        close_match = re.search(r"\b(close|exit|stop|terminate)\s+([a-z0-9\s\._\-]+)", text_lower)
        if close_match:
            app_name = close_match.group(2).strip()
            return {
                "action": "close_app",
                "params": {"app_name": app_name},
                "response": f"Closing {app_name}."
            }

        # Store Memory rules
        # "remember that <content>"
        if text_lower.startswith("remember that ") or text_lower.startswith("remember "):
            content = text[9:] if text_lower.startswith("remember ") else text[14:]
            if text_lower.startswith("remember that "):
                content = text[14:]
            return {
                "action": "store_memory",
                "params": {"content": content.strip()},
                "response": f"Stored memory: \"{content.strip()}\""
            }

        # Recall Memory rules
        # "what do i have...", "do you remember...", "recall..."
        if "what do i have" in text_lower or "recall" in text_lower or "remember" in text_lower or "memory" in text_lower:
            # Extract possible query keywords
            query = ""
            if "next week" in text_lower:
                query = "next week"
            elif "exam" in text_lower:
                query = "exam"
            elif "about" in text_lower:
                parts = text_lower.split("about", 1)
                if len(parts) > 1:
                    query = parts[1].strip()
            
            return {
                "action": "recall_memory",
                "params": {"query": query.strip()},
                "response": "Searching memory..."
            }

        # Check Battery rule
        if "battery" in text_lower or "power" in text_lower:
            return {
                "action": "check_battery",
                "params": {},
                "response": "Checking battery status."
            }

        # Check Wi-Fi / Internet rule
        if "wifi" in text_lower or "wi-fi" in text_lower or "internet" in text_lower or "connection" in text_lower:
            return {
                "action": "check_wifi",
                "params": {},
                "response": "Checking connection status."
            }

        # Create Folder rule
        create_folder_match = re.search(r"\bcreate\s+(?:folder|directory)\s+([a-z0-9\s\._\-\\]+)", text_lower)
        if create_folder_match:
            folder_path = create_folder_match.group(1).strip()
            return {
                "action": "create_folder",
                "params": {"folder_path": folder_path},
                "response": f"Creating folder: {folder_path}."
            }

        # Default chat fallback
        return {
            "action": "chat",
            "params": {},
            "response": f"I heard you say: '{text}'. What would you like me to do with that?"
        }
