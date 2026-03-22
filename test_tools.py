"""Test the three-tool pattern directly without full supervisor."""
import re
import time
from src.agent_graph import start_job, check_status, get_result, job_storage


def test_three_tool_pattern():
    print("=" * 60)
    print("Testing Three-Tool Pattern")
    print("=" * 60)
    
    # Step 1: Start job
    print("\n[1] Starting background job...")
    job_response = start_job.invoke({
        "agent_name": "writer",
        "description": "Write a short haiku about coding"
    })
    print(f"Response: {job_response}")
    
    # Extract job ID
    match = re.search(r"job_\w+", job_response)
    if not match:
        print("ERROR: Could not extract job ID")
        return
    job_id = match.group()
    print(f"Job ID: {job_id}")
    
    # Step 2: Check status (while running)
    print("\n[2] Checking status (should be running)...")
    time.sleep(1)
    status_response = check_status.invoke({"job_id": job_id})
    print(f"Status: {status_response}")
    
    # Step 3: Wait and get result
    print("\n[3] Waiting for completion and getting result...")
    time.sleep(45)
    result_response = get_result.invoke({"job_id": job_id})
    print(f"Result: {result_response}")
    
    # Also check status to confirm
    print("\n[4] Final status check...")
    final_status = check_status.invoke({"job_id": job_id})
    print(f"Final Status: {final_status}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_three_tool_pattern()
