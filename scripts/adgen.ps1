function Invoke-AdGen {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$OutDirRoot = "$env:USERPROFILE\Downloads",
    [switch]$NoOpen
  )

  $gen = Invoke-RestMethod -Method Post http://localhost:8000/generate `
          -ContentType "application/json" -Body (@{prompt=$Prompt}|ConvertTo-Json)

  $run = $null
  if ($gen.detail.run_id -is [string]) { $run = $gen.detail.run_id }
  elseif ($gen.run_id -is [string])    { $run = $gen.run_id }
  elseif ($gen.run_id.run_id)          { $run = $gen.run_id.run_id }
  if (-not $run) {
    $s = ($gen | ConvertTo-Json -Depth 12)
    if ($s -match '"run_id"\s*:\s*"([A-Za-z0-9_-]{8,})"') { $run = $Matches[1] }
  }
  "RUN: $run"

  $null = Invoke-RestMethod -Method Post "http://localhost:8000/finalize/$run"

  $runOutDir = Join-Path $OutDirRoot ("run_" + $run)
  if (!(Test-Path $runOutDir)) { New-Item -ItemType Directory -Path $runOutDir | Out-Null }
  $zipName = "$run.zip"
  $zipFile = "$runOutDir.zip"
  $url     = "http://localhost:8000/download/$run?path=$zipName"

  $ok = $false
  foreach ($i in 1..12) {
    try {
      Invoke-WebRequest $url -OutFile $zipFile -UseBasicParsing -ErrorAction Stop | Out-Null
      $ok = $true; break
    } catch { Start-Sleep -Milliseconds 1000 }
  }

  if (-not $ok) {
    Write-Host "Download endpoint failed. Falling back to docker cp..."
    docker cp "adgen-api:/app/adgen/runs/$zipName" "$zipFile"
  }

  if (Test-Path $zipFile) {
    Expand-Archive $zipFile -DestinationPath $runOutDir -Force
    if (-not $NoOpen) { Start $runOutDir }
    return $runOutDir
  } else {
    throw "ZIP not found after retries and docker cp. Check 'docker logs -f adgen-api'."
  }
}
