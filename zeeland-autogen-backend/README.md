# Zeeland Backend Deployment

This directory contains the Zeeland Autogen Backend application, deployed as an Azure Container App.

## Application Details

- **Technology**: FastAPI + Python 3.11
- **Port**: 8000
- **Endpoints**:
  - `/` - Service status
  - `/health` - Health check
  - `/api/agents` - Agents API

## Deployment

The application is automatically deployed to Azure Container Apps via GitHub Actions when changes are pushed to the `main` branch.

### Deployment Workflow

File: `.github/workflows/deploy-zeeland-backend-containerapp.yml`

**Configuration:**
- **Resource Group**: `aiagentsgov_group`
- **Container Registry**: `somcregistry.azurecr.io` (West Europe)
- **Container App**: `BackendAIGovNieuw`
- **Region**: West Europe
- **Port**: 8000 (with external ingress)

### Docker Images

Two Dockerfiles are available:
- `Dockerfile` - Standard Docker build
- `Dockerfile.azure` - Azure-optimized build with trusted PyPI hosts

### Manual Deployment

```bash
# Build the image
docker build -t zeeland-backend -f Dockerfile.azure .

# Run locally for testing
docker run -p 8000:8000 zeeland-backend

# Test the application
curl http://localhost:8000/health
```

### Migration from App Service

The previous deployment used Azure App Service (Web App). The new deployment uses Azure Container Apps for better scalability and containerization benefits.

**Old workflow**: `main_backendaigovnieuw.yml` (now deprecated)
**New workflow**: `deploy-zeeland-backend-containerapp.yml`

## Environment Variables

Currently the application runs without external dependencies. Environment variables can be added to the Container App configuration as needed.

## Monitoring

- Health check endpoint: `/health`
- Application logs available in Azure Container Apps
- Automatic scaling: 1-3 replicas
- Resource allocation: 0.25 CPU, 0.5Gi memory