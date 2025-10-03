import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase import create_client, Client

def get_email_body(instruction: str) -> str:
    """Mock function to generate email body."""
    print(f"Generating email body for instruction: '{instruction}'")
    return f"Hello, this is your daily update based on: '{instruction}'. Have a great day!"

def send_emails_for_flow(flow_id: int, instruction: str):
    """
    Fetches receivers for a flow and 'sends' an email.
    In a real application, this would use an email service (e.g., via Gmail API).
    """
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase credentials not found for scheduler.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"\n--- Triggering job for Flow ID: {flow_id} at specified time ---")
    
    email_body = get_email_body(instruction)
    
    try:
        response = supabase.table('receivers').select('email, name').eq('flow_id', flow_id).eq('active', True).execute()
        
        if response.data:
            receivers = response.data
            print(f"Found {len(receivers)} active receivers for Flow ID {flow_id}.")
            
            for receiver in receivers:
                print(f"Simulating sending email to: {receiver['name']} <{receiver['email']}>")
                print(f"  Subject: Your Daily Update")
                print(f"  Body: {email_body}\n")
        else:
            print(f"No active receivers found for Flow ID {flow_id}.")

    except Exception as e:
        print(f"An error occurred while processing flow {flow_id}: {e}")

scheduler = BackgroundScheduler(timezone="UTC")

def schedule_flow(flow_id: int, hour: int, minute: int, instruction: str):
    """Adds or updates a job in the scheduler for a given flow."""
    job_id = f"flow_{flow_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        print(f"Removed existing job '{job_id}' to update schedule.")

    scheduler.add_job(
        send_emails_for_flow,
        trigger=CronTrigger(hour=hour, minute=minute, second=0),
        args=[flow_id, instruction],
        id=job_id,
        replace_existing=True
    )
    print(f"Scheduled job '{job_id}' to run daily at {hour:02d}:{minute:02d}.")
