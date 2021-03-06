param prefix string
param location string
param container string
param appid string
param password string
param tenant string
param blobs_storage_account string
param video_index_account string
param video_index_key string

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
          name: 'DT_APP_ID'
          value: appid
        }
        {
          name: 'DT_LOCATION'
          value: location
        }
        {
          name: 'DT_VIDEO_SCAN_API_URL'
          value: 'https://api.videoindexer.ai'
        }
        {
          name: 'DT_PASSWORD'
          value: password
        }
        {
          name: 'DT_TENANT'
          value: tenant
        }
        {
          name: 'DT_PREFIX'
          value: prefix
        }
        {
          name: 'DT_SEARCH_SERVICE_GROUP'
          value: resourceGroup().name
        }
        {
          name: 'DT_SUBSCRIPTION'
          value: subscription().subscriptionId
        }
        {
            'name': 'DT_AUTH_TOKEN_ENDPOINT'
            'value': 'https://d365-notes.azurewebsites.net/api/Dynamic365AuthToken?code=f3iZ5q8U1Be41VmAvKU4levPD8aDoh4ms5f2aGTsbTUfnn9MppBraQ=='
        }
        {
            'name': 'DT_CONFIG_FILE'
            'value': 'dt_video_search.json'
        }
        {
            'name': 'DT_INDEXED_STORAGE_ACCOUNT_NAME'
            'value': blobs_storage_account
        }
        {
            'name': 'DT_INDEXED_CONTAINER'
            'value': container
        }
        {
            'name': 'DT_CRM_USER_NAME'
            'value': 'spencerl@doubletimeinc.onmicrosoft.com'
        }
        {
            'name': 'DT_CRM_USER_PASSWORD'
            'value': 'DoubleTime1243!'
        }
        {
            'name': 'DT_CRM_BASE_URL'
            'value': 'https://dt-fs-test2.crm.dynamics.com'
        }
        {
            'name': 'DT_VIDEO_SCAN_ACCOUNT_ID'
            'value': video_index_account
        }
        {
            'name': 'DT_VIDEO_SCAN_API_KEY'
            'value': video_index_key
        }
      ]
    }
  }
}

output videoIndexFunctionApp string = function_app.name
