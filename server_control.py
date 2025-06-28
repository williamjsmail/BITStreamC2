import os
import subprocess
import time
from colorama import Fore, Style
from utils import log_error, log_info

def start_server(server_script, log_file):
    """Start the server script and capture output for debugging."""
    if not os.path.exists(server_script):
        print(f"{Fore.RED}[-] Server script '{server_script}' not found.{Style.RESET_ALL}")
        log_error(f"Server script '{server_script}' not found", log_file)
        return None

    print(f"{Fore.CYAN}[*] Starting server script: {server_script} on port 80...{Style.RESET_ALL}")
    log_info(f"Starting server script: {server_script} on port 80", log_file)
    try:
        server_process = subprocess.Popen(
            ["sudo", "python3", server_script, "80"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2)
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate(timeout=5)
            error_msg = f"Server process terminated unexpectedly. stdout: {stdout}, stderr: {stderr}"
            log_error(error_msg, log_file)
            print(f"{Fore.RED}[-] Failed to start server: {error_msg}{Style.RESET_ALL}")
            return None
        log_info("Server started successfully", log_file)
        print(f"{Fore.GREEN}[+] Server started successfully on port 80{Style.RESET_ALL}")
        return server_process
    except Exception as e:
        log_error(f"Failed to start server: {str(e)}", log_file)
        print(f"{Fore.RED}[-] Failed to start server: {str(e)}{Style.RESET_ALL}")
        return None

def stop_server(server_process, log_file):
    """Stop the server process."""
    if server_process:
        print(f"{Fore.CYAN}[*] Stopping server script...{Style.RESET_ALL}")
        log_info("Stopping server script", log_file)
        try:
            server_process.terminate()
            stdout, stderr = server_process.communicate(timeout=5)
            print(f"{Fore.GREEN}[+] Server stopped. stdout: {stdout}, stderr: {stderr}{Style.RESET_ALL}")
            log_info(f"Server stopped. stdout: {stdout}, stderr: {stderr}", log_file)
        except Exception as e:
            log_error(f"Failed to stop server: {str(e)}", log_file)
            print(f"{Fore.RED}[-] Failed to stop server: {str(e)}{Style.RESET_ALL}")