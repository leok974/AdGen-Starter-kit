# AdGen Automated Workflow Script
# This script handles: Generate -> Wait -> Finalize -> Download

param(
    [Parameter(Mandatory=$true)]
    [string]$Prompt,
    
    [string]$NegativePrompt = "",
    [int]$Seed = $null,
    [int]$MaxWaitMinutes = 10,
    [string]$OutputDir = "adgen_results"
)

# Configuration
$API_BASE = "http://127.0.0.1:8000"
$CHECK_INTERVAL = 15  # seconds between checks

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir"
}

# Function to check if ComfyUI is responding
function Test-ComfyUI {
    try {
        $response = Invoke-RestMethod "http://localhost:8188/system_stats" -TimeoutSec 5
        return $true
    } catch {
        return $false
    }
}

# Function to check if AdGen API is healthy
function Test-AdGenAPI {
    try {
        $response = Invoke-RestMethod "$API_BASE/health" -TimeoutSec 5
        # Handle different response formats - could be boolean true or object with ok property
        return ($response -eq $true) -or ($response.ok -eq $true) -or ($response -ne $null)
    } catch {
        return $false
    }
}

# Function to wait for generation completion by monitoring ComfyUI queue
function Wait-ForGeneration {
    param([int]$MaxMinutes, [string]$PromptId)
    
    Write-Host "Monitoring generation progress (max $MaxMinutes minutes)..."
    $startTime = Get-Date
    $maxTime = $startTime.AddMinutes($MaxMinutes)
    $checkCount = 0
    
    while ((Get-Date) -lt $maxTime) {
        $checkCount++
        Write-Host "  Check #$checkCount - $((Get-Date).ToString('HH:mm:ss'))"
        
        try {
            # Check ComfyUI queue status
            $queueStatus = Invoke-RestMethod "http://localhost:8188/queue" -TimeoutSec 10
            
            # Check if our prompt is still in the queue
            $stillProcessing = $false
            
            # Check running queue
            if ($queueStatus.queue_running -and $queueStatus.queue_running.Count -gt 0) {
                $runningIds = $queueStatus.queue_running | ForEach-Object { $_[1] }
                if ($runningIds -contains $PromptId) {
                    $stillProcessing = $true
                    Write-Host "    Status: Currently processing"
                }
            }
            
            # Check pending queue
            if ($queueStatus.queue_pending -and $queueStatus.queue_pending.Count -gt 0) {
                $pendingIds = $queueStatus.queue_pending | ForEach-Object { $_[1] }
                if ($pendingIds -contains $PromptId) {
                    $stillProcessing = $true
                    Write-Host "    Status: Pending in queue"
                }
            }
            
            if (-not $stillProcessing) {
                Write-Host "    Status: Generation completed!"
                return
            }
            
        } catch {
            Write-Host "    ComfyUI queue check failed, using fallback timing"
            # Fallback: just wait a bit more
        }
        
        Start-Sleep -Seconds $CHECK_INTERVAL
    }
    
    Write-Host "Wait period completed (timeout reached)"
}

# Main workflow
try {
    Write-Host "=== AdGen Automated Workflow ===" -ForegroundColor Cyan
    Write-Host "Prompt: $Prompt"
    Write-Host "Output Directory: $OutputDir"
    Write-Host ""

    # Step 1: Health checks
    Write-Host "1. Checking system health..." -ForegroundColor Yellow
    
    if (-not (Test-AdGenAPI)) {
        throw "AdGen API is not responding. Make sure docker-compose is running."
    }
    Write-Host "   AdGen API: OK"
    
    if (-not (Test-ComfyUI)) {
        throw "ComfyUI is not responding. Make sure ComfyUI is running on port 8188."
    }
    Write-Host "   ComfyUI: OK"

    # Step 2: Start generation
    Write-Host "2. Starting generation..." -ForegroundColor Yellow
    
    # Build payload
    $payload = @{ prompt = $Prompt }
    if ($NegativePrompt) { $payload.negative_prompt = $NegativePrompt }
    if ($Seed) { $payload.seed = $Seed }
    
    $payloadJson = $payload | ConvertTo-Json
    Write-Host "   Payload: $payloadJson"
    
    $response = Invoke-RestMethod -Uri "$API_BASE/generate" -Method Post -ContentType "application/json" -Body $payloadJson
    $runId = $response.run_id
    
    Write-Host "   Generation started: $runId" -ForegroundColor Green
    Write-Host "   Status: $($response.status)"

    # Step 3: Wait for completion
    Write-Host "3. Monitoring generation..." -ForegroundColor Yellow
    Wait-ForGeneration -MaxMinutes $MaxWaitMinutes -PromptId $response.prompt_id

    # Step 4: Finalize
    Write-Host "4. Finalizing run..." -ForegroundColor Yellow
    
    try {
        $finalizeResult = Invoke-RestMethod -Uri "$API_BASE/finalize/$runId" -Method Post
        Write-Host "   Images collected: $($finalizeResult.images.Count)"
        Write-Host "   Total files: $($finalizeResult.files.Count)"
        
        $totalSize = ($finalizeResult.files | Measure-Object -Property size -Sum).Sum
        Write-Host "   Total size: $([math]::Round($totalSize / 1MB, 2)) MB"
    } catch {
        throw "Finalization failed: $($_.Exception.Message)"
    }

    # Step 5: Download
    Write-Host "5. Downloading results..." -ForegroundColor Yellow
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = Join-Path $OutputDir "adgen_${runId}_${timestamp}.zip"
    
    Invoke-WebRequest "$API_BASE/download/$runId" -OutFile $outputFile
    
    $fileInfo = Get-Item $outputFile
    Write-Host "   Downloaded: $($fileInfo.Name)" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB"
    Write-Host "   Path: $($fileInfo.FullName)"

    # Step 6: Extract and display results
    Write-Host "6. Extracting results..." -ForegroundColor Yellow
    
    $extractPath = Join-Path $OutputDir "extracted_${runId}_${timestamp}"
    Expand-Archive $outputFile -DestinationPath $extractPath
    
    $extractedFiles = Get-ChildItem $extractPath -File
    Write-Host "   Extracted $($extractedFiles.Count) files:"
    
    foreach ($file in $extractedFiles) {
        Write-Host "     - $($file.Name) ($([math]::Round($file.Length / 1KB, 0)) KB)"
        
        # Auto-open images if they're PNG/JPG
        if ($file.Extension -match '\.(png|jpg|jpeg)$') {
            Start-Process $file.FullName
        }
    }

    Write-Host ""
    Write-Host "=== SUCCESS ===" -ForegroundColor Green
    Write-Host "Run ID: $runId"
    Write-Host "ZIP: $outputFile"
    Write-Host "Extracted: $extractPath"

} catch {
    Write-Host ""
    Write-Host "=== ERROR ===" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "1. Ensure Docker container is running: docker compose -f adgen/docker-compose.dev.yml up"
    Write-Host "2. Ensure ComfyUI is running on port 8188"
    Write-Host "3. Check Docker logs: docker compose -f adgen/docker-compose.dev.yml logs"
    exit 1
}

# Cleanup option
$cleanup = Read-Host "Delete run from server? (y/n)"
if ($cleanup -eq 'y' -or $cleanup -eq 'Y') {
    try {
        Invoke-RestMethod -Uri "$API_BASE/runs/$runId" -Method Delete
        Write-Host "Run $runId deleted from server" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not delete run: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}