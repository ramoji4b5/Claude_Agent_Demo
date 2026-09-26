import anthropic
import json
import ast
import operator

# ──────────────────────────────────────────────────────────────
# ⚙️  SETUP
# ──────────────────────────────────────────────────────────────
API_KEY = ""  # ← REPLACE THIS
client  = anthropic.Anthropic(api_key=API_KEY)
MODEL   = "claude-sonnet-4-6"

def hello_world(st_name):
    print("\n" + "="*60)
    print(f"Hello Good Morning...! {st_name}")
    print("="*60)

    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[
            {"role": "user", "content": f"Welcome the user {st_name}"}
        ]
    )

    # Claude answers and stops. No loop. No tools. No decisions.
    print("Claude answered:", response.content[0].text)

if __name__ == "__main__":
    print("🤖 LAB 0 — Hello World")
    print("=" * 60)
    username = str(input("enter the entity name :"))
    hello_world(username)

    # Start here — see the difference between a function call and an agent:
