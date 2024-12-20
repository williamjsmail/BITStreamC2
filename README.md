# BITStreamC2

This project demonstrates a Command and Control (C2) implant that uses **Background Intelligent Transfer Service (BITS)** on Windows to perform command execution and result reporting. The implant periodically fetches commands from a remote server, executes them, and uploads the results.

## Features

- **Command Fetching**: The implant downloads commands from a server in JSON format.
- **Command Execution**: Commands are executed locally, and their outputs are redirected to a result file.
- **Result Uploading**: The implant uploads the result file back to the server.

## Components

### 1. **Implant (C++)**
The implant is a Windows executable written in C++ that performs the following tasks:
- **Command Fetching**: Uses BITS to download a JSON file (`command.json`) containing the command to execute.
- **Execution**: Executes the command and saves the output to `response.txt`.
- **Uploading Results**: Uploads the `response.txt` file to the server.

### 2. **Server**
A BITS compliant HTTP server that:
- Serves `command.json` at `/commands/command.json`.
- Receives the `response.txt` file at `/uploads/response.txt`.

---

## Installation

### Prerequisites
- **Windows OS for compiling C++ implant**
- **BITS**: Ensure BITS is enabled on the system.
- **C++ Compiler**: GCC/MinGW or Visual Studio.

### Build Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/williamjsmail/BITStreamC2
   cd BITStreamC2
