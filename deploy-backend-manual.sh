#!/bin/bash
set -e

echo "🚀 Manual Backend Deployment to Container Apps"

# Variables
RESOURCE_GROUP="rg-info-2259"
CONTAINER_APP_NAME="backend-aiagents-gov"
ENVIRONMENT_NAME="managedEnvironment-rginfo2259-8048"
IMAGE_NAME="ca2a76f03945acr.azurecr.io/backend-aiagents-gov:latest"
REGISTRY_SERVER="ca2a76f03945acr.azurecr.io"

echo "📋 Creating Container App: $CONTAINER_APP_NAME"

# Create Container App
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image $IMAGE_NAME \
  --registry-server $REGISTRY_SERVER \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    AZURE_OPENAI_ENDPOINT="https://somc-ai-gov-openai.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="fake-key-will-be-set" \
    OPENAI_API_VERSION="2024-10-21" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002" \
    OTEL_PYTHON_LOG_CORRELATION="true" \
    OTEL_PYTHON_LOG_LEVEL="info" \
    PYTHON_ENV="production"

echo "✅ Backend deployed successfully!"

# Get Backend URL
BACKEND_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.latestRevisionFqdn" -o tsv)
echo "🔗 Backend URL: https://$BACKEND_URL"

echo "🔄 Now updating frontend to connect to backend..."

# Update Frontend with Backend URL
az containerapp update \
  --name frontend-aiagents-gov \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars BACKEND_API_URL="https://$BACKEND_URL"

echo "✅ Frontend updated with backend connection!"
echo "🎉 FULL STACK DEPLOYED AND CONNECTED!"
echo "Frontend: https://frontend-aiagents-gov--6x2uctg.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io"
echo "Backend: https://$BACKEND_URL"
