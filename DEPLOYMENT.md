# Deployment Instructions

## 🎯 Summary of Fixes Applied

### Issues Fixed:
1. **✅ Backend requirements.txt**: Removed git commands that caused build failures
2. **✅ Import path issues**: Fixed circular import by creating proper main.py entry point
3. **✅ Application structure**: Removed duplicate app_kernel.py file in root
4. **✅ Docker configuration**: Updated Dockerfile.azure to be more robust with fallback mechanisms
5. **✅ Environment setup**: Created proper .env configuration templates
6. **✅ Azure deployment**: Updated azure.yaml with complete service configuration
7. **✅ Frontend API URL**: Fixed hardcoded localhost URL to use environment variables

### Current Status:
- ✅ **Backend application**: Starts successfully without errors
- ✅ **Dependencies**: All Python packages install correctly  
- ✅ **Docker builds**: Dockerfile.azure uses robust pip fallback approach
- ✅ **GitHub Actions**: Deployment workflows are ready for automatic deployment
- ✅ **Environment configuration**: Proper .env templates created (not committed for security)
- ✅ **Frontend API connection**: Now uses configurable URL instead of hardcoded localhost

## 🚀 Deployment Options

### Option 1: 🤖 Automated Backend Deployment Script (NIEUWE FEATURE!)
**Snelle, betrouwbare productie-deployment met één bevestiging:**

```bash
# Geautomatiseerde deployment met bevestiging
./deploy-backend-auto.sh

# Voor CI/CD (skip confirmatie)
./deploy-backend-auto.sh --skip-confirm
```

**Voordelen:**
- ✅ Voorkomt handmatige fouten
- ✅ Automatische image tagging met timestamp en git hash
- ✅ Deployment verificatie en health checks
- ✅ Automatische rollback bij failures
- ✅ Uitgebreide logging en error handling
- ✅ Productie-veilige bevestiging

📖 **Volledige documentatie**: Zie `DEPLOYMENT_AUTOMATION.md`

### Option 2: Automatic Deployment via GitHub Actions
The repository has GitHub Actions workflows configured for automatic deployment:

1. **Backend deployment** (`deploy-container-backend.yml`): 
   - Triggers on pushes to main branch with backend changes
   - Deploys to Azure Container App `backend-aiagents-gov`
   - Uses Azure Container Registry `ca2a76f03945acr.azurecr.io`

2. **Frontend deployment** (`main_aiagentsgov.yml`):
   - Deploys Node.js frontend to Azure Web App `aiagentsgov`
   - **Now properly configured** with production API URL during build

**To deploy**: Merge this PR to main branch and the workflows will automatically deploy.

### Option 2: Manual Deployment using Azure Developer CLI (azd)
```bash
# Install Azure Developer CLI
# https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/

# Login to Azure
az login

# Deploy the application
azd up
```

### Option 3: Manual Docker Build and Push
```bash
# Build backend image
docker build -f src/backend/Dockerfile.azure -t backend:latest src/backend/

# Tag for your Azure Container Registry
docker tag backend:latest yourregistry.azurecr.io/backend:latest

# Push to registry
docker push yourregistry.azurecr.io/backend:latest

# Update Container App to use the new image
az containerapp update --name your-app --resource-group your-rg --image yourregistry.azurecr.io/backend:latest
```

## 🔧 Environment Variables Required for Production

Set these in your Azure Container App environment:

### Required Variables:
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
COSMOSDB_ENDPOINT=https://your-cosmos-endpoint.documents.azure.com:443/
COSMOSDB_DATABASE=macae
COSMOSDB_CONTAINER=memory
```

### Optional Variables:
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string
AZURE_AI_PROJECT_ENDPOINT=your-ai-project-endpoint
AZURE_AI_SUBSCRIPTION_ID=your-subscription-id
AZURE_AI_RESOURCE_GROUP=your-resource-group
AZURE_AI_PROJECT_NAME=your-project-name
BACKEND_API_URL=http://localhost:8000
FRONTEND_SITE_NAME=http://127.0.0.1:3000
```

### Frontend API URL Configuration:
The frontend now uses environment variables to configure the backend API URL:
- **Production builds**: Set `VITE_API_URL` in the GitHub Actions workflow
- **Development**: Uses `http://127.0.0.1:8000` as fallback
- **Custom deployments**: Set `VITE_API_URL` or `REACT_APP_API_URL` environment variables

Example for local development:
```bash
# src/frontend/.env (not committed)
VITE_API_URL=http://localhost:8000
```

## 📋 Next Steps

1. **Merge this PR** to trigger automatic deployment
2. **Monitor deployment** status in GitHub Actions
3. **Verify application** is running in Azure Portal
4. **Configure environment variables** for production use
5. **Test the deployed application** endpoints

## 🧪 Testing

- **Local testing**: `python main.py` - Application starts on http://localhost:8000
- **Health check**: Application includes health check middleware
- **API documentation**: Available at http://localhost:8000/docs
- **Frontend**: Available at http://localhost:3000 (when running frontend)

## 🔍 Verification

After deployment, verify:
- Application starts without errors
- API endpoints are accessible
- Health checks pass
- Environment variables are properly set
- Database connections work (if configured)

## 📞 Support

If you encounter issues:
1. Check GitHub Actions logs for deployment errors
2. Verify environment variables are set correctly
3. Check Azure Container App logs in Azure Portal
4. Ensure all required Azure resources are deployed