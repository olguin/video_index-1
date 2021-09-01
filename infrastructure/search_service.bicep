param prefix string
param location string

param searchServiceName string = '${prefix}ss'

targetScope = 'resourceGroup'

resource searchService 'Microsoft.Search/searchServices@2021-04-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
      bypass: 'None'
    }
    disableLocalAuth: false
    authOptions: {
      apiKeyOnly: {}
    }
    disabledDataExfiltrationOptions: []
    semanticSearch: 'disabled'
  }
}

output searchService string = searchService.name
