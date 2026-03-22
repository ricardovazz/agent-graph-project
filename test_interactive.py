"""Interactive test script for the agent graph."""
import asyncio
from langchain_core.messages import HumanMessage
from src.agent_graph import app


async def interactive_test():
    """Run interactive tests with the agent graph."""
    print("=" * 60)
    print("Interactive Agent Graph Test")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  1 - Test synchronous 'task' dispatcher")
    print("  2 - Test async_research tool")
    print("  3 - Start a background job (three-tool pattern)")
    print("  4 - Check job status")
    print("  5 - Get job result")
    print("  6 - Custom message")
    print("  q - Quit")
    print("=" * 60)
    
    # Store job IDs from this session
    job_ids = []
    
    while True:
        print("\nSelect option (1-6 or q):")
        choice = input("> ").strip()
        
        if choice == 'q':
            print("Goodbye!")
            break
        
        if choice == '1':
            msg = "Use the task tool to research the history of computers"
            print(f"\nSending: {msg}")
            result = await app.ainvoke({"messages": [HumanMessage(content=msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
        
        elif choice == '2':
            msg = "Use async_research to find information about machine learning"
            print(f"\nSending: {msg}")
            result = await app.ainvoke({"messages": [HumanMessage(content=msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
        
        elif choice == '3':
            print("\nWhat task type? (research/writer)")
            task_type = input("> ").strip()
            print("\nEnter task description:")
            description = input("> ").strip()
            
            msg = f"Start a background job with the {task_type} agent to: {description}"
            print(f"\nSending: {msg}")
            result = await app.ainvoke({"messages": [HumanMessage(content=msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
                # Extract and store job ID
                import re
                match = re.search(r"job_\w+", m.content)
                if match:
                    job_ids.append(match.group())
                    print(f"\n[Stored job ID: {match.group()}]")
        
        elif choice == '4':
            if not job_ids:
                print("No job IDs stored. Start a job first (option 3).")
                continue
            
            print(f"\nAvailable job IDs: {job_ids}")
            print("Enter job ID (or 'latest' for most recent):")
            job_id = input("> ").strip()
            if job_id == 'latest' and job_ids:
                job_id = job_ids[-1]
            
            msg = f"Check the status of {job_id}"
            print(f"\nSending: {msg}")
            result = await app.ainvoke({"messages": [HumanMessage(content=msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
        
        elif choice == '5':
            if not job_ids:
                print("No job IDs stored. Start a job first (option 3).")
                continue
            
            print(f"\nAvailable job IDs: {job_ids}")
            print("Enter job ID (or 'latest' for most recent):")
            job_id = input("> ").strip()
            if job_id == 'latest' and job_ids:
                job_id = job_ids[-1]
            
            msg = f"Get the result for {job_id}"
            print(f"\nSending: {msg}")
            result = await app.ainvoke({"messages": [HumanMessage(content=msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
        
        elif choice == '6':
            print("\nEnter your message:")
            custom_msg = input("> ").strip()
            result = await app.ainvoke({"messages": [HumanMessage(content=custom_msg)]})
            for m in result["messages"]:
                print(f"\n{m.type}: {m.content}")
        
        else:
            print("Invalid option. Choose 1-6 or q.")


if __name__ == "__main__":
    asyncio.run(interactive_test())
