# Registers the BMB Sandbox Server to start automatically at logon.
#
# No admin rights needed -- this is a per-user logon task, the same approach
# the DuckDNS updater uses. Re-running it updates the existing task rather
# than creating a second one.
#
#   Install / update :  powershell -ExecutionPolicy Bypass -File install-autostart.ps1
#   Remove           :  powershell -ExecutionPolicy Bypass -File install-autostart.ps1 -Remove
#
# Runs pythonw.exe, so there is no console window. That also means no visible
# log -- when you need to watch requests, stop the task and use run.bat instead.

param([switch]$Remove)

$TaskName = "BMB Sandbox Server"
$DataTask = "BMB Loop Data Refresh"
$Here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script   = Join-Path $Here "serve.py"

if ($Remove) {
    foreach ($t in @($TaskName, $DataTask)) {
        if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
            Stop-ScheduledTask  -TaskName $t -ErrorAction SilentlyContinue
            Unregister-ScheduledTask -TaskName $t -Confirm:$false
            Write-Host "Removed scheduled task '$t'." -ForegroundColor Yellow
        } else {
            Write-Host "No task named '$t' -- nothing to remove."
        }
    }
    return
}

# --- locate pythonw.exe (console-less python) -------------------------------
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { Write-Error "Python not found on PATH. Install Python 3 from python.org."; return }
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }   # fall back; a console window will show

if (-not (Test-Path $Script)) { Write-Error "serve.py not found next to this script ($Script)."; return }

# --- (re)register -----------------------------------------------------------
$action  = New-ScheduledTaskAction -Execute $pythonw -Argument "serve.py" -WorkingDirectory $Here
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Restart if it dies; never stop it for running long or on battery -- this is
# a laptop, and a server that quits when unplugged is not a server.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Replacing existing task..." -ForegroundColor DarkGray
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Static host for BlackMarker.TV work in progress (http://127.0.0.1:8790)" | Out-Null

# --- nightly refresh of loop-data.json ---------------------------------------
# Upcoming and Latest Shows read a generated file, because building it needs the
# ChannelCast token and that can never reach a browser. 4am so it never lands
# mid-show. StartWhenAvailable catches up if the laptop was asleep.
$dataAction  = New-ScheduledTaskAction -Execute $pythonw -Argument "build-loop-data.py" -WorkingDirectory $Here
$dataTrigger = New-ScheduledTaskTrigger -Daily -At 4am
$dataSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

if (Get-ScheduledTask -TaskName $DataTask -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $DataTask -Confirm:$false
}
Register-ScheduledTask -TaskName $DataTask -Action $dataAction -Trigger $dataTrigger `
    -Settings $dataSettings -Description "Rebuild loop-data.json for the BlackMarker.TV homepage" | Out-Null

Write-Host ""
Write-Host "Registered '$DataTask' -- runs daily at 4:00am." -ForegroundColor Green
Write-Host "Registered '$TaskName' -- starts at logon." -ForegroundColor Green
Write-Host "  Runs   : $pythonw serve.py"
Write-Host "  From   : $Here"
Write-Host "  URL    : http://127.0.0.1:8790/"
Write-Host ""
Write-Host "  Start now : schtasks /run /tn `"$TaskName`""
Write-Host "  Stop      : schtasks /end /tn `"$TaskName`""
Write-Host "  Remove    : powershell -ExecutionPolicy Bypass -File install-autostart.ps1 -Remove"
Write-Host ""
