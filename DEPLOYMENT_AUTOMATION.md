# 🚀 Automated Backend Deployment Guide

Dit document beschrijft hoe je de geautomatiseerde backend deployment gebruikt voor Azure Container Apps.

## 📋 Overzicht

Het `deploy-backend-auto.sh` script automatiseert het volledige deployment proces voor de backend:
- ✅ Builden van Docker container
- ✅ Pushen naar Azure Container Registry
- ✅ Deployen naar Azure Container App
- ✅ Verificatie van deployment status
- ✅ Automatische rollback bij failures

## 🔧 Vereisten

Voordat je het script gebruikt, zorg ervoor dat je het volgende hebt:

### Software
- **Azure CLI** geïnstalleerd en ingelogd (`az login`)
- **Docker** geïnstalleerd en draaiend
- **Git** voor versie tracking

### Azure Toegang
- Toegang tot Azure Container Registry: `ca2a76f03945acr.azurecr.io`
- Toegang tot Resource Group: `rg-info-2259`
- Juiste permissions voor Container Apps

## 🚀 Gebruik

### Basis Deployment
```bash
./deploy-backend-auto.sh
```

Dit commando zal:
1. Prerequisites controleren
2. Azure login verificeren
3. Deployment details tonen
4. **Bevestiging vragen** voor productie deployment
5. Docker image builden met timestamp tag
6. Image pushen naar ACR
7. Container App updaten of aanmaken
8. Deployment verificeren
9. Status rapport tonen

### Opties

#### Help Informatie
```bash
./deploy-backend-auto.sh --help
```

#### Skip Bevestiging (Voorzichtig gebruiken!)
```bash
./deploy-backend-auto.sh --skip-confirm
```

## 🎯 Deployment Details

### Azure Configuratie
- **Container Registry**: `ca2a76f03945acr.azurecr.io`
- **Resource Group**: `rg-info-2259`
- **Container App**: `backend-aiagents-gov`
- **Environment**: `managedEnvironment-rginfo2259-8048`

### Image Tagging
Het script gebruikt een intelligente tagging strategie:
- **Timestamp**: `YYYYMMDD-HHMMSS`
- **Git Hash**: Korte commit hash
- **Voorbeeld**: `20250122-143052-a1b2c3d`
- **Latest Tag**: Altijd ook tagged als `latest`

### Container Configuratie
- **CPU**: 1.0 cores
- **Memory**: 2.0Gi
- **Replicas**: 1-3 (auto-scaling)
- **Port**: 8000
- **Ingress**: External
- **Health Check**: `/health` endpoint

## 🔧 Environment Variables

Het script configureert automatisch alle benodigde environment variables:

```bash
PORT=8000
AZURE_OPENAI_ENDPOINT=https://somc-ai-gov-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_AI_SUBSCRIPTION_ID=05cc117e-29ea-49f3-9428-c5d042340a91
AZURE_AI_RESOURCE_GROUP=rg-info-2259
AZURE_AI_PROJECT_NAME=ai-project-default
AZURE_AI_AGENT_ENDPOINT=https://somc-ai-gov-openai.openai.azure.com/
OTEL_PYTHON_LOG_CORRELATION=true
OTEL_PYTHON_LOG_LEVEL=info
PYTHON_ENV=production
```

## 🛡️ Veiligheidsfeatures

### Bevestiging Vereist
Het script vraagt **altijd** om bevestiging voordat het naar productie deployed:
```
⚠️  This will deploy to PRODUCTION environment!
⚠️  Container App: backend-aiagents-gov in Resource Group: rg-info-2259
🤔 Are you sure you want to continue? (yes/no):
```

### Automatische Rollback
Bij deployment failures wordt automatisch teruggerold naar de vorige working image.

### Error Handling
- Uitgebreide error checking op elke stap
- Duidelijke error messages met emoji's
- Exit codes voor scripting integratie

## 📊 Output Voorbeeld

```
🚀 Starting automated backend deployment...
==================================================================
🚀 AZURE CONTAINER APP DEPLOYMENT
==================================================================
📦 Container App: backend-aiagents-gov
🏷️  Resource Group: rg-info-2259
🐳 Image: ca2a76f03945acr.azurecr.io/backend-aiagents-gov:20250122-143052-a1b2c3d
📂 Backend Directory: src/backend
🐋 Dockerfile: src/backend/Dockerfile.azure
⏰ Timestamp: 20250122-143052
==================================================================
ℹ️  Checking prerequisites...
✅ Prerequisites check passed
ℹ️  Verifying Azure login...
✅ Logged in to Azure subscription: Your Subscription
⚠️  This will deploy to PRODUCTION environment!
⚠️  Container App: backend-aiagents-gov in Resource Group: rg-info-2259
🤔 Are you sure you want to continue? (yes/no): yes
ℹ️  Starting deployment process...
ℹ️  Building Docker image...
✅ Docker image built successfully
ℹ️  Logging in to Azure Container Registry...
✅ Successfully logged in to ACR: ca2a76f03945acr
ℹ️  Pushing image to Azure Container Registry...
✅ Image pushed successfully to ACR
ℹ️  Deploying to Azure Container App...
✅ Container App updated successfully
ℹ️  Verifying deployment...
✅ Container App is available at: https://backend-aiagents-gov.westeurope-01.azurecontainerapps.io
✅ Health check passed
==================================================================
🎉 DEPLOYMENT SUMMARY
==================================================================
✅ Container App: backend-aiagents-gov
✅ Resource Group: rg-info-2259
✅ Image: ca2a76f03945acr.azurecr.io/backend-aiagents-gov:20250122-143052-a1b2c3d
✅ Timestamp: 20250122-143052
🔗 URL: https://backend-aiagents-gov.westeurope-01.azurecontainerapps.io
==================================================================
✅ Backend deployment completed successfully!
🎉 Deployment process completed successfully!
```

## 🔍 Troubleshooting

### Veelvoorkomende Problemen

#### Azure Login Issues
```bash
az login
az account set --subscription "Your-Subscription-ID"
```

#### Docker Daemon Issues
```bash
sudo systemctl start docker
# of voor Windows/Mac: start Docker Desktop
```

#### Permission Issues
```bash
# Controleer Azure RBAC permissions
az role assignment list --assignee your-email@domain.com
```

#### Container Registry Access
```bash
# Test ACR login
az acr login --name ca2a76f03945acr
```

### Log Analysis
Het script geeft uitgebreide logging met kleurgecodeerde output:
- 🔵 **Blauw**: Informatie
- 🟢 **Groen**: Succes
- 🟡 **Geel**: Waarschuwingen
- 🔴 **Rood**: Errors

### Manual Rollback
Als automatische rollback faalt:
```bash
# Lijst beschikbare images
az acr repository show-tags --name ca2a76f03945acr --repository backend-aiagents-gov

# Manual rollback naar specifieke tag
az containerapp update \
  --name backend-aiagents-gov \
  --resource-group rg-info-2259 \
  --image ca2a76f03945acr.azurecr.io/backend-aiagents-gov:YOUR-PREVIOUS-TAG
```

## 📈 Best Practices

1. **Test Lokaal Eerst**: Altijd lokaal testen voordat je deployed
2. **Check Git Status**: Zorg dat je code gecommit is
3. **Monitor Deployments**: Hou deployment logs in de gaten
4. **Backup Strategy**: Houd altijd een working image tag bij de hand
5. **Scheduled Deployments**: Gebruik tijdens onderhoudsvensters

## 🔗 Gerelateerde Scripts

- `deploy-backend-manual.sh`: Manual deployment voor testing
- `deploy-manual.sh`: Volledige stack deployment
- GitHub Actions: Automatische CI/CD workflows

## 📞 Support

Voor vragen of problemen:
1. Check dit document eerst
2. Controleer Azure Portal logs
3. Bekijk Container App logs in Azure
4. Contact DevOps team voor complexe issues