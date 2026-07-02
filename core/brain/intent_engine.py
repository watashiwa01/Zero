import re
import json
import requests

class IntentEngine:
    def __init__(self, model_name="qwen2.5", ollama_url="http://localhost:11434/api/chat"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.system_prompt = (
            "You are Zero, Varun's autonomous local operating system brain.\n"
            "Analyze the user input and convert it into a structured list of actions.\n"
            "Format your reply as a JSON object with three keys:\n"
            "1. 'intent': One of: 'single_action', 'multi_action'.\n"
            "2. 'actions': A list of action dictionaries, where each contains:\n"
            "   - 'action': 'open_app', 'close_app', 'store_memory', 'recall_memory', 'check_battery', 'check_wifi', 'create_folder', 'search_web', 'open_url', 'toggle_wifi', 'chat'.\n"
            "   - 'params': parameters for the action (e.g. {'app_name': 'chrome'} for 'open_app', {'content': 'exam is on Monday'} for 'store_memory', {'query': 'exam'} for 'recall_memory', {'url': 'google.com'} for 'open_url', {'state': 'on'} for 'toggle_wifi', or empty {}).\n"
            "   - 'response': A short text describing this action.\n"
            "3. 'response': A combined friendly conversational response to say to Varun.\n\n"
            "Example output:\n"
            "{\n"
            "  \"intent\": \"multi_action\",\n"
            "  \"actions\": [\n"
            "    {\"action\": \"open_app\", \"params\": {\"app_name\": \"chrome\"}, \"response\": \"Opening Google Chrome.\"},\n"
            "    {\"action\": \"store_memory\", \"params\": {\"content\": \"meeting at 5pm\"}, \"response\": \"Storing meeting memory.\"}\n"
            "  ],\n"
            "  \"response\": \"I'll open Chrome and remember the 5pm meeting for you, Varun.\"\n"
            "}\n\n"
            "Strictly return only valid JSON, without any markdown formatting wrappers."
        )

    def process_input(self, user_input):
        user_input_clean = user_input.strip()
        
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
            pass

        return self._rule_based_fallback(user_input_clean)

    def _clean_and_parse_json(self, json_str):
        try:
            cleaned = re.sub(r"^```(json)?\s*", "", json_str, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception:
            return None

    def _rule_based_fallback(self, text):
        # Match splitters case-insensitively but split on the original text to preserve casing
        splitters = [r"\s+and\s+then\s+", r"\s+then\s+", r"\s+and\s+", r"\s+next\s+", r"\s+&\s+"]
        combined_splitter = re.compile("|".join(splitters), re.IGNORECASE)
        
        segments = combined_splitter.split(text)
        segments = [s.strip() for s in segments if s.strip()]
        
        if len(segments) > 1:
            actions = []
            for seg in segments:
                parsed_action = self._parse_single_phrase(seg)
                if parsed_action:
                    actions.append(parsed_action)
            
            if actions:
                return {
                    "intent": "multi_action",
                    "actions": actions,
                    "response": f"Running {len(actions)} actions for you."
                }

        single_action = self._parse_single_phrase(text)
        if single_action:
            return {
                "intent": "single_action",
                "actions": [single_action],
                "response": single_action["response"]
            }

        return {
            "intent": "single_action",
            "actions": [{"action": "chat", "params": {}, "response": f"Let's chat about '{text}'."}],
            "response": f"I heard you say '{text}'. What can I do for you?"
        }

    def _parse_single_phrase(self, text):
        text_lower = text.lower().strip()
        
        # 1. Open URL/Website
        url_match = re.search(r"\b(?:open|go\s+to|visit)\s+([a-z0-9\-]+\.[a-z]{2,}(?:\/[^\s]*)?)", text_lower)
        if url_match:
            start, end = url_match.span(1)
            url = text[start:end].strip()
            return {
                "action": "open_url",
                "params": {"url": url},
                "response": f"Opening link: {url}."
            }

        # 2. Open Application
        open_match = re.search(r"\b(?:open|launch|start)\s+([a-z0-9\s\._\-]+)", text_lower)
        if open_match:
            start, end = open_match.span(1)
            app_name = text[start:end].strip()
            if "." in app_name and len(app_name.split(".")[-1]) >= 2:
                return {
                    "action": "open_url",
                    "params": {"url": app_name},
                    "response": f"Opening link: {app_name}."
                }
            return {
                "action": "open_app",
                "params": {"app_name": app_name},
                "response": f"Opening {app_name}."
            }
            
        # 3. Close Application
        close_match = re.search(r"\b(?:close|exit|stop|terminate)\s+([a-z0-9\s\._\-]+)", text_lower)
        if close_match:
            start, end = close_match.span(1)
            app_name = text[start:end].strip()
            return {
                "action": "close_app",
                "params": {"app_name": app_name},
                "response": f"Closing {app_name}."
            }

        # 4. Toggle Wi-Fi / Connection
        if "wifi" in text_lower or "wi-fi" in text_lower or "internet" in text_lower:
            if any(w in text_lower for w in ["turn on", "enable", "connect"]):
                return {
                    "action": "toggle_wifi",
                    "params": {"state": "on"},
                    "response": "Turning Wi-Fi on."
                }
            elif any(w in text_lower for w in ["turn off", "disable", "disconnect"]):
                return {
                    "action": "toggle_wifi",
                    "params": {"state": "off"},
                    "response": "Turning Wi-Fi off."
                }
            elif any(w in text_lower for w in ["check", "status", "show"]):
                return {
                    "action": "check_wifi",
                    "params": {},
                    "response": "Checking Wi-Fi status."
                }

        # 5. Search Web
        search_match = re.search(r"\b(?:search|google|find)\s+(?:for\s+)?(.+)", text_lower)
        if search_match:
            start, end = search_match.span(1)
            query = text[start:end].strip()
            return {
                "action": "search_web",
                "params": {"query": query},
                "response": f"Searching Google for '{query}'."
            }

        # 6. Store Memory
        if text_lower.startswith("remember that ") or text_lower.startswith("remember "):
            content = text[9:] if text_lower.startswith("remember ") else text[14:]
            if text_lower.startswith("remember that "):
                content = text[14:]
            return {
                "action": "store_memory",
                "params": {"content": content.strip()},
                "response": f"Saving memory: \"{content.strip()}\"."
            }

        # 7. Recall Memory
        if any(w in text_lower for w in ["what do i have", "recall", "remember", "memory"]):
            query = ""
            if "next week" in text_lower:
                query = "next week"
            elif "exam" in text_lower:
                query = "exam"
            elif "about" in text_lower:
                parts = text_lower.split("about", 1)
                if len(parts) > 1:
                    # Get index in original text to preserve casing
                    idx = text_lower.find("about") + len("about")
                    query = text[idx:].strip()
            return {
                "action": "recall_memory",
                "params": {"query": query.strip()},
                "response": f"Recalling memories about '{query.strip()}'."
            }

        # 8. Check Battery
        if "battery" in text_lower or "power" in text_lower:
            return {
                "action": "check_battery",
                "params": {},
                "response": "Checking battery status."
            }

        # 9. Create Folder
        create_folder_match = re.search(r"\bcreate\s+(?:folder|directory)\s+([a-z0-9\s\._\-\\]+)", text_lower)
        if create_folder_match:
            start, end = create_folder_match.span(1)
            folder_path = text[start:end].strip()
            return {
                "action": "create_folder",
                "params": {"folder_path": folder_path},
                "response": f"Creating folder: {folder_path}."
            }

        return None
