#!/bin/bash
# Build, push en deploy backend-aiagents-gov container image naar Azure Container App

set -e

# Vul deze variabelen aan met jouw registry en resource group
ACR_NAME="<jouw-acr-naam>"
RESOURCE_GROUP="rg-info-2259"
CONTAINER_APP="backend-aiagents-gov"
IMAGE_NAME="$ACR_NAME.azurecr.io/$CONTAINER_APP:latest"

# 1. Build Docker image

echo "Building Docker image..."
docker build -t $IMAGE_NAME src/backend

# 2. Login bij Azure Container Registry

echo "Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

# 3. Push image naar ACR

echo "Pushing image to ACR..."
docker push $IMAGE_NAME

# 4. Update Azure Container App met nieuwe image

echo "Updating Azure Container App..."
az containerapp update --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --image $IMAGE_NAME

echo "Deployment voltooid!"
