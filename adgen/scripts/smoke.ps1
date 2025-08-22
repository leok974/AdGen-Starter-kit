param(
    [string]$Base="http://localhost:8000",
    [string]$Prompt="smoke test can on ice",
    [int]$TimeoutSeconds=120
)

$ErrorActionPreference = "Stop"

function Wait-ForHealth {
    param([string]$Url, [int]$MaxAttempts=30)
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $health = Invoke-RestMethod "$Url/health" -TimeoutSec 5
            if ($health.ok) { return }
        } catch {
            Write-Host "Health check $i/$MaxAttempts failed, retrying..."
        }
        Start-Sleep 2
    }
    throw "Service not healthy after $MaxAttempts attempts"
}

function Extract-RunId {
    param($Response)

    # Try direct string match first
    if ($Response -is [string] -and $Response -match '^[a-f0-9]{8,}$') {
        return $Response
    }

    # Try structured response paths
    if ($Response.run_id -and $Response.run_id -is [string]) {
        return $Response.run_id
    }
    if ($Response.detail.run_id) {
        return $Response.detail.run_id
    }
    if ($Response.run_id.run_id) {
        return $Response.run_id.run_id
    }

    # Last resort: regex search in JSON
    $json = $Response | ConvertTo-Json -Depth 12 -Compress
    if ($json -match '"run_id"\s*:\s*"([a-f0-9]{8,})"') {
        return $Matches[1]
    }

    throw "No valid run_id found in response: $json"
}

Write-Host "Checking health..."
Wait-ForHealth $Base

Write-Host "Generating run..."
try {
    $genBody = @{ prompt = $Prompt } | ConvertTo-Json
    $gen = Invoke-RestMethod -Method Post "$Base/generate" -ContentType "application/json" -Body $genBody -TimeoutSec $TimeoutSeconds
    $run = Extract-RunId $gen
    Write-Host "RUN ID: $run"
} catch {
    Write-Host "Generate failed: $_"
    Write-Host "Response: $(try { $gen | ConvertTo-Json -Depth 5 } catch { 'N/A' })"
    throw
}

Write-Host "Finalizing run..."
try {
    $fin = Invoke-RestMethod -Method Post "$Base/finalize/$run" -TimeoutSec $TimeoutSeconds
    Write-Host "Finalize completed"
} catch {
    Write-Host "Finalize failed: $_"
    # Try to get run status for debugging
    try {
        $status = Invoke-RestMethod "$Base/runs/$run/files"
        Write-Host "Current run status: $($status | ConvertTo-Json -Depth 3)"
    } catch {}
    throw
}

Write-Host "Checking files..."
try {
    $files = Invoke-RestMethod "$Base/runs/$run/files" -TimeoutSec 30
    if (-not $files.files -or $files.files.Count -eq 0) {
        throw "No files generated in run $run"
    }
    Write-Host "Files found: $($files.files.Count)"
} catch {
    Write-Host "File check failed: $_"
    throw
}

Write-Host "✅ Smoke test PASSED"
exit 0
