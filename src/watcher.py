import os
import time
import yaml
import datetime
import threading
from ingest import ingest

# Status file path
STATUS_FILE = ".agent_status"

def update_status(status):
    """Update the agent status file."""
    try:
        with open(STATUS_FILE, "w") as f:
            f.write(status)
    except Exception as e:
        print(f"Error updating status: {e}")

def is_within_schedule(config):
    """Check if current time is within the scheduled active hours."""
    if not config or 'agent_schedule' not in config:
        return True  # Default to always active if no schedule
    
    schedule = config['agent_schedule']
    if not schedule.get('enabled', True):
        return False
    
    start_str = schedule.get('start_time', "09:00")
    end_str = schedule.get('end_time', "18:00")
    
    now = datetime.datetime.now().time()
    try:
        start_time = datetime.datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.datetime.strptime(end_str, "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else: # Crosses midnight
            return now >= start_time or now <= end_time
    except ValueError:
        print(f"Invalid time format in config: {start_str} or {end_str}")
        return True

def load_config():
    config_path = os.path.join(os.getcwd(), "config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def watcher_loop():
    """Main loop for the background watcher."""
    print("Background watcher started.")
    
    while True:
        config = load_config()
        schedule = config.get('agent_schedule', {})
        interval = schedule.get('check_interval_seconds', 60)
        
        if is_within_schedule(config):
            update_status("Active: Checking for new files...")
            try:
                # Run ingestion (it will only process new files due to incremental logic)
                # We pass a dummy callback or None since we don't need UI progress here
                # Or we could write progress to a file if needed
                ingest(progress_callback=None)
                update_status("Active: Idle (Waiting for next check)")
            except Exception as e:
                print(f"Error in watcher: {e}")
                update_status(f"Error: {str(e)}")
        else:
            update_status("Sleeping (Outside scheduled hours)")
        
        time.sleep(interval)

def start_watcher():
    """Start the watcher in a background thread."""
    thread = threading.Thread(target=watcher_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    # For testing independently
    watcher_loop()
