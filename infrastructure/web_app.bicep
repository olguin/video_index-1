param prefix string
param webAppName string = '${prefix}-${uniqueString(resourceGroup().id)}' // Generate unique String for web app name
param sku string = 'P1V2' // The SKU of App Service Plan
param linuxFxVersion string = 'node|14-lts' // The runtime stack of web app
param location string = resourceGroup().location // Location for all resources
param repositoryUrl string = 'https://github.com/DoubleTimeEng/video_search'
param branch string = 'main'
param container string
param blobs_storage_account string

var appServicePlanName = toLower('AppServicePlan-${webAppName}')
var webSiteName = toLower('wapp-${webAppName}')

resource appServicePlan 'Microsoft.Web/serverfarms@2020-06-01' = {
  name: appServicePlanName
  location: location
  properties: {
    reserved: true
  }
  sku: {
    name: sku
  }
  kind: 'linux'
}

resource appService 'Microsoft.Web/sites@2020-06-01' = {
  name: webSiteName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: linuxFxVersion
     appSettings: [
        {
          name: 'DT_SEARCH_SERVICE_NAME'
          value: '${prefix}ss'
        }
        {
          name: 'DT_SEARCH_SERVICE_KEY'
          value: ''
        }
        {
          name: 'DT_ACS_WRAPPER_FUNCTION_URL'
          value: ''
        }
        {
          name: 'DT_API_VERSION'
          value: '2020-06-30'
        }
        {
          name: 'DT_SEARCH_SERVICE_INDEX'
          value: '${container}-in'
        }
        {
          name: 'DT_INDEXED_CONTAINER'
          value: 'https://${blobs_storage_account}.blob.core.windows.net/${container}'
        }

      ]
    }
  }
}

resource srcControls 'Microsoft.Web/sites/sourcecontrols@2021-01-01' = {
  name: '${appService.name}/web'
  properties: {
    repoUrl: repositoryUrl
    branch: branch
    isManualIntegration: true
  }
}

output name string = appService.name

