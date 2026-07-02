# Zero OS - Phase 1 (Milestone 1)

Zero is a personal autonomous operating system designed to learn how Varun works and help him achieve goals. This repository contains the foundation layer (v0.1).

## Repository Structure

```text
Zero/
├── core/
│   ├── brain.py       # Ollama LLM / intent fallback parsing
│   ├── memory.py      # SQLite memory manager
│   ├── planner.py     # Proactive suggestion generator
│   ├── goals.py       # Goal & task manager
│   └── kernel.py      # Main OS coordinator
│
├── agents/
│   ├── voice.py       # Speech recognition & Windows TTS
│   ├── system.py      # Windows app, battery, & Wi-Fi controls
│   └── browser.py     # Web browser links controller
│
├── data/
│   └── zero.db        # SQLite database (auto-generated)
│
├── tests/
│   └── test_zero.py   # Test suite
│
├── main.py            # Entry point script
└── requirements.txt   # Dependencies
```

## Features Supported in Milestone 1

1. **Wake Word "Zero":** Wakes up the assistant, triggering a `"Yes Varun?"` response.
2. **Open & Close Applications:** Works with Chrome, VS Code, Spotify, and generic Windows programs.
3. **Store & Recall Memories:** SQLite database saves facts permanently.
4. **Autonomous Planner:** Proactively reminds you if you haven't studied for goals (e.g. AI900) in 4 days.
5. **System Controls:** Check battery, network connectivity, and Wi-Fi state.

---

## Installation & Setup

1. **Clone or copy the files** to your preferred folder (e.g. `D:\ZERO OS`).
2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Ollama (Optional for local LLM processing):**
   * Download and install Ollama from [ollama.com](https://ollama.com).
   * Pull the default Qwen model:
     ```bash
     ollama pull qwen2.5
     ```
   * *Note: If Ollama is offline or not installed, the application falls back gracefully to a robust local rule-based intent parsing engine.*

---

## Running Zero OS

To run Zero:
```bash
python main.py
```

Choose:
* **Option 1 (Voice Mode):** Control Zero using your microphone. Say `"Zero"` to wake it up, followed by your command (e.g. `"Open Chrome"` or `"Remember that my ML exam is on Monday"`).
* **Option 2 (Keyboard Mode):** Type commands directly into the terminal prompt.
