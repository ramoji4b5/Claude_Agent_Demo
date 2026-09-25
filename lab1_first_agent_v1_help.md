---
What This Lab Is About

This lab teaches you the difference between a regular AI call and an AI Agent.

---
The Big Idea: Function Call vs Agent

┌──────────────────────────────────┬─────────────────────────────────────────┐
│      Regular Function Call       │                AI Agent                 │
├──────────────────────────────────┼─────────────────────────────────────────┤
│ YOU decide what to ask           │ Claude decides what to do next          │
├──────────────────────────────────┼─────────────────────────────────────────┤
│ One question → one answer → DONE │ Claude loops until the goal is achieved │
├──────────────────────────────────┼─────────────────────────────────────────┤
│ Claude just replies              │ Claude calls tools on its own           │
└──────────────────────────────────┴─────────────────────────────────────────┘

---
The 4 Parts Explained

Part 0 — NOT an Agent (lines 46–79)

response = client.messages.create(...)
print(response.content[0].text)
You ask Claude "What is 15 + 27?" and it answers. That's it. No loop, no tools, no decisions. Just like texting someone a question.

---
Part 1 — The Tool (lines 86–143)

Two things are defined here:

1. Tool Description (CALCULATOR_TOOL_DEFINITION) — This is like a menu card you give Claude. It says:

▎ "Hey Claude, there's a tool called calculator. You can call it whenever you need to do math."

2. Tool Implementation (run_calculator) — This is the actual Python code that does the math. Claude cannot run Python itself — WE run it and send the result back.

---
Part 2 — The Agent Loop (lines 147–272)

This is the heart of the lab. The loop works like this:

YOU give a goal
    ↓
Claude thinks: "What should I do?"
    ↓
Claude wants calculator? → WE run it → send result back to Claude
    ↓
Claude thinks again with the new result
    ↓
Repeat until Claude says "I'm done" (end_turn)

Two possible outcomes each loop:
- stop_reason == "end_turn" → Claude is done, print the answer
- stop_reason == "tool_use" → Claude wants a tool, run it, loop again

---
Part 3 — 4 Demos (lines 283–341)

┌────────┬─────────────────────────────────────────────────────────────────────┐
│  Demo  │                            What it shows                            │
├────────┼─────────────────────────────────────────────────────────────────────┤
│ Demo 1 │ Claude calls calculator once                                        │
├────────┼─────────────────────────────────────────────────────────────────────┤
│ Demo 2 │ Claude calls calculator multiple times in sequence                  │
├────────┼─────────────────────────────────────────────────────────────────────┤
│ Demo 3 │ Claude decides it doesn't need the tool (France capital question)   │
├────────┼─────────────────────────────────────────────────────────────────────┤
│ Demo 4 │ Claude plans steps and calls tool multiple times (cricket run rate) │
└────────┴─────────────────────────────────────────────────────────────────────┘

---
Part 4 — Your Challenge (lines 346–384)

Add a text_length tool that counts characters and words in a text. The template is already given — you just need to wire it up in 5 steps.

---
The Key Takeaway

▎ An Agent = Claude + a Loop + Tools + Claude deciding when to stop

The loop and the tool-calling decision are what separate an agent from a simple API call.