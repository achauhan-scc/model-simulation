[CmdletBinding()]
param(
    [string]$EnvironmentName = "dev",
    [string]$ResourceGroupName = ""
)

$ErrorActionPreference = "Stop"
$simulatorRoot = Split-Path -Parent $PSScriptRoot
$stateFile = Join-Path $simulatorRoot ".deployment.json"

if ([string]::IsNullOrWhiteSpace($ResourceGroupName) -and (Test-Path $stateFile)) {
    $state = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
    $ResourceGroupName = $state.resourceGroup
}

if ([string]::IsNullOrWhiteSpace($ResourceGroupName)) {
    throw "Provide -ResourceGroupName or deploy first so .deployment.json exists."
}

Write-Host "Deleting resource group $ResourceGroupName..."
az group delete --name $ResourceGroupName --yes --no-wait

if (Test-Path $stateFile) {
    Remove-Item -LiteralPath $stateFile
}

Write-Host "Deletion started for environment $EnvironmentName."
