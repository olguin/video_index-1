param prefix string
param location string
param container string
param appid string
param password string
param tenant string

param function_app_name string = '${prefix}-video-index'
param appservice_plan_name string = '${prefix}-video-index-plan'
param app_insights_name string = '${prefix}-video-index-insights'
param storage_account_name string = '${prefix}ac'

var unique_string = uniqueString(subscription().id)
var unique_function_name = '${function_app_name}-${unique_string}'
var unique_storage_name = '${storage_account_name}0${unique_string}'
param dockerRegistryHost string = 'dtcontainerregister.azurecr.io'
param tokenDocker string = 'Gz0sYqjmJxTPJHiCkMwI7zNZ3Rdl688/'

targetScope = 'resourceGroup'

resource storage_account 'Microsoft.Storage/storageAccounts@2019-06-01' = {
  name: unique_storage_name
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_ZRS'
  }
  properties: {
    accessTier: 'Hot'
  }
}

resource app_insights 'Microsoft.Insights/components@2015-05-01' = {
  name: app_insights_name
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource appservice_plan 'Microsoft.Web/serverfarms@2020-12-01' = {
  name: appservice_plan_name
  location: location
  kind: 'elastic'
  properties: {
    reserved: true
  }
  sku: {
    name: 'EP1'
    tier: 'ElasticPremium'
  }
}

resource function_app 'Microsoft.Web/sites@2020-12-01' = {
  name: unique_function_name
  location: location
  kind: 'functionapp,linux,container'
  dependsOn: [
    storage_account
    appservice_plan
    app_insights
  ]
  properties: {
    serverFarmId: appservice_plan.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|dtcontainerregister.azurecr.io/videosearch:v2'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage_account.name};AccountKey=${listKeys(storage_account.id, '2019-06-01').keys[0].value}'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: reference(app_insights.id, '2015-05-01').InstrumentationKey
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~3'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${dockerRegistryHost}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: 'dtContainerRegister'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: tokenDocker
        }
        {
          name: 'APP_ID'
          value: appid
        }
        {
          name: 'PASSWORD'
          value: password
        }
        {
          name: 'TENANT'
          value: tenant
        }
        {
          name: 'PREFIX'
          value: prefix
        }
        {
          name: 'GROUP'
          value: resourceGroup().name
        }
        {
          name: 'SUBSCRIPTION'
          value: subscription().subscriptionId
        }
        {
          name: 'CONTAINER'
          value: container
        }
      ]
    }
  }
}

output videoIndexFunctionApp string = function_app.name
