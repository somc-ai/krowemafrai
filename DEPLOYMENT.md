# Deployment Instructions

## Overview
This application has been fixed and is ready for deployment to Azure Container Apps.

## What was fixed:
1. **Backend requirements.txt**: Removed unnecessary git commands that were causing build issues
2. **Application entry point**: Fixed import path issues by creating a proper main.py entry point
3. **Environment configuration**: Added proper .env files for development and production configuration
4. **Azure deployment**: Updated azure.yaml with proper service configuration

## Current Status
✅ **Backend application**: Can start successfully without errors
✅ **Dependencies**: All Python packages install correctly  
✅ **Docker configuration**: Dockerfiles are properly configured
✅ **GitHub Actions**: Deployment workflows are set up and ready

## Deployment Options

### Option 1: Automatic Deployment via GitHub Actions (Recommended)
The repository has GitHub Actions workflows configured for automatic deployment:

1. **Backend deployment** (`deploy-backend-azure.yml`): 
   - Triggers on pushes to main branch with backend changes
   - Deploys to Azure Container App `camar01`
   - Uses Azure Container Registry `somcregistrysweden.azurecr.io`

2. **Frontend deployment** (`main_aiagentsgov.yml`):
   - Deploys Node.js frontend to Azure Web App `aiagentsgov`

**To deploy**: Push changes to the main branch and the workflows will automatically deploy.

### Option 2: Manual Deployment using Azure Developer CLI (azd)
1. Install Azure Developer CLI: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/
2. Login to Azure: `az login`
3. Deploy: `azd up`

### Option 3: Manual Docker Build and Push
1. Build backend image: `docker build -f src/backend/Dockerfile.azure -t backend:latest src/backend/`
2. Tag and push to your Azure Container Registry
3. Update Container App to use the new image

## Environment Variables Required for Production
Set these in your Azure Container App environment:

```bash
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
COSMOSDB_ENDPOINT=https://your-cosmos-endpoint.documents.azure.com:443/
COSMOSDB_DATABASE=macae
COSMOSDB_CONTAINER=memory
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string
AZURE_AI_PROJECT_ENDPOINT=your-ai-project-endpoint
```

## Next Steps
1. Merge this PR to trigger automatic deployment
2. Monitor deployment status in GitHub Actions
3. Verify application is running in Azure Portal
4. Set up proper environment variables for production use

## Testing
- Local testing: `python main.py` - Application starts on http://localhost:8000
- Health check: Application includes health check middleware
- API documentation: Available at http://localhost:8000/docs