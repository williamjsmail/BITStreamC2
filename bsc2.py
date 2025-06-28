import os
from colorama import init, Fore, Style
from agent_manager import AgentManager
from server_control import start_server, stop_server
from cli import run_cli
from utils import log_error, log_info
import threading
import time

# Initialize colorama
init(strip=False, autoreset=True)

# Directories and files
BASE_DIR = os.getcwd()
COMMAND_DIR = os.path.join(BASE_DIR, "commands")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
LOG_FILE = os.path.join(BASE_DIR, "logs", "c2.log")
AGENT_CONFIG = os.path.join(BASE_DIR, "agents.json")
NOTIFY_FILE = os.path.join(UPLOAD_DIR, "notify.txt")
SERVER_SCRIPT = "server.py"

# Ensure directories exist
os.makedirs(COMMAND_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def monitor_notify_file(agent_manager):
    while True:
        try:
            log_info("Starting notify file check", agent_manager.log_file)
            agent_manager.check_notify_file()
            log_info("Completed notify file check", agent_manager.log_file)
        except Exception as e:
            log_error(f"Error in notify file monitor: {e}", agent_manager.log_file)
        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    print(f"{Fore.MAGENTA}=== BITStreamC2 ==={Style.RESET_ALL}")
    print("[1] Start HTTP Server and Launch Operator Interface")
    print("[2] Exit")

    option = input("\nSelect an option: ")
    if option == "1":
        agent_manager = AgentManager(AGENT_CONFIG, UPLOAD_DIR)
        agent_manager.log_file = LOG_FILE
        server_process = start_server(SERVER_SCRIPT, LOG_FILE)
        if server_process:
            try:
                # Start notify file monitoring thread
                notify_thread = threading.Thread(target=monitor_notify_file, args=(agent_manager,), daemon=True)
                notify_thread.start()
                log_info("Started notify file monitoring thread", LOG_FILE)
                run_cli(agent_manager)
            except Exception as e:
                log_error(f"Error in CLI or notify thread: {e}", LOG_FILE)
            finally:
                stop_server(server_process, LOG_FILE)
    elif option == "2":
        print("Exiting...")
        log_info("Exiting BITStreamC2", LOG_FILE)
    else:
        print(f"{Fore.RED}[-] Invalid option. Exiting...{Style.RESET_ALL}")
        log_error("Invalid startup option", LOG_FILE)