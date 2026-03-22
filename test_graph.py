"""Scripted test for the agent graph - no user input required."""
import asyncio
from langchain_core.messages import HumanMessage
from src.agent_graph import app, job_storage
import re
import time


async def run_graph_tests():
    """Run scripted tests with the agent graph."""
    print("=" * 60)
    print("Agent Graph - Scripted Tests")
    print("=" * 60)
    
    # Test 1: Simple message
    print("\n" + "=" * 60)
    print("Test 1: Simple greeting")
    print("=" * 60)
    result = await app.ainvoke({"messages": [HumanMessage(content="Hello!")]})
    for m in result["messages"]:
        print(f"{m.type}: {m.content}")
    
    # Test 2: Use task dispatcher (synchronous)
    print("\n" + "=" * 60)
    print("Test 2: Task dispatcher (research)")
    print("=" * 60)
    result = await app.ainvoke({
        "messages": [HumanMessage(content="Use the task tool to research what is Python")]
    })
    for m in result["messages"]:
        print(f"{m.type}: {m.content}")
    
    # Test 3: Start background job
    print("\n" + "=" * 60)
    print("Test 3: Start background job (writer)")
    print("=" * 60)
    result = await app.ainvoke({
        "messages": [HumanMessage(content="Start a background job with the writer agent to write a short poem about rain")]
    })
    job_id = None
    for m in result["messages"]:
        print(f"{m.type}: {m.content}")
        match = re.search(r"job_\w+", m.content)
        if match:
            job_id = match.group()
            print(f"\n[Extracted job ID: {job_id}]")
    
    if job_id:
        # Test 4: Check status
        print("\n" + "=" * 60)
        print("Test 4: Check job status")
        print("=" * 60)
        time.sleep(2)  # Wait a bit
        result = await app.ainvoke({
            "messages": [HumanMessage(content=f"Check the status of {job_id}")]
        })
        for m in result["messages"]:
            print(f"{m.type}: {m.content}")
        
        # Test 5: Get result (wait for completion)
        print("\n" + "=" * 60)
        print("Test 5: Get job result (waiting 45s for completion...)")
        print("=" * 60)
        time.sleep(45)
        result = await app.ainvoke({
            "messages": [HumanMessage(content=f"Get the result for {job_id}")]
        })
        for m in result["messages"]:
            print(f"{m.type}: {m.content}")
        
        # Test 6: Final status check
        print("\n" + "=" * 60)
        print("Test 6: Final status check")
        print("=" * 60)
        result = await app.ainvoke({
            "messages": [HumanMessage(content=f"What is the status of {job_id}?")]
        })
        for m in result["messages"]:
            print(f"{m.type}: {m.content}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_graph_tests())
