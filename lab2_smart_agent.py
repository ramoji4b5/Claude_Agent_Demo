"""
╔══════════════════════════════════════════════════════════════╗
║   LAB 2 — Smart Agent with Multiple Tools & Memory          ║
║   Agentic AI Training | Class 12                            ║
║   Duration: ~75 minutes                                     ║
╚══════════════════════════════════════════════════════════════╝

WHAT YOU WILL BUILD:
  A personal assistant agent with FOUR tools:
    🔍 Web-search simulator     — find information
    🧮 Calculator               — do math
    📝 Note-taker               — save & recall notes (memory!)
    🌤️  Weather checker          — get weather info (simulated)

  The agent keeps a MEMORY of the conversation so it can
  reference earlier answers in later steps.

LEARNING GOALS:
  ✓ Multiple tools in one agent
  ✓ Conversation memory (message history)
  ✓ Tool routing (deciding which tool to call)
  ✓ Clean agent architecture
  ✓ Real-world agent pattern you can extend
"""

import anthropic
import json
import ast
import operator
from datetime import datetime
from typing import Any

# ──────────────────────────────────────────────────────────────
# ⚙️  SETUP
# ──────────────────────────────────────────────────────────────
API_KEY = "sk-ant-api03-"  # ← REPLACE THIS
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"


# ══════════════════════════════════════════════════════════════
#  SECTION A — TOOL DEFINITIONS
#  (These describe each tool so the AI knows what it can call)
# ══════════════════════════════════════════════════════════════

TOOLS = [
    # ── TOOL 1: Web Search (simulated) ──────────────────────
    {
        "name": "web_search",
        "description": (
            "Search the internet for information on any topic. "
            "Returns a summary of the top results."
        ),
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

    # ── TOOL 2: Calculator ───────────────────────────────────
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

    # ── TOOL 3: Save Note (memory!) ──────────────────────────
    {
        "name": "save_note",
        "description": (
            "Save an important piece of information to memory. "
            "Use this to remember facts, answers, or user preferences."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A short title for this note, e.g. 'Cricket run rate'"
                },
                "content": {
                    "type": "string",
                    "description": "The information to save"
                }
            },
            "required": ["title", "content"]
        }
    },

    # ── TOOL 4: Get Notes ────────────────────────────────────
    {
        "name": "get_notes",
        "description": "Retrieve all previously saved notes from memory.",
        "input_schema": {
            "type": "object",
            "properties": {}   # No inputs needed
        }
    },

    # ── TOOL 5: Get Weather (simulated) ─────────────────────
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
#  SECTION B — TOOL IMPLEMENTATIONS
#  (The actual functions that run when Claude calls a tool)
# ══════════════════════════════════════════════════════════════

# ── B1: Web Search (simulated with preset answers) ───────────
KNOWLEDGE_BASE = {
    "python": "Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. It's famous for its simple, readable syntax and is widely used in AI/ML, web development, and data science.",
    "ai": "Artificial Intelligence (AI) is the simulation of human intelligence in computers. Modern AI uses neural networks and large language models (LLMs) to understand and generate text, images, and code.",
    "agent": "An AI agent is a system that perceives its environment, plans actions, uses tools, and pursues goals autonomously. Key components: LLM brain, tools, memory, and a planning loop.",
    "langchain": "LangChain is a Python framework for building AI applications and agents. It provides abstractions for chains, agents, tools, and memory.",
    "anthropic": "Anthropic is an AI safety company founded in 2021. They created the Claude family of AI models, known for being helpful, harmless, and honest.",
    "machine learning": "Machine Learning (ML) is a subset of AI where systems learn from data. Types: supervised (labeled data), unsupervised (unlabeled), and reinforcement (reward signals).",
    "india": "India has a rapidly growing tech ecosystem with major hubs in Bengaluru, Hyderabad, Pune, and Delhi NCR. India produces 1.5 million engineering graduates annually.",
}

def run_web_search(query: str) -> str:
    """Simulated web search — in a real agent, you'd call Google/Bing API."""
    query_lower = query.lower()
    for keyword, result in KNOWLEDGE_BASE.items():
        if keyword in query_lower:
            return f"Search results for '{query}':\n{result}"
    # Generic fallback
    return (
        f"Search results for '{query}':\n"
        f"Found general information: '{query}' is a topic with many resources available. "
        f"In a production agent, this would connect to Google Search API, "
        f"Wikipedia API, or a vector database of documents."
    )


# ── B2: Calculator ───────────────────────────────────────────
def run_calculator(expression: str) -> str:
    """Safe math evaluator — handles +, -, *, /, **, %."""
    try:
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.Mod: operator.mod,
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

        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        # Round floats to 4 decimal places for readability
        if isinstance(result, float):
            result = round(result, 4)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculator error for '{expression}': {str(e)}"


# ── B3 & B4: Notes (in-memory store) ────────────────────────
# This is our agent's "memory" — a simple list of dicts.
# In a real agent, this would be stored in a database.
notes_store: list[dict] = []

def run_save_note(title: str, content: str) -> str:
    """Save a note to our in-memory store."""
    note = {
        "id": len(notes_store) + 1,
        "title": title,
        "content": content,
        "saved_at": datetime.now().strftime("%H:%M:%S")
    }
    notes_store.append(note)
    return f"✅ Note saved: '{title}'"


def run_get_notes() -> str:
    """Return all saved notes."""
    if not notes_store:
        return "No notes saved yet."
    lines = ["📝 Saved Notes:"]
    for note in notes_store:
        lines.append(f"\n[{note['id']}] {note['title']} (saved {note['saved_at']})")
        lines.append(f"    {note['content']}")
    return "\n".join(lines)


# ── B5: Weather (simulated) ──────────────────────────────────
WEATHER_DB = {
    "mumbai":    {"temp": 31, "condition": "Humid and partly cloudy", "humidity": 82},
    "delhi":     {"temp": 38, "condition": "Hot and sunny",           "humidity": 45},
    "bengaluru": {"temp": 24, "condition": "Pleasant with light breeze","humidity": 65},
    "chennai":   {"temp": 34, "condition": "Hot and humid",           "humidity": 78},
    "kolkata":   {"temp": 32, "condition": "Muggy with some clouds",  "humidity": 80},
    "pune":      {"temp": 26, "condition": "Mild and breezy",         "humidity": 60},
    "hyderabad": {"temp": 33, "condition": "Warm and sunny",          "humidity": 55},
    "london":    {"temp": 14, "condition": "Overcast and cool",       "humidity": 70},
    "new york":  {"temp": 22, "condition": "Clear and sunny",         "humidity": 50},
    "tokyo":     {"temp": 27, "condition": "Partly cloudy",           "humidity": 68},
}

def run_get_weather(city: str) -> str:
    """Return simulated weather for a city."""
    key = city.lower().strip()
    if key in WEATHER_DB:
        w = WEATHER_DB[key]
        return (
            f"🌤️ Weather in {city.title()}:\n"
            f"   Temperature: {w['temp']}°C\n"
            f"   Condition:   {w['condition']}\n"
            f"   Humidity:    {w['humidity']}%"
        )
    return f"Weather data not available for '{city}'. Try: Mumbai, Delhi, Bengaluru, Chennai, London."


# ══════════════════════════════════════════════════════════════
#  SECTION C — TOOL ROUTER
#  (Decides which function to call based on tool name)
# ══════════════════════════════════════════════════════════════

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Route a tool call to the correct implementation.
    This is called every time Claude decides to use a tool.
    """
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
    else:
        return f"Unknown tool: {tool_name}"


# ══════════════════════════════════════════════════════════════
#  SECTION D — THE AGENT
#  (The main class that wraps everything together)
# ══════════════════════════════════════════════════════════════

class SmartAgent:
    """
    A multi-tool AI agent with persistent conversation memory.
    
    Architecture:
      ┌─────────────────────────────────────┐
      │           SmartAgent                │
      │                                     │
      │  messages[]  ← conversation memory  │
      │  tools[]     ← available tools      │
      │                                     │
      │  run(goal)                          │
      │    └── Agent Loop:                  │
      │          Think → Act → Observe      │
      │          Repeat until done          │
      └─────────────────────────────────────┘
    """

    SYSTEM_PROMPT = """You are a helpful personal assistant with access to several tools.
When given a task:
1. Break it into clear steps
2. Use your tools to gather information and compute results
3. Save important results using save_note so you can reference them later
4. Give a clear, concise final answer

Always show your reasoning before using a tool."""

    def __init__(self, name: str = "SmartAgent"):
        self.name = name
        self.messages: list[dict] = []   # ← This IS the agent's memory!

    def reset(self):
        """Clear conversation memory — start fresh."""
        self.messages = []
        notes_store.clear()
        print(f"🔄 {self.name} memory cleared.")

    def run(self, user_message: str, verbose: bool = True) -> str:
        """
        Run the agent on a user message.
        
        This is the AGENT LOOP:
          While not done:
            1. Call the LLM (Claude)
            2. If tool_use → run the tool, add result to messages
            3. If end_turn → return final answer
        """
        print(f"\n{'='*60}")
        print(f"👤 User: {user_message}")
        print(f"{'='*60}")

        # Add user message to memory
        self.messages.append({"role": "user", "content": user_message})

        step = 0

        while True:
            step += 1
            if verbose:
                print(f"\n[Step {step}] Thinking...")

            # ── Call Claude ──────────────────────────────────
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=self.SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages
            )

            if verbose:
                print(f"         Stop reason: {response.stop_reason}")

            # ── DONE: Claude finished ────────────────────────
            if response.stop_reason == "end_turn":
                # Extract text from the last response
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text = block.text

                # Add to memory so future messages can reference it
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                print(f"\n{'─'*60}")
                print(f"🤖 {self.name}: {final_text}")
                print(f"{'─'*60}")
                return final_text

            # ── TOOL USE: Claude wants to call a tool ────────
            if response.stop_reason == "tool_use":
                # Add Claude's response (with tool calls) to memory
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Process all tool calls in this response
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if verbose:
                            print(f"\n[Step {step}] 🔧 Tool call: {block.name}")
                            print(f"            Input: {json.dumps(block.input)}")

                        # ── Execute the tool ─────────────────
                        result = execute_tool(block.name, block.input)

                        if verbose:
                            # Show first 200 chars of result
                            preview = result[:200] + ("..." if len(result) > 200 else "")
                            print(f"            Result: {preview}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,  # Must match the call!
                            "content": result
                        })

                # Send all tool results back to Claude
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

            # Safety stop
            if step >= 15:
                print("⚠️  Max steps reached. Stopping.")
                break

        return "Agent stopped after maximum steps."


# ══════════════════════════════════════════════════════════════
#  SECTION E — DEMO SCENARIOS
#  (Run these to see the agent in action)
# ══════════════════════════════════════════════════════════════

def demo_1_research_and_calculate():
    """
    The agent searches for info about Python and then does math.
    Shows: multi-tool use, sequential reasoning.
    """
    print("\n" + "★"*60)
    print("DEMO 1: Research + Calculate")
    print("★"*60)

    agent = SmartAgent("ResearchBot")

    # Turn 1: Research
    agent.run("Search for information about Python programming language and save the key points.")

    # Turn 2: Multi-step math (agent remembers the previous answer!)
    agent.run(
        "If a Python developer earns ₹12 LPA (lakhs per year), "
        "calculate their monthly salary and daily rate (assuming 22 working days). "
        "Save these results."
    )

    # Turn 3: Reference earlier info
    agent.run("Show me all the notes you've saved so far.")


def demo_2_weather_planning():
    """
    The agent checks weather for multiple cities and plans a trip.
    Shows: multiple tool calls in one turn, decision making.
    """
    print("\n" + "★"*60)
    print("DEMO 2: Weather-based Trip Planning")
    print("★"*60)

    agent = SmartAgent("TravelBot")
    agent.run(
        "I'm planning a weekend trip from Delhi. "
        "Check the weather in Mumbai and Bengaluru. "
        "Which one has better weather right now? "
        "Also calculate how much a flight at ₹4500 each way costs for 2 people."
    )


def demo_3_study_assistant():
    """
    A study assistant that takes notes and answers questions.
    Shows: memory across multiple turns.
    """
    print("\n" + "★"*60)
    print("DEMO 3: Study Assistant (Multi-turn Memory)")
    print("★"*60)

    agent = SmartAgent("StudyBot")

    agent.run("Search for what AI agents are and save the definition.")
    agent.run("Now search for LangChain and save what it's used for.")
    agent.run(
        "I have 3 months to study AI. If I study 2 hours per day, "
        "how many total hours will I study? Save this as a note."
    )
    agent.run(
        "Based on everything you've learned and saved, "
        "give me a 3-point summary of what I should focus on first."
    )


def demo_4_interactive():
    """
    Interactive mode — type your own questions!
    """
    print("\n" + "★"*60)
    print("DEMO 4: Interactive Mode — Talk to the Agent!")
    print("★"*60)
    print("Type your questions. Type 'quit' to exit, 'reset' to clear memory.\n")

    agent = SmartAgent("PersonalAssistant")

    while True:
        user_input = input("\n👤 You: ").strip()

        if not user_input:
            continue
        if user_input.lower() == 'quit':
            print("Goodbye! 👋")
            break
        if user_input.lower() == 'reset':
            agent.reset()
            continue

        agent.run(user_input)


# ══════════════════════════════════════════════════════════════
#  MAIN — Choose which demo to run
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🤖 LAB 2 — Smart Multi-Tool Agent")
    print("=" * 60)
    print("Available demos:")
    print("  1 — Research + Calculate (automated)")
    print("  2 — Weather Trip Planner (automated)")
    print("  3 — Study Assistant with memory (automated)")
    print("  4 — Interactive mode (type your own questions)")
    print()

    choice = input("Which demo? (1/2/3/4): ").strip()

    if choice == "1":
        demo_1_research_and_calculate()
    elif choice == "2":
        demo_2_weather_planning()
    elif choice == "3":
        demo_3_study_assistant()
    elif choice == "4":
        demo_4_interactive()
    else:
        print("Running Demo 1 by default...")
        demo_1_research_and_calculate()
