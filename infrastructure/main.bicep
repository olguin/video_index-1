param prefix string
param location string
param container string
param appid string
param password string
param tenant string

param resource_group_name string = '${prefix}rg'

var unique_string = uniqueString(subscription().id)
var unique_group_name = '${resource_group_name}0${unique_string}'

targetScope = 'subscription'

resource resource_group 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: unique_group_name
  location: location
}

module functionAppModule './function_app.bicep' = {
  name: 'video-index-function-app-module'
  scope: resource_group
  params: {
    prefix: prefix
    location: location
    appid: appid
    password: password
    tenant: tenant
    container: container
  }
}

module searchServiceModule './search_service.bicep' = {
  name: 'search-service-app-module'
  scope: resource_group
  params: {
    prefix: prefix
    location: location
  }
}

output videoIndexFunctionApp string = functionAppModule.outputs.videoIndexFunctionApp
output searchService string = searchServiceModule.outputs.searchService
output resourceGroup string = resource_group.name
