# progress_tracker.py
import datetime

def log_progress(msg):
    with open("PROGRESS.md", "a") as f:
        f.write(f"\n[{datetime.datetime.now().strftime('%H:%M')}] {msg}")
    print(f"Progress: {msg}")
    
log_progress("Starting implementation continuation from branch a3dd")