az login
az acr login --name dtcontainerregister
docker tag videosearch:v2 dtcontainerregister.azurecr.io/videosearch:v2
docker push dtcontainerregister.azurecr.io/videosearch:v2
