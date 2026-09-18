targetScope = 'subscription'

@description('Short environment name used in resource names.')
@minLength(2)
@maxLength(12)
param environmentName string = 'dev'

@description('Azure region for the simulator resources.')
param location string = deployment().location

@description('Resource group name. Leave empty to use the generated name.')
param resourceGroupName string = ''

@description('SSH public key used by the AKS Linux nodes.')
param sshPublicKey string

@description('AKS system node VM size.')
param nodeVmSize string = 'Standard_D2s_v5'

@description('Number of AKS system nodes.')
@minValue(1)
@maxValue(3)
param nodeCount int = 1

@description('Linux administrator username for the AKS nodes.')
param linuxAdminUsername string = 'azureuser'

@description('Tags applied to deployed resources.')
param tags object = {
  workload: 'agent-model-simulator'
  environment: environmentName
  purpose: 'hackathon'
}

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var generatedResourceGroupName = 'rg-model-sim-${environmentName}-${resourceToken}'
var effectiveResourceGroupName = empty(resourceGroupName)
  ? generatedResourceGroupName
  : resourceGroupName

resource resourceGroup 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: effectiveResourceGroupName
  location: location
  tags: tags
}

module simulator './modules/simulator.bicep' = {
  name: 'model-simulator-${environmentName}'
  scope: resourceGroup
  params: {
    environmentName: environmentName
    location: location
    resourceToken: resourceToken
    sshPublicKey: sshPublicKey
    nodeVmSize: nodeVmSize
    nodeCount: nodeCount
    linuxAdminUsername: linuxAdminUsername
    tags: tags
  }
}

output resourceGroupName string = resourceGroup.name
output aksClusterName string = simulator.outputs.aksClusterName
output containerRegistryName string = simulator.outputs.containerRegistryName
output containerRegistryLoginServer string = simulator.outputs.containerRegistryLoginServer
output logAnalyticsWorkspaceName string = simulator.outputs.logAnalyticsWorkspaceName
