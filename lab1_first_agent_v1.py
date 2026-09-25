"""
╔══════════════════════════════════════════════════════════════╗
║   LAB 1 — Build Your First AI Agent (Properly!)             ║
║   Agentic AI Training | Class 12                            ║
║   Duration: ~75 minutes                                     ║
╚══════════════════════════════════════════════════════════════╝

THE KEY QUESTION: What makes something an AGENT?

  A function call:   You call Claude → Claude answers → DONE.
                     You control everything. Claude just replies.

  An Agent:          Claude DECIDES what to do next.
                     Claude CALLS tools on its own.
                     Claude LOOPS until the goal is achieved.
                     YOU just give it a goal and wait.

This lab shows you the difference clearly, then builds up
to a real agent step by step.

PREREQUISITES:
  pip install anthropic

GET AN API KEY:
  1. Go to https://console.anthropic.com
  2. Create a free account → API Keys → Create Key
  3. Paste it below (replace "your-key-here")
"""

import anthropic
import json
import ast
import operator

# ──────────────────────────────────────────────────────────────
# ⚙️  SETUP
# ──────────────────────────────────────────────────────────────
API_KEY = "sk-ant-api03-"  # ← REPLACE THIS
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"


# ══════════════════════════════════════════════════════════════
#  PART 0 — NOT an Agent (just to show the difference)
# ══════════════════════════════════════════════════════════════
def part0_NOT_an_agent():
    """
    This is a NORMAL function call — NOT an agent.

    YOU (the programmer) call Claude.
    YOU decide what to ask.
    YOU do one thing, get one answer, stop.

    Claude has no loop. Claude has no tools. Claude cannot decide
    to do anything extra. It just answers and waits for you.

    This is like asking someone a question face-to-face —
    they answer, conversation ends.
    """
    print("\n" + "="*60)
    print("PART 0: Normal function call (NOT an agent)")
    print("="*60)

    # YOU call Claude with a fixed question
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[
            {"role": "user", "content": "What is 15 + 27?"}
        ]
    )

    # Claude answers and stops. No loop. No tools. No decisions.
    print("Claude answered:", response.content[0].text)
    print("\n💡 Notice:")
    print("   - YOU wrote the question in the code.")
    print("   - Claude answered it.")
    print("   - Nothing else happened.")
    print("   - This is NOT an agent. This is a function call.")


# ══════════════════════════════════════════════════════════════
#  PART 1 — The Tool (what the agent will USE)
# ══════════════════════════════════════════════════════════════

# ── 1a. Tool DESCRIPTION (what Claude reads) ─────────────────
#
# This is the JSON that tells Claude:
#   "There is a tool called 'calculator'.
#    It takes one input: 'expression' (a math string).
#    You can call it whenever you need to do math."
#
CALCULATOR_TOOL_DEFINITION = {
    "name": "calculator",
    "description": (
        "Evaluates a mathematical expression and returns the numeric result. "
        "Use this whenever you need to compute numbers precisely."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A math expression, e.g. '(15 + 27) * 3'"
            }
        },
        "required": ["expression"]
    }
}

# ── 1b. Tool IMPLEMENTATION (the actual Python function) ──────
#
# This is the code that ACTUALLY runs when Claude calls the tool.
# Claude CANNOT run Python. WE run it and send the result back.
#
def run_calculator(expression: str) -> str:
    """Safe math evaluator — supports +, -, *, /, **, %"""
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

        result = safe_eval(ast.parse(expression, mode='eval').body)
        if isinstance(result, float):
            result = round(result, 6)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# ══════════════════════════════════════════════════════════════
#  PART 2 — The Agent Loop (THIS is what makes it an agent)
# ══════════════════════════════════════════════════════════════
#
#  The agent loop runs like this:
#
#   ┌─────────────────────────────────────────────────────┐
#   │  1. Give the agent a GOAL (in natural language)     │
#   │  2. Claude THINKS: what should I do next?           │
#   │  3. If Claude wants a tool → WE run the tool        │
#   │  4. We send the tool RESULT back to Claude          │
#   │  5. Claude THINKS again with the new information    │
#   │  6. Repeat steps 2-5 until Claude says "I'm done"  │
#   └─────────────────────────────────────────────────────┘
#
#  KEY INSIGHT: WE only give a GOAL. Claude decides:
#    - whether to use a tool
#    - which tool to use
#    - what input to give the tool
#    - whether the goal is achieved yet
#
def run_agent(goal: str) -> str:
    """
    Runs the agent loop for a given goal.

    Args:
        goal: A natural language task, e.g.
              "Calculate the area of a circle with radius 7.
               Then find what percentage that is of a 10x10 square."

    Returns:
        Claude's final answer (a string).
    """
    print(f"\n{'='*60}")
    print(f"🎯 GOAL: {goal}")
    print(f"{'='*60}")

    # The conversation history. We start with the user's goal.
    # This list GROWS as the agent works — it IS the agent's memory.
    messages = [
        {"role": "user", "content": goal}
    ]

    step = 0

    # ── THE LOOP ──────────────────────────────────────────────
    while True:
        step += 1
        print(f"\n--- Agent Step {step} ---")

        # ── Ask Claude: what do you want to do next? ──────────
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[CALCULATOR_TOOL_DEFINITION],   # tell Claude what tools exist
            messages=messages                      # give Claude the full history
        )

        print(f"Claude's decision: stop_reason = '{response.stop_reason}'")

        # ── DECISION POINT: What did Claude decide? ───────────

        # CASE A: Claude says "end_turn" → goal is achieved, we're done
        if response.stop_reason == "end_turn":
            # Extract Claude's final text answer
            final_answer = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_answer = block.text

            print(f"\n✅ AGENT DONE after {step} step(s)")
            print(f"📢 Final Answer:\n{final_answer}")
            return final_answer

        # CASE B: Claude says "tool_use" → it wants to call a tool
        if response.stop_reason == "tool_use":

            # Step 2a: Add Claude's response to the conversation history
            # (important! Claude needs to see its own tool calls in history)
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Step 2b: Find every tool call in Claude's response
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":

                    # Claude decided to call this tool with these inputs:
                    tool_name  = block.name
                    tool_input = block.input
                    tool_id    = block.id   # unique ID for this call

                    print(f"\n🔧 Claude called tool: '{tool_name}'")
                    print(f"   Input Claude chose: {json.dumps(tool_input)}")

                    # Step 2c: WE run the tool (Claude cannot do this itself)
                    if tool_name == "calculator":
                        result = run_calculator(tool_input["expression"])
                    else:
                        result = f"Unknown tool: {tool_name}"

                    print(f"   Result we got:      {result}")

                    # Step 2d: Package the result to send back
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": tool_id,   # must match the call id!
                        "content":     result
                    })

            # Step 2e: Send results back to Claude so it can continue
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Now the loop repeats — Claude will think again with new info

        # Safety: stop if it takes too long
        if step >= 10:
            print("⚠️  Reached max steps. Stopping.")
            break

    return "Agent stopped."


# ══════════════════════════════════════════════════════════════
#  PART 3 — See the Agent in Action
# ══════════════════════════════════════════════════════════════
#
#  Each goal below shows a different aspect of agent behaviour.
#  Run them one at a time and observe what Claude decides to do.
#

def demo_single_tool_call():
    """
    Simple goal: Claude calls the calculator ONCE and answers.
    Shows the minimum agent loop: 2 steps (think → done).
    """
    print("\n" + "★"*60)
    print("DEMO 1: Single tool call")
    print("★"*60)

    run_agent("What is 1234 multiplied by 5678?")


def demo_multiple_tool_calls():
    """
    Claude needs to call the calculator MULTIPLE TIMES
    in sequence to achieve the goal.
    Shows: Claude deciding to call the tool more than once.
    """
    print("\n" + "★"*60)
    print("DEMO 2: Multiple tool calls in sequence")
    print("★"*60)

    run_agent(
        "I need to buy 3 items: a book for ₹450, a pen for ₹75, "
        "and a notebook for ₹120. "
        "Calculate the total cost, then calculate a 10% discount on that total, "
        "and finally tell me the final price after the discount."
    )


def demo_agent_decides_no_tool_needed():
    """
    Claude decides it does NOT need the calculator for this goal.
    Shows: the agent makes a decision — tool use is optional, not forced.
    """
    print("\n" + "★"*60)
    print("DEMO 3: Agent decides no tool is needed")
    print("★"*60)

    run_agent("What is the capital of France and why is it famous?")


def demo_multi_step_reasoning():
    """
    A complex goal that requires Claude to break it into
    steps and call the tool multiple times.
    Shows: planning + sequential tool use.
    """
    print("\n" + "★"*60)
    print("DEMO 4: Multi-step reasoning")
    print("★"*60)

    run_agent(
        "A cricket team scored 287 runs in 50 overs. "
        "Step 1: Calculate the run rate per over. "
        "Step 2: If they need to score 310 to win, how many more runs do they need? "
        "Step 3: They have 5 overs left. What run rate do they need in those 5 overs?"
    )


# ══════════════════════════════════════════════════════════════
#  PART 4 — CHALLENGE: Add YOUR OWN Tool
# ══════════════════════════════════════════════════════════════
"""
Now it's your turn!

TASK: Add a "text_length" tool that:
  - Takes a "text" input (a string)
  - Returns the number of characters and words in that text

STEP 1: Define the tool (copy the calculator definition as a template)
STEP 2: Write the run_text_length(text) function
STEP 3: Add it to the tools list in run_agent()
STEP 4: Add an elif block in the tool router inside run_agent()
STEP 5: Test with this goal:
  "Count the characters and words in the phrase:
   'Agentic AI is the future of software'
   Then calculate how many seconds it would take to read it
   at 200 words per minute."

TEMPLATE:

TEXT_LENGTH_TOOL = {
    "name": "text_length",
    "description": "Counts the number of characters and words in a text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to analyze"
            }
        },
        "required": ["text"]
    }
}

def run_text_length(text: str) -> str:
    chars = len(text)
    words = len(text.split())
    return f"Characters: {chars}, Words: {words}"
"""


# ──────────────────────────────────────────────────────────────
# ▶  MAIN — Run the demos
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 LAB 1 — Your First AI Agent")
    print("=" * 60)

    # Start here — see the difference between a function call and an agent:
    part0_NOT_an_agent()

    input("\n[Press Enter to continue to DEMO 1...]\n")
    demo_single_tool_call()

    input("\n[Press Enter to continue to DEMO 2...]\n")
    demo_multiple_tool_calls()

    input("\n[Press Enter to continue to DEMO 3...]\n")
    demo_agent_decides_no_tool_needed()

    input("\n[Press Enter to continue to DEMO 4...]\n")
    demo_multi_step_reasoning()

    print("\n\n🎉 Done! Now try the CHALLENGE in PART 4.")
