import json
import os
from pathlib import Path

def create_mock_jsonl():
    data_dir = Path("tests/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data for an "Architect" style session
    session1 = [
        {"role": "user", "content": "Let's plan the architecture for the new authentication module. I want to see the existing structure first."},
        {"role": "assistant", "content": [{"type": "text", "text": "I will check the existing structure."}, {"type": "tool_use", "name": "ls", "input": {"path": "."}}]},
        {"role": "user", "content": "Before we write any code, let's compare the adapter pattern vs the factory pattern for this."},
        {"role": "assistant", "content": "Thinking about patterns...", "thinking": "The user wants to plan first. This indicates an Architect archetype."}
    ]
    
    # Mock data for a "Debugger" style session
    session2 = [
        {"role": "user", "content": "There is a bug in the logout logic. Why is the session not cleared?"},
        {"role": "assistant", "content": "Let me debug this.", "tool_calls": [{"function": {"name": "grep", "arguments": {"query": "clear_session"}}}]},
        {"role": "user", "content": "It's still broken after that fix. Trace the logs again."},
        {"role": "assistant", "content": "Checking logs..."}
    ]

    with open(data_dir / "architect_session.jsonl", "w") as f:
        for msg in session1:
            f.write(json.dumps(msg) + "\n")
            
    with open(data_dir / "debugger_session.jsonl", "w") as f:
        for msg in session2:
            f.write(json.dumps(msg) + "\n")

    print(f"✅ Created mock JSONL files in {data_dir}")

if __name__ == "__main__":
    create_mock_jsonl()
