import time
import signal
import sys

inventory = []

def add_agent(agent, hostname, ip):
    inventory.append({"agent": agent, "hostname": hostname, "ip": ip})

def check(agent):
    return any(item.get("agent") == agent for item in inventory)

def display_table(data):
    if not data:
        print("No agents yet!")
        return

    headers = list(data[0].keys())
    col_widths = {header: max(len(header), max(len(str(row[header])) for row in data)) for header in headers}

    print("=" * (sum(col_widths.values()) + len(headers) * 3))
    print("".join(f"{header:<{col_widths[header] + 2}}" for header in headers))
    print("=" * (sum(col_widths.values()) + len(headers) * 3))

    for row in data:
        print("".join(f"{str(row[header]):<{col_widths[header] + 2}}" for header in headers))

    print("=" * (sum(col_widths.values()) + len(headers) * 3))

def show():
    with open("uploads/response.txt", "r") as f:
        agent = f.readline().strip()
        hostname = f.readline().strip()
        ip = f.readline().strip()
        if not check(agent):
            add_agent(agent, hostname, ip)
    display_table(inventory)
