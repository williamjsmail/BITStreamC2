# BITStreamC2

**BITStreamC2** is a command-and-control (C2) framework leveraging Background Intelligent Transfer Service (BITS) to communicate between agents and a central server. It supports Windows implants in both PowerShell and C++, allowing for fileless command execution and data exfiltration.

![Alt text](images/bsc2.png) 

---

## Features

- Agent registration via `notify.txt`
- Command queuing and remote execution
- Response collection via BITS uploads
- Multiple implant formats (`ps1` and `cpp`) **cpp Needs Update**
- CLI-based interaction with live agents
- Offline agent detection and pruning
- Hostname/IP auto-collection from agent
- Persistent command queuing with command history
- Server-side command file and response file handling

---

## How It Works

1. **Agents check in** by uploading a `notify.txt` file.
2. The C2 server registers new agents and maintains their last seen timestamp.
3. Analysts queue commands using a CLI (`set command <cmd>`).
4. The implant downloads commands, executes them, and uploads the output to `/uploads/<agent>_response.txt`.
5. The C2 displays and logs results per agent.

---

---

## Commands (CLI)

```bash
list                              # Show all agents
select agent <id>                 # Target an agent
exitagent                         # Deselect current agent
set command <cmd>                 # Queue a command
show agents|commands              # View agents or command queues
remove agent <id>                 # Delete agent
prune                             # Auto-delete stale agents
generate implant ps1|cpp          # Generate an implant
debug                             # View environment and raw responses
exit                              # Exit the shell
```

---

---

## To Do

BSC2 is still a work in progress and has many bugs. Some of the features I would like to add are:
1. Encrypted Communications
2. Reverse Command Injection
3. HTTP Header Randomization
4. SMB Support
5. File Upload/Download Support
6. Keylogger Plugin
7. Clipboard Extraction
8. Persistence Options
9. Multi-Host Beaconing
10. Complete Autocompletion of Commands
11. Agent Auth Tokens
12. Etc.
