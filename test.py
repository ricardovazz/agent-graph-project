"""Simple test for the Three-tool pattern with polling."""
import asyncio
import time
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from langchain_core.messages import HumanMessage
from src.agent_graph import app, get_thread_config, create_thread_id


async def test_three_tool_pattern():
    print("=" * 60)
    print("Three-Tool Pattern Test (with polling)")
    print("=" * 60)
    
    # Check LangSmith configuration
    if os.environ.get("LANGSMITH_API_KEY"):
        print(f"\n✓ LangSmith tracing enabled")
        print(f"  Project: {os.environ.get('LANGSMITH_PROJECT', 'default')}")
        print(f"  View traces at: https://smith.langchain.com")
    else:
        print("\n✗ LangSmith tracing NOT enabled")
        print("  Set LANGSMITH_API_KEY environment variable to enable tracing")
        print("  See .env.example for configuration")
    print("=" * 60)

    # Create a thread ID to group all related runs together
    thread_id = create_thread_id()
    print(f"\n📋 Thread ID: {thread_id}")
    print(f"   All runs in this session will be grouped in LangSmith")
    print("=" * 60)
    
    # Get config with thread_id for tracing
    config = get_thread_config(thread_id)

    # Step 1: Start job
    print("\n[1] Starting background job (writer agent)...")
    result = await app.ainvoke({
        "messages": [HumanMessage(content="Start a background job with the writer agent to write a haiku about coding")]
    }, config=config)
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")

    # Extract job ID
    job_id_match = re.search(r"job_\w+", msg.content)
    if not job_id_match:
        print("ERROR: No job ID found")
        return
    job_id = job_id_match.group()
    print(f"\nJob ID: {job_id}")

    # Step 2: Poll for completion
    print("\n[2] Polling for completion (every 15s, max 2min)...")
    max_attempts = 8  # 8 * 15s = 120s = 2min
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        time.sleep(15)

        result = await app.ainvoke({
            "messages": [HumanMessage(content=f"Check the status of {job_id}")]
        }, config=config)
        for msg in result["messages"]:
            print(f"\n[Poll {attempt}/8] {msg.type}: {msg.content}")

            if "completed" in msg.content:
                # Step 3: Get result
                print("\n[3] Job completed! Getting result...")
                result = await app.ainvoke({
                    "messages": [HumanMessage(content=f"Get the result for {job_id}")]
                }, config=config)
                for m in result["messages"]:
                    print(f"{m.type}: {m.content}")
                print("\n" + "=" * 60)
                print("Test complete!")
                print(f"View all runs in thread at: https://smith.langchain.com")
                print("=" * 60)
                return

    print("\nERROR: Timeout after 2 minutes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_three_tool_pattern())
