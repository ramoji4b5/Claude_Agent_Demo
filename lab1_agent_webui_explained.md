# Lab 1 — AI Agent Web UI Explained
### For Class 12 Students

---

## What Is This File?

`lab1_agent_webui.py` takes the AI Agent we built in `lab1_first_agent_v1.py` and gives it a **web browser interface** so anyone can chat with the agent — no coding needed to use it!

Instead of running in a terminal, the agent now runs inside a **chat window in your browser**, just like WhatsApp Web or ChatGPT.

---

## What New Library Does It Use?

```python
import gradio as gr
```

**Gradio** is a Python library that lets you build simple web apps for AI models in just a few lines. You don't need to know HTML, CSS, or JavaScript.

Install it with:
```
pip install gradio
```

---

## How the File is Structured

```
lab1_agent_webui.py
│
├── Setup (API key, model, client)
├── CALCULATOR_TOOL_DEFINITION  ← same as lab1
├── run_calculator()            ← same as lab1
├── agent_chat()                ← NEW: connects agent to the web UI
├── EXAMPLES                    ← sample questions shown on screen
└── Gradio UI setup             ← builds and launches the web page
```

---

## Part 1 — Setup (Lines 12–14)

```python
API_KEY = "sk-ant-..."
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"
```

Same as before — connects to Claude using your API key.

---

## Part 2 — Calculator Tool (Lines 16–62)

Exactly the same as `lab1_first_agent_v1.py`:
- `CALCULATOR_TOOL_DEFINITION` tells Claude a calculator tool exists
- `run_calculator()` is the actual Python code that does the math

> **Key reminder:** Claude cannot run Python. WE run the calculator and send the result back.

---

## Part 3 — The `agent_chat()` Function (Lines 65–119)

This is the **most important new part**. It connects the agent loop to the web UI.

```python
def agent_chat(message: str, history: list) -> str:
```

### What the parameters mean:
| Parameter | What it is |
|---|---|
| `message` | The question the user typed in the chat box |
| `history` | All previous messages in the chat (Gradio handles this automatically) |

### How it works — step by step:

```
User types a question in the browser
        ↓
agent_chat() is called with that message
        ↓
The agent loop starts (same loop from lab1)
        ↓
Each step: it sends an update to the browser using `yield`
        ↓
If Claude calls the calculator → shows: 🔧 Calculator: expression → result
        ↓
When Claude is done → shows the final answer
```

### What is `yield`?

Instead of `return` (which gives one answer at the end), `yield` **sends partial updates** as the agent works. This lets the user **watch the agent think in real time**, step by step.

```python
response_text += f"\n**Step {step}** — Thinking...\n"
yield response_text   # ← sends this to the browser immediately
```

Think of `yield` like a live cricket scorecard — it updates after every ball, not just at the end of the match.

---

## Part 4 — Example Questions (Lines 122–128)

```python
EXAMPLES = [
    "What is 1234 multiplied by 5678?",
    "What is the capital of France and why is it famous?",
    ...
]
```

These are **ready-made questions** shown as clickable buttons on the web page so users can try the agent quickly without typing.

---

## Part 5 — Building the Web UI (Lines 130–152)

```python
with gr.Blocks(title="Lab 1 — AI Agent Demo") as demo:
    gr.Markdown("# 🤖 Lab 1 — AI Agent Demo ...")

    chatbot = gr.ChatInterface(
        fn=agent_chat,
        examples=EXAMPLES,
        ...
    )

demo.launch(share=False, show_error=True, theme=gr.themes.Soft())
```

### What each part does:

| Code | What it does |
|---|---|
| `gr.Blocks()` | Creates a blank web page |
| `gr.Markdown()` | Adds formatted text / headings to the page |
| `gr.ChatInterface(fn=agent_chat)` | Creates a full chat UI that calls `agent_chat()` when user sends a message |
| `demo.launch()` | Starts the web server and opens the browser |

### What `share=False` means:
- `share=False` → only works on **your computer** (localhost)
- `share=True` → creates a **public link** anyone on the internet can use (useful for demos)

---

## The Difference: lab1 vs lab1_webui

| Feature | lab1_first_agent_v1.py | lab1_agent_webui.py |
|---|---|---|
| Interface | Terminal / command line | Web browser chat UI |
| How you see output | `print()` statements | Live updates via `yield` |
| Who can use it | Only you (by running Python) | Anyone (just open the link) |
| New library needed | No | Yes — Gradio |
| Agent logic | Same | Same |

---

## How to Run It

```bash
pip install gradio anthropic
python lab1_agent_webui.py
```

Then open your browser and go to: `http://localhost:7860`

---

## What You Will See in the Browser

```
╔══════════════════════════════════════════╗
║  🤖 Lab 1 — AI Agent Demo               ║
║                                          ║
║  [Type your question here...]  [Send]    ║
║                                          ║
║  Example questions (click to try):       ║
║  • What is 1234 × 5678?                  ║
║  • Capital of France?                    ║
║  • Cricket run rate problem              ║
╚══════════════════════════════════════════╝
```

When you ask a math question, you'll see something like:

```
Step 1 — Thinking...
🔧 Calculator: 450 + 75 + 120 → 645
Step 2 — Thinking...
🔧 Calculator: 645 * 0.10 → 64.5
Step 3 — Thinking...
🔧 Calculator: 645 - 64.5 → 580.5

The total cost is ₹645. After a 10% discount of ₹64.50,
the final price is ₹580.50.
```

---

## Key Concepts Summary

| Concept | Simple Explanation |
|---|---|
| **Gradio** | A library that turns Python functions into web apps |
| **`yield`** | Sends live updates to the browser as the agent works |
| **`gr.ChatInterface`** | A ready-made chat window — just pass your function |
| **`demo.launch()`** | Starts the web server so you can open it in a browser |
| **Agent loop** | Same as lab1 — Claude thinks, calls tools, thinks again |

---

## The Big Picture

```
lab1_first_agent_v1.py   →   Core agent logic (terminal)
         +
   Gradio library         →   Wraps it in a browser chat UI
         =
lab1_agent_webui.py      →   Same agent, now anyone can use it!
```

The agent logic did NOT change. Gradio just gave it a friendly face.
