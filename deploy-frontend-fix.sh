#!/bin/bash
# Quick deployment script to update the frontend on Azure

echo "🚀 Starting frontend deployment to Azure..."

# Variables
RESOURCE_GROUP="rg-aiagents-gov"
FRONTEND_APP_NAME="frontend-aiagents-gov" 
BACKEND_URL="https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io"

echo "📝 Resource Group: $RESOURCE_GROUP"
echo "📝 Frontend App: $FRONTEND_APP_NAME"
echo "📝 Backend URL: $BACKEND_URL"

# Build and deploy the frontend container
echo "🔨 Building and deploying frontend container..."

# Update the container app with the latest code and correct environment variables
az containerapp update \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars "BACKEND_API_URL=$BACKEND_URL" "AUTH_ENABLED=false" \
  --source .

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployment completed successfully!"
    echo "🌐 Frontend URL: https://frontend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/"
    echo "🔧 Config endpoint: https://frontend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/config"
    echo "🩺 Health endpoint: https://frontend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/health"
    echo "🐛 Debug endpoint: https://frontend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/debug/build-contents"
else
    echo "❌ Frontend deployment failed!"
    exit 1
fi

echo "🎉 Deployment complete!"
