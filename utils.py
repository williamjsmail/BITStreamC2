import os
from datetime import datetime

def log_error(message, log_file):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] ERROR: {message}\n")

def log_info(message, log_file):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] INFO: {message}\n")