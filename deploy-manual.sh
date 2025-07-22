#!/bin/bash
set -e

echo "🚀 Manual Container Apps Deployment Script"
echo "=========================================="

# Configuration
RESOURCE_GROUP="rg-info-2259"
LOCATION="westeurope"
ENVIRONMENT_NAME="managedEnvironment-rginfo2259-8048"
REGISTRY_NAME="somcregistry"
REGISTRY_LOGIN_SERVER="somcregistry-hec2c3cahcgxg8bb.azurecr.io"
BACKEND_APP_NAME="backend-aiagents-gov"
FRONTEND_APP_NAME="frontend-aiagents-gov"

# Check if logged in
echo "🔐 Checking Azure login..."
if ! az account show &> /dev/null; then
    echo "❌ Please login first: az login"
    exit 1
fi

echo "✅ Azure login confirmed"

# Login to registry
echo "🐳 Logging in to Container Registry..."
az acr login --name $REGISTRY_NAME

# Build and push backend
echo "🏗️  Building Backend Docker image..."
cd /workspaces/krowemafrai
docker build -t $REGISTRY_LOGIN_SERVER/backend-aiagents-gov:latest -f src/backend/Dockerfile.azure .
docker push $REGISTRY_LOGIN_SERVER/backend-aiagents-gov:latest

# Deploy backend
echo "🚀 Deploying Backend Container App..."
if az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "📝 Updating existing Backend Container App..."
    az containerapp update \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $REGISTRY_LOGIN_SERVER/backend-aiagents-gov:latest
else
    echo "🆕 Creating new Backend Container App..."
    az containerapp create \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $REGISTRY_LOGIN_SERVER/backend-aiagents-gov:latest \
        --registry-server $REGISTRY_LOGIN_SERVER \
        --cpu 1.0 \
        --memory 2.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --target-port 8000 \
        --ingress external \
        --env-vars \
            "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
            "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY" \
            "OPENAI_API_VERSION=2024-10-21" \
            "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o" \
            "AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002" \
            "OTEL_PYTHON_LOG_CORRELATION=true" \
            "OTEL_PYTHON_LOG_LEVEL=info" \
            "PYTHON_ENV=production"
fi

# Get backend URL
BACKEND_URL=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
echo "✅ Backend URL: https://$BACKEND_URL"

# Build and push frontend
echo "🏗️  Building Frontend Docker image..."
cd src/frontend
docker build -t $REGISTRY_LOGIN_SERVER/frontend-aiagents-gov:latest -f Dockerfile .
docker push $REGISTRY_LOGIN_SERVER/frontend-aiagents-gov:latest
cd ../..

# Deploy frontend
echo "🚀 Deploying Frontend Container App..."
if az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "📝 Updating existing Frontend Container App..."
    az containerapp update \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $REGISTRY_LOGIN_SERVER/frontend-aiagents-gov:latest \
        --set-env-vars "BACKEND_API_URL=https://$BACKEND_URL"
else
    echo "🆕 Creating new Frontend Container App..."
    az containerapp create \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $REGISTRY_LOGIN_SERVER/frontend-aiagents-gov:latest \
        --registry-server $REGISTRY_LOGIN_SERVER \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --target-port 3000 \
        --ingress external \
        --env-vars "BACKEND_API_URL=https://$BACKEND_URL"
fi

# Get frontend URL
FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo "Backend URL:  https://$BACKEND_URL"
echo "Frontend URL: https://$FRONTEND_URL"
echo ""
echo "Test your deployment:"
echo "curl https://$BACKEND_URL/health"
echo "open https://$FRONTEND_URL"
