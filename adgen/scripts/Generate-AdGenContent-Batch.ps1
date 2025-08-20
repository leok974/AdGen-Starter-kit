# AdGen Batch Processing Script
# Processes multiple prompts automatically

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,  # CSV or TXT file with prompts

    [int]$MaxWaitMinutes = 10,
    [string]$OutputDir = "batch_results",
    [int]$DelayBetweenJobs = 30,  # seconds between starting each job
    [switch]$ConcurrentMode = $false  # if true, starts all jobs at once
)

# Configuration
$API_BASE = "http://127.0.0.1:8000"
$CHECK_INTERVAL = 15

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir"
}

# Health check functions (reused from single script)
function Test-ComfyUI {
    try {
        $response = Invoke-RestMethod "http://localhost:8188/system_stats" -TimeoutSec 5
        return $true
    } catch {
        return $false
    }
}

function Test-AdGenAPI {
    try {
        $response = Invoke-RestMethod "$API_BASE/health" -TimeoutSec 5
        return ($response -eq $true) -or ($response.ok -eq $true) -or ($response -ne $null)
    } catch {
        return $false
    }
}

# Function to read prompts from file
function Read-PromptsFromFile {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        throw "Input file not found: $FilePath"
    }

    $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
    $prompts = @()

    switch ($extension) {
        ".csv" {
            # Read CSV file - expect columns: prompt, negative_prompt (optional), seed (optional)
            $csvData = Import-Csv $FilePath
            foreach ($row in $csvData) {
                $promptObj = @{
                    prompt = $row.prompt
                    negative_prompt = if ($row.negative_prompt) { $row.negative_prompt } else { "" }
                    seed = if ($row.seed) { [int]$row.seed } else { $null }
                    name = if ($row.name) { $row.name } else { "prompt_$($prompts.Count + 1)" }
                }
                $prompts += $promptObj
            }
        }
        ".txt" {
            # Read TXT file - one prompt per line
            $lines = Get-Content $FilePath
            $lineNumber = 1
            foreach ($line in $lines) {
                if ($line.Trim()) {  # Skip empty lines
                    $promptObj = @{
                        prompt = $line.Trim()
                        negative_prompt = ""
                        seed = $null
                        name = "line_$lineNumber"
                    }
                    $prompts += $promptObj
                    $lineNumber++
                }
            }
        }
        default {
            throw "Unsupported file format: $extension. Use .csv or .txt"
        }
    }

    return $prompts
}

# Function to start a single generation
function Start-Generation {
    param($PromptData, $Index, $Total)

    Write-Host "[$Index/$Total] Starting: $($PromptData.name)" -ForegroundColor Cyan
    Write-Host "  Prompt: $($PromptData.prompt)"

    try {
        # Build payload
        $payload = @{ prompt = $PromptData.prompt }
        if ($PromptData.negative_prompt) { $payload.negative_prompt = $PromptData.negative_prompt }
        if ($PromptData.seed) { $payload.seed = $PromptData.seed }

        $payloadJson = $payload | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$API_BASE/generate" -Method Post -ContentType "application/json" -Body $payloadJson

        $jobInfo = @{
            name = $PromptData.name
            prompt = $PromptData.prompt
            run_id = $response.run_id
            prompt_id = $response.prompt_id
            status = $response.status
            start_time = Get-Date
        }

        Write-Host "  Started: $($response.run_id)" -ForegroundColor Green
        return $jobInfo

    } catch {
        Write-Host "  Failed to start: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Function to monitor a job until completion
function Wait-ForJob {
    param($JobInfo, $MaxMinutes)

    Write-Host "Monitoring $($JobInfo.name) (ID: $($JobInfo.run_id))..." -ForegroundColor Yellow
    $startTime = $JobInfo.start_time
    $maxTime = $startTime.AddMinutes($MaxMinutes)
    $checkCount = 0

    while ((Get-Date) -lt $maxTime) {
        $checkCount++

        try {
            # Check ComfyUI queue status
            $queueStatus = Invoke-RestMethod "http://localhost:8188/queue" -TimeoutSec 10
            $stillProcessing = $false

            # Check if prompt is still in queue
            if ($queueStatus.queue_running -and $queueStatus.queue_running.Count -gt 0) {
                $runningIds = $queueStatus.queue_running | ForEach-Object { $_[1] }
                if ($runningIds -contains $JobInfo.prompt_id) {
                    $stillProcessing = $true
                }
            }

            if ($queueStatus.queue_pending -and $queueStatus.queue_pending.Count -gt 0) {
                $pendingIds = $queueStatus.queue_pending | ForEach-Object { $_[1] }
                if ($pendingIds -contains $JobInfo.prompt_id) {
                    $stillProcessing = $true
                }
            }

            if (-not $stillProcessing) {
                Write-Host "  $($JobInfo.name): Generation completed!" -ForegroundColor Green
                return $true
            }

        } catch {
            # Queue check failed, continue waiting
        }

        Start-Sleep -Seconds $CHECK_INTERVAL
    }

    Write-Host "  $($JobInfo.name): Timeout reached" -ForegroundColor Orange
    return $false
}

# Function to finalize and download a job
function Complete-Job {
    param($JobInfo, $OutputDir)

    Write-Host "Finalizing $($JobInfo.name)..." -ForegroundColor Yellow

    try {
        # Finalize
        $finalizeResult = Invoke-RestMethod -Uri "$API_BASE/finalize/$($JobInfo.run_id)" -Method Post

        # Download
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $filename = "$($JobInfo.name)_$($JobInfo.run_id)_$timestamp.zip"
        $outputFile = Join-Path $OutputDir $filename

        Invoke-WebRequest "$API_BASE/download/$($JobInfo.run_id)" -OutFile $outputFile

        # Extract
        $extractPath = Join-Path $OutputDir "$($JobInfo.name)_$($JobInfo.run_id)_extracted"
        Expand-Archive $outputFile -DestinationPath $extractPath -Force

        $fileInfo = Get-Item $outputFile
        Write-Host "  Completed: $filename ($([math]::Round($fileInfo.Length / 1MB, 2)) MB)" -ForegroundColor Green

        return @{
            success = $true
            zip_file = $outputFile
            extracted_path = $extractPath
            size_mb = [math]::Round($fileInfo.Length / 1MB, 2)
            images_count = if ($finalizeResult.images) { $finalizeResult.images.Count } else { 0 }
        }

    } catch {
        Write-Host "  Failed to complete: $($_.Exception.Message)" -ForegroundColor Red
        return @{ success = $false; error = $_.Exception.Message }
    }
}

# Main batch processing logic
try {
    Write-Host "=== AdGen Batch Processing ===" -ForegroundColor Cyan
    Write-Host "Input File: $InputFile"
    Write-Host "Output Directory: $OutputDir"
    Write-Host "Concurrent Mode: $ConcurrentMode"
    Write-Host ""

    # Health checks
    Write-Host "Checking system health..." -ForegroundColor Yellow
    if (-not (Test-AdGenAPI)) {
        throw "AdGen API is not responding"
    }
    if (-not (Test-ComfyUI)) {
        throw "ComfyUI is not responding"
    }
    Write-Host "  Systems OK" -ForegroundColor Green

    # Read prompts
    Write-Host "Reading prompts from file..." -ForegroundColor Yellow
    $prompts = Read-PromptsFromFile -FilePath $InputFile
    Write-Host "  Found $($prompts.Count) prompts" -ForegroundColor Green

    if ($prompts.Count -eq 0) {
        throw "No prompts found in input file"
    }

    # Process prompts
    $jobs = @()
    $results = @()

    if ($ConcurrentMode) {
        # Start all jobs at once
        Write-Host "Starting all jobs concurrently..." -ForegroundColor Cyan
        for ($i = 0; $i -lt $prompts.Count; $i++) {
            $job = Start-Generation -PromptData $prompts[$i] -Index ($i + 1) -Total $prompts.Count
            if ($job) {
                $jobs += $job
            }
            Start-Sleep -Seconds 5  # Brief delay to avoid overwhelming the API
        }

        # Wait for all jobs to complete
        Write-Host "Waiting for all jobs to complete..." -ForegroundColor Cyan
        foreach ($job in $jobs) {
            $completed = Wait-ForJob -JobInfo $job -MaxMinutes $MaxWaitMinutes
            if ($completed) {
                $result = Complete-Job -JobInfo $job -OutputDir $OutputDir
                $results += $result
            }
        }

    } else {
        # Sequential processing
        Write-Host "Processing sequentially..." -ForegroundColor Cyan
        for ($i = 0; $i -lt $prompts.Count; $i++) {
            $job = Start-Generation -PromptData $prompts[$i] -Index ($i + 1) -Total $prompts.Count

            if ($job) {
                $completed = Wait-ForJob -JobInfo $job -MaxMinutes $MaxWaitMinutes
                if ($completed) {
                    $result = Complete-Job -JobInfo $job -OutputDir $OutputDir
                    $results += $result
                }

                # Delay before next job (except for last one)
                if ($i -lt ($prompts.Count - 1)) {
                    Write-Host "Waiting $DelayBetweenJobs seconds before next job..." -ForegroundColor Gray
                    Start-Sleep -Seconds $DelayBetweenJobs
                }
            }
        }
    }

    # Summary - FIXED SECTION
    Write-Host ""
    Write-Host "=== BATCH COMPLETE ===" -ForegroundColor Green
    $successful = ($results | Where-Object { $_.success }).Count
    $failed = $results.Count - $successful

    Write-Host "Processed: $($prompts.Count) prompts"
    Write-Host "Successful: $successful"
    Write-Host "Failed: $failed"

    if ($successful -gt 0) {
        try {
            # Safe calculation of totals with error handling
            $successfulResults = $results | Where-Object { $_.success }
            
            # Calculate total size with proper null checking
            $totalSize = 0
            $totalImages = 0
            
            foreach ($result in $successfulResults) {
                if ($result.size_mb -and $result.size_mb -is [System.Double]) {
                    $totalSize += $result.size_mb
                }
                if ($result.images_count -and $result.images_count -is [System.Int32]) {
                    $totalImages += $result.images_count
                }
            }
            
            # Alternative: Calculate from actual files if properties are missing
            if ($totalSize -eq 0) {
                $zipFiles = Get-ChildItem -Path $OutputDir -Filter "*.zip" -ErrorAction SilentlyContinue
                if ($zipFiles) {
                    $totalSize = [math]::Round(($zipFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
                }
            }
            
            # If we still don't have image counts, estimate based on typical output
            if ($totalImages -eq 0) {
                $totalImages = $successful * 4  # Estimate 4 images per successful prompt
                Write-Host "Total size: $([math]::Round($totalSize, 2)) MB"
                Write-Host "Total images: $totalImages (estimated)"
            } else {
                Write-Host "Total size: $([math]::Round($totalSize, 2)) MB"
                Write-Host "Total images: $totalImages"
            }
            
        } catch {
            Write-Warning "Could not calculate summary statistics: $($_.Exception.Message)"
            Write-Host "Total size: Unable to calculate"
            Write-Host "Total images: Unable to calculate"
        }
        
        Write-Host "Results saved to: $OutputDir"
    }

} catch {
    Write-Host ""
    Write-Host "=== BATCH FAILED ===" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}