[CmdletBinding()]
param(
    [string]$EnvironmentName = "dev",
    [string]$Location = "eastus2",
    [string]$ResourceGroupName = "",
    [string]$ImageTag = "dev",
    [string]$ApiKey = "",
    [string]$SshPublicKeyPath = "$HOME\.ssh\id_rsa.pub"
)

$ErrorActionPreference = "Stop"
$simulatorRoot = Split-Path -Parent $PSScriptRoot
$infraFile = Join-Path $simulatorRoot "infra\main.bicep"
$manifestFile = Join-Path $simulatorRoot "k8s\deployment.yaml"
$toolsDirectory = Join-Path $simulatorRoot ".tools"
$kubectl = Join-Path $toolsDirectory "kubectl.exe"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required."
}

$containerServiceProviderState = az provider show `
    --namespace Microsoft.ContainerService `
    --query registrationState `
    --output tsv
if ($containerServiceProviderState -ne "Registered") {
    Write-Host "Registering Microsoft.ContainerService provider..."
    az provider register `
        --namespace Microsoft.ContainerService `
        --wait `
        --output none
}

$account = az account show --output json | ConvertFrom-Json
if (-not $account.id) {
    throw "No active Azure subscription. Run 'az login' and select a subscription."
}

if (-not (Test-Path -LiteralPath $SshPublicKeyPath)) {
    $privateKeyPath = [IO.Path]::ChangeExtension($SshPublicKeyPath, $null)
    $privateKeyDirectory = Split-Path -Parent $privateKeyPath
    New-Item -ItemType Directory -Path $privateKeyDirectory -Force | Out-Null
    & ssh-keygen -t rsa -b 4096 -f $privateKeyPath -N '""'
}

$sshPublicKey = (Get-Content -LiteralPath $SshPublicKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($sshPublicKey)) {
    throw "SSH public key is empty: $SshPublicKeyPath"
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $ApiKey = [Convert]::ToBase64String($bytes)
}

Write-Host "Validating Bicep template..."
az bicep build --file $infraFile --stdout | Out-Null

$deploymentName = "model-simulator-$EnvironmentName"
$deploymentArguments = @(
    "deployment", "sub", "create",
    "--name", $deploymentName,
    "--location", $Location,
    "--template-file", $infraFile,
    "--parameters",
    "environmentName=$EnvironmentName",
    "location=$Location",
    "sshPublicKey=$sshPublicKey",
    "--output", "json"
)
if (-not [string]::IsNullOrWhiteSpace($ResourceGroupName)) {
    $deploymentArguments += @("resourceGroupName=$ResourceGroupName")
}

Write-Host "Provisioning AKS, ACR, and monitoring resources..."
$deployment = az @deploymentArguments | ConvertFrom-Json
$outputs = $deployment.properties.outputs
$resourceGroup = $outputs.resourceGroupName.value
$clusterName = $outputs.aksClusterName.value
$registryName = $outputs.containerRegistryName.value
$loginServer = $outputs.containerRegistryLoginServer.value
$image = "$loginServer/model-simulator:$ImageTag"

Write-Host "Building image in Azure Container Registry..."
az acr build `
    --registry $registryName `
    --image "model-simulator:$ImageTag" `
    $simulatorRoot `
    --output none

New-Item -ItemType Directory -Path $toolsDirectory -Force | Out-Null
if (-not (Test-Path -LiteralPath $kubectl)) {
    Write-Host "Installing kubectl locally..."
    az aks install-cli --install-location $kubectl --output none
}

Write-Host "Loading AKS credentials..."
az aks get-credentials `
    --resource-group $resourceGroup `
    --name $clusterName `
    --overwrite-existing `
    --output none

Write-Host "Creating simulator API-key secret..."
& $kubectl create secret generic model-simulator-secrets `
    "--from-literal=api-key=$ApiKey" `
    --dry-run=client `
    -o yaml |
    & $kubectl apply -f -
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the Kubernetes secret."
}

Write-Host "Deploying simulator image $image..."
$manifest = (Get-Content -LiteralPath $manifestFile -Raw).Replace(
    "MODEL_SIMULATOR_IMAGE",
    $image
)
$manifest | & $kubectl apply -f -
if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply the Kubernetes manifest."
}

& $kubectl rollout status deployment/model-simulator --timeout=5m
if ($LASTEXITCODE -ne 0) {
    throw "The model-simulator deployment did not become ready."
}

$externalAddress = $null
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    $externalAddress = & $kubectl get service model-simulator `
        -o "jsonpath={.status.loadBalancer.ingress[0].ip}"
    if ([string]::IsNullOrWhiteSpace($externalAddress)) {
        $externalAddress = & $kubectl get service model-simulator `
            -o "jsonpath={.status.loadBalancer.ingress[0].hostname}"
    }
    if (-not [string]::IsNullOrWhiteSpace($externalAddress)) {
        break
    }
    Start-Sleep -Seconds 5
}

if ([string]::IsNullOrWhiteSpace($externalAddress)) {
    throw "The load balancer did not receive an external address."
}

$endpoint = "http://$externalAddress"
$deploymentState = @{
    resourceGroup = $resourceGroup
    clusterName = $clusterName
    registryName = $registryName
    image = $image
    endpoint = $endpoint
}
$stateFile = Join-Path $simulatorRoot ".deployment.json"
$deploymentState | ConvertTo-Json | Set-Content -LiteralPath $stateFile

Write-Host ""
Write-Host "Simulator endpoint: $endpoint"
Write-Host "API key is available only in this process output. Store it securely."
Write-Host "SIMULATOR_API_KEY=$ApiKey"
Write-Host ""
Write-Host "Run the smoke test:"
Write-Host ".\scripts\Test-RefundScenario.ps1 -Endpoint '$endpoint' -ApiKey '<key>'"
