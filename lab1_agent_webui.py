"""
Web UI for Lab 1 AI Agent
Run: pip install gradio && python lab1_agent_webui.py
"""

import anthropic
import json
import ast
import operator
import gradio as gr

API_KEY = "sk-ant-api03-"
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"

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


def agent_chat(message: str, history: list) -> str:
    """
    Runs the agent loop and yields step-by-step updates to the chat UI.
    Each yield shows accumulated progress so the user can watch the agent think.
    """
    messages = [{"role": "user", "content": message}]
    step = 0
    response_text = ""

    while True:
        step += 1
        response_text += f"\n**Step {step}** — Thinking...\n"
        yield response_text

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[CALCULATOR_TOOL_DEFINITION],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final = block.text

            response_text += f"\n---\n{final}"
            yield response_text
            return

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    expr = block.input.get("expression", "")
                    result = run_calculator(expr) if block.name == "calculator" else f"Unknown tool: {block.name}"

                    response_text += f"🔧 **Calculator:** `{expr}` → **`{result}`**\n"
                    yield response_text

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})

        if step >= 10:
            response_text += "\n⚠️ Max steps reached."
            yield response_text
            return


EXAMPLES = [
    "What is 1234 multiplied by 5678?",
    "What is the capital of France and why is it famous?",
    "I need to buy 3 items: a book for ₹450, a pen for ₹75, and a notebook for ₹120. Calculate the total, apply a 10% discount, and give me the final price.",
    "A cricket team scored 287 runs in 50 overs. Calculate the run rate, runs needed if target is 310, and required rate in the last 5 overs.",
    "Calculate: 15% of 2500, then add it to 2500.",
]

with gr.Blocks(title="Lab 1 — AI Agent Demo") as demo:
    gr.Markdown("""
# 🤖 Lab 1 — AI Agent Demo

This agent uses Claude + a **calculator tool** to solve problems step by step.

- It **decides** when to use the tool (or not)
- You can **watch each step** as it works
- Try a math question, a general knowledge question, or a multi-step problem
""")

    chatbot = gr.ChatInterface(
        fn=agent_chat,
        examples=EXAMPLES,
        title="",
        description="Ask the agent anything — it will use the calculator tool when needed.",
    )

if __name__ == "__main__":
    demo.launch(
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )
