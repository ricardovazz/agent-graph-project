"""Simple test for the Three-tool pattern with polling."""
import asyncio
import time
import re
from langchain_core.messages import HumanMessage
from src.agent_graph import app


async def test_three_tool_pattern():
    print("=" * 60)
    print("Three-Tool Pattern Test (with polling)")
    print("=" * 60)
    
    # Step 1: Start job
    print("\n[1] Starting background job (writer agent)...")
    result = await app.ainvoke({
        "messages": [HumanMessage(content="Start a background job with the writer agent to write a haiku about coding")]
    })
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
        })
        for msg in result["messages"]:
            print(f"\n[Poll {attempt}/8] {msg.type}: {msg.content}")
            
            if "completed" in msg.content:
                # Step 3: Get result
                print("\n[3] Job completed! Getting result...")
                result = await app.ainvoke({
                    "messages": [HumanMessage(content=f"Get the result for {job_id}")]
                })
                for m in result["messages"]:
                    print(f"{m.type}: {m.content}")
                print("\n" + "=" * 60)
                print("Test complete!")
                print("=" * 60)
                return
    
    print("\nERROR: Timeout after 2 minutes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_three_tool_pattern())
