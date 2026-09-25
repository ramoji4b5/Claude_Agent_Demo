"""
╔══════════════════════════════════════════════════════════════╗
║   LAB 2 — Smart Agent Web UI                                 ║
║   lab2_smart_agent.py + Gradio browser interface            ║
╚══════════════════════════════════════════════════════════════╝

Run: pip install anthropic gradio && python lab2_smart_agent_webui.py

WHAT'S NEW COMPARED TO lab1_agent_webui.py:
  ✓ 5 tools instead of 1  (search, calculator, notes, weather)
  ✓ Conversation memory    (agent remembers across turns)
  ✓ Notes panel            (see saved notes live)
  ✓ Reset button           (clear memory and start fresh)
  ✓ Each tool has its own icon so you can see what the agent chose
"""

import anthropic
import json
import ast
import operator
import gradio as gr
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# ⚙️  SETUP
# ──────────────────────────────────────────────────────────────
API_KEY = "sk-ant-api03-"
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"

# Icon shown in the chat for each tool
TOOL_ICONS = {
    "web_search":  "🔍",
    "calculator":  "🧮",
    "save_note":   "📝",
    "get_notes":   "📂",
    "get_weather": "🌤️",
}

SYSTEM_PROMPT = """You are a helpful personal assistant with access to several tools.
When given a task:
1. Break it into clear steps
2. Use your tools to gather information and compute results
3. Save important results using save_note so you can reference them later
4. Give a clear, concise final answer

Always show your reasoning before using a tool."""


# ══════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS  (the menu card Claude reads)
# ══════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the internet for information on any topic. Returns a summary of the top results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'Python programming language history'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "description": "Evaluate a mathematical expression and return the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression, e.g. '(15 * 3) + 200 / 4'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "save_note",
        "description": "Save an important piece of information to memory. Use this to remember facts, answers, or user preferences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":   {"type": "string", "description": "A short title for this note"},
                "content": {"type": "string", "description": "The information to save"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "get_notes",
        "description": "Retrieve all previously saved notes from memory.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_weather",
        "description": "Get the current weather and temperature for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Mumbai', 'Delhi', 'Bengaluru'"
                }
            },
            "required": ["city"]
        }
    },
]


# ══════════════════════════════════════════════════════════════
#  TOOL IMPLEMENTATIONS  (the actual Python functions)
# ══════════════════════════════════════════════════════════════

# ── Web Search (simulated) ───────────────────────────────────
KNOWLEDGE_BASE = {
    "python":           "Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. Famous for readable syntax, widely used in AI/ML, web development, and data science.",
    "ai":               "Artificial Intelligence (AI) is the simulation of human intelligence in computers. Modern AI uses neural networks and LLMs to understand and generate text, images, and code.",
    "agent":            "An AI agent perceives its environment, plans actions, uses tools, and pursues goals autonomously. Key parts: LLM brain, tools, memory, and a planning loop.",
    "langchain":        "LangChain is a Python framework for building AI applications. It provides abstractions for chains, agents, tools, and memory.",
    "anthropic":        "Anthropic is an AI safety company founded in 2021. They created Claude — a family of AI models known for being helpful, harmless, and honest.",
    "machine learning": "Machine Learning (ML) is a subset of AI where systems learn from data. Types: supervised, unsupervised, and reinforcement learning.",
    "india":            "India has a rapidly growing tech ecosystem with major hubs in Bengaluru, Hyderabad, Pune, and Delhi NCR. India produces 1.5 million engineering graduates annually.",
}

def run_web_search(query: str) -> str:
    query_lower = query.lower()
    for keyword, result in KNOWLEDGE_BASE.items():
        if keyword in query_lower:
            return f"Search results for '{query}':\n{result}"
    return (
        f"Search results for '{query}':\n"
        f"General information found. In production this connects to Google/Bing API or a vector database."
    )


# ── Calculator ───────────────────────────────────────────────
def run_calculator(expression: str) -> str:
    try:
        allowed_ops = {
            ast.Add:      operator.add,
            ast.Sub:      operator.sub,
            ast.Mult:     operator.mul,
            ast.Div:      operator.truediv,
            ast.Pow:      operator.pow,
            ast.USub:     operator.neg,
            ast.Mod:      operator.mod,
            ast.FloorDiv: operator.floordiv,
        }
        def safe_eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                return allowed_ops[type(node.op)](safe_eval(node.left), safe_eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                return allowed_ops[type(node.op)](safe_eval(node.operand))
            raise ValueError(f"Unsupported: {type(node)}")
        result = safe_eval(ast.parse(expression, mode="eval").body)
        if isinstance(result, float):
            result = round(result, 4)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculator error for '{expression}': {e}"


# ── Notes (in-memory store — persists across chat turns) ─────
notes_store: list[dict] = []

def run_save_note(title: str, content: str) -> str:
    note = {
        "id":       len(notes_store) + 1,
        "title":    title,
        "content":  content,
        "saved_at": datetime.now().strftime("%H:%M:%S"),
    }
    notes_store.append(note)
    return f"Note saved: '{title}'"

def run_get_notes() -> str:
    if not notes_store:
        return "No notes saved yet."
    lines = ["Saved Notes:"]
    for note in notes_store:
        lines.append(f"[{note['id']}] {note['title']} (saved {note['saved_at']})")
        lines.append(f"    {note['content']}")
    return "\n".join(lines)


# ── Weather (simulated) ──────────────────────────────────────
WEATHER_DB = {
    "mumbai":    {"temp": 31, "condition": "Humid and partly cloudy",     "humidity": 82},
    "delhi":     {"temp": 38, "condition": "Hot and sunny",               "humidity": 45},
    "bengaluru": {"temp": 24, "condition": "Pleasant with light breeze",  "humidity": 65},
    "chennai":   {"temp": 34, "condition": "Hot and humid",               "humidity": 78},
    "kolkata":   {"temp": 32, "condition": "Muggy with some clouds",      "humidity": 80},
    "pune":      {"temp": 26, "condition": "Mild and breezy",             "humidity": 60},
    "hyderabad": {"temp": 33, "condition": "Warm and sunny",              "humidity": 55},
    "london":    {"temp": 14, "condition": "Overcast and cool",           "humidity": 70},
    "new york":  {"temp": 22, "condition": "Clear and sunny",             "humidity": 50},
    "tokyo":     {"temp": 27, "condition": "Partly cloudy",               "humidity": 68},
}

def run_get_weather(city: str) -> str:
    key = city.lower().strip()
    if key in WEATHER_DB:
        w = WEATHER_DB[key]
        return (
            f"Weather in {city.title()}:\n"
            f"  Temperature: {w['temp']}°C\n"
            f"  Condition:   {w['condition']}\n"
            f"  Humidity:    {w['humidity']}%"
        )
    return f"Weather not available for '{city}'. Try: Mumbai, Delhi, Bengaluru, Chennai, London."


# ── Tool Router ──────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "web_search":
        return run_web_search(tool_input["query"])
    elif tool_name == "calculator":
        return run_calculator(tool_input["expression"])
    elif tool_name == "save_note":
        return run_save_note(tool_input["title"], tool_input["content"])
    elif tool_name == "get_notes":
        return run_get_notes()
    elif tool_name == "get_weather":
        return run_get_weather(tool_input["city"])
    return f"Unknown tool: {tool_name}"


# ══════════════════════════════════════════════════════════════
#  AGENT MEMORY
#  This list grows with every message — it IS the agent's memory.
#  It persists across chat turns until the user presses Reset.
# ══════════════════════════════════════════════════════════════
conversation_messages: list[dict] = []


# ══════════════════════════════════════════════════════════════
#  AGENT CHAT — streams step-by-step updates to the browser
# ══════════════════════════════════════════════════════════════
def agent_chat(message: str, history: list):
    """
    Runs the agent loop with all 5 tools.
    Uses `yield` to stream live updates to the Gradio chat UI.
    conversation_messages persists across calls (that's the memory).
    """
    # Add this message to the persistent memory
    conversation_messages.append({"role": "user", "content": message})

    step = 0
    response_text = ""

    while True:
        step += 1
        response_text += f"\n**Step {step}** — Thinking...\n"
        yield response_text

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversation_messages,
        )

        # ── DONE ─────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            final = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final = block.text

            # Save the assistant reply to memory
            conversation_messages.append({
                "role": "assistant",
                "content": response.content,
            })

            response_text += f"\n---\n{final}"
            yield response_text
            return

        # ── TOOL USE ──────────────────────────────────────────
        if response.stop_reason == "tool_use":
            # Save Claude's decision (with tool calls) to memory
            conversation_messages.append({
                "role": "assistant",
                "content": response.content,
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    icon   = TOOL_ICONS.get(block.name, "🔧")
                    name   = block.name
                    inputs = block.input

                    # Build a short human-readable label for what Claude chose
                    if name == "web_search":
                        label = f'search: "{inputs.get("query", "")}"'
                    elif name == "calculator":
                        label = f'`{inputs.get("expression", "")}`'
                    elif name == "save_note":
                        label = f'note: "{inputs.get("title", "")}"'
                    elif name == "get_notes":
                        label = "reading saved notes"
                    elif name == "get_weather":
                        label = f'weather in {inputs.get("city", "")}'
                    else:
                        label = json.dumps(inputs)

                    response_text += f"{icon} **{name}** — {label}\n"
                    yield response_text

                    # Run the tool and collect the result
                    result = execute_tool(name, inputs)

                    # Show a short preview of the result
                    preview = result[:150] + ("..." if len(result) > 150 else "")
                    response_text += f"   → {preview}\n"
                    yield response_text

                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result,
                    })

            # Send all tool results back to Claude and save to memory
            conversation_messages.append({
                "role": "user",
                "content": tool_results,
            })

        if step >= 15:
            response_text += "\n⚠️ Max steps reached."
            yield response_text
            return


def reset_agent():
    """Clear conversation memory and notes. Called by the Reset button."""
    conversation_messages.clear()
    notes_store.clear()
    return "Memory and notes cleared. Start a fresh conversation!"


def show_notes():
    """Show current notes. Called by the View Notes button."""
    return run_get_notes()


# ══════════════════════════════════════════════════════════════
#  EXAMPLE QUESTIONS
# ══════════════════════════════════════════════════════════════
EXAMPLES = [
    "Search for what AI agents are and save a note with the key points.",
    "Check the weather in Mumbai and Delhi. Which city is better for a weekend trip?",
    "I earn ₹12 LPA. Calculate my monthly salary and daily rate (22 working days). Save both results.",
    "A cricket team scored 287 in 50 overs. What's the run rate? They need 310 to win — how many more runs and what rate in the last 5 overs?",
    "Search for information about Anthropic, then calculate: if they have 500 employees and average salary is $200,000, what's the annual salary bill?",
    "Show me all the notes you've saved so far.",
]


# ══════════════════════════════════════════════════════════════
#  GRADIO WEB UI
# ══════════════════════════════════════════════════════════════
with gr.Blocks(title="Lab 2 — Smart Agent", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
# 🤖 Lab 2 — Smart Agent with Multiple Tools & Memory

This agent has **5 tools** and **remembers your conversation** across messages.

| Tool | What it does |
|------|-------------|
| 🔍 Web Search | Find information on any topic |
| 🧮 Calculator | Compute math precisely |
| 📝 Save Note  | Store facts for later |
| 📂 Get Notes  | Recall all saved notes |
| 🌤️ Weather    | Check weather for a city |

**Memory:** The agent remembers everything in this session. Use **Reset** to start fresh.
""")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.ChatInterface(
                fn=agent_chat,
                examples=EXAMPLES,
                title="",
                description="Ask anything — the agent picks the right tool(s) automatically.",
            )

        with gr.Column(scale=1):
            gr.Markdown("### 🗂️ Session Controls")

            notes_output = gr.Textbox(
                label="📝 Saved Notes",
                lines=12,
                interactive=False,
                placeholder="Notes saved by the agent will appear here...",
            )

            view_btn = gr.Button("📂 View Notes", variant="secondary")
            reset_btn = gr.Button("🔄 Reset Memory + Notes", variant="stop")
            reset_status = gr.Textbox(label="Status", interactive=False, lines=1)

            view_btn.click(fn=show_notes, outputs=notes_output)
            reset_btn.click(fn=reset_agent, outputs=reset_status)

    gr.Markdown("""
---
**Tip:** Try a multi-turn conversation:
1. Ask: *"Search for Python and save a note"*
2. Then ask: *"Show me all notes"*
3. Then ask: *"What was the Python fact you saved?"*

Watch the agent use its memory across all three turns!
""")


if __name__ == "__main__":
    demo.launch(
        share=False,
        show_error=True,
    )
