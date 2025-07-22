# 🚀 Automated Backend Deployment Guide

Dit document beschrijft hoe je de **verbeterde** geautomatiseerde backend deployment gebruikt voor Azure Container Apps.

## 📋 Overzicht

Het `deploy-backend-auto.sh` script automatiseert het volledige deployment proces voor de backend:
- ✅ **Configuratie management** met externe config file
- ✅ **Dry-run mode** voor veilig testen
- ✅ Builden van Docker container met optimale tagging
- ✅ Pushen naar Azure Container Registry
- ✅ Deployen naar Azure Container App
- ✅ **Uitgebreide validatie** van prerequisites
- ✅ Verificatie van deployment status
- ✅ Automatische rollback bij failures
- ✅ **Consistente environment variables** met andere deployment methodes

## ✨ Nieuwe Features

### 🔧 Configuration Management
Alle configuratie is nu gecentraliseerd in `deployment-config.env`:
- Consistente instellingen tussen verschillende deployment methodes
- Eenvoudig aanpasbaar voor verschillende omgevingen
- Geen hardcoded waarden meer in het script

### 🧪 Dry-Run Mode
Test je deployment zonder daadwerkelijke wijzigingen:
```bash
./deploy-backend-auto.sh --dry-run
```
- Valideert alle prerequisites
- Toont wat er zou worden gedeployed
- Geen echte Azure resources worden aangepast
- Perfect voor testing en validatie

### 🔍 Verbeterde Validatie
- Controleert Docker daemon status
- Valideert alle configuratie variabelen
- Uitgebreide error handling met rollback
- Consistency checks tussen environment variables

## 🔧 Vereisten

Voordat je het script gebruikt, zorg ervoor dat je het volgende hebt:

### Software
- **Azure CLI** geïnstalleerd en ingelogd (`az login`)
- **Docker** geïnstalleerd en draaiend
- **Git** voor versie tracking
- **Bash** 4.0+ voor script uitvoering

### Azure Toegang
- Toegang tot Azure Container Registry: `ca2a76f03945acr.azurecr.io`
- Toegang tot Resource Group: `rg-info-2259`
- Juiste permissions voor Container Apps
- Active Azure subscription

### Configuratie
- `deployment-config.env` file met alle benodigde instellingen
- Consistente environment variables setup

## 🚀 Gebruik

### Basis Deployment
```bash
./deploy-backend-auto.sh
```

Dit commando zal:
1. **Configuratie laden** van `deployment-config.env`
2. Prerequisites controleren (Azure CLI, Docker, files)
3. Azure login verificeren
4. Deployment details tonen
5. **Bevestiging vragen** voor productie deployment
6. Docker image builden met timestamp tag
7. Image pushen naar ACR
8. Container App updaten of aanmaken met **alle** environment variables
9. Deployment verificeren met health check
10. Status rapport tonen

### Opties

#### Help Informatie
```bash
./deploy-backend-auto.sh --help
```

#### Dry-Run Mode (Nieuw!)
```bash
./deploy-backend-auto.sh --dry-run
```
- **Veilig testen** zonder echte deployment
- Valideert alle instellingen
- Toont wat er zou gebeuren
- Geen Azure resources worden aangepast

#### Skip Bevestiging (Voorzichtig gebruiken!)
```bash
./deploy-backend-auto.sh --skip-confirm
```
- Voor CI/CD pipelines
- Geen handmatige bevestiging vereist
- **Gebruik alleen in geautomatiseerde omgevingen**

#### Custom Configuration
```bash
./deploy-backend-auto.sh --config custom-config.env
```
- Gebruik alternatieve configuratie file
- Handig voor verschillende omgevingen (dev/staging/prod)

## 🎯 Deployment Details

### Azure Configuratie (van config file)
- **Container Registry**: `ca2a76f03945acr.azurecr.io`
- **Resource Group**: `rg-info-2259`
- **Container App**: `backend-aiagents-gov`
- **Environment**: `managedEnvironment-rginfo2259-8048`
- **Location**: `westeurope`

### Image Tagging Strategie
Het script gebruikt een intelligente tagging strategie:
- **Timestamp**: `YYYYMMDD-HHMMSS`
- **Git Hash**: Korte commit hash
- **Voorbeeld**: `20250122-143052-a1b2c3d`
- **Latest Tag**: Altijd ook tagged als `latest`

### Container Configuratie
- **CPU**: 1.0 cores (configureerbaar)
- **Memory**: 2.0Gi (configureerbaar)
- **Replicas**: 1-3 (auto-scaling, configureerbaar)
- **Port**: 8000 (configureerbaar)
- **Ingress**: External
- **Health Check**: `/health` endpoint

## 🔧 Environment Variables

Het script configureert automatisch **alle** benodigde environment variables uit de config file:

```bash
# Application
PORT=8000

# Azure OpenAI (Gecorrigeerde configuratie)
AZURE_OPENAI_ENDPOINT=https://somc-ai-gov-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Azure AI Project
AZURE_AI_SUBSCRIPTION_ID=05cc117e-29ea-49f3-9428-c5d042340a91
AZURE_AI_RESOURCE_GROUP=rg-info-2259
AZURE_AI_PROJECT_NAME=ai-project-default
AZURE_AI_AGENT_ENDPOINT=https://somc-ai-gov-openai.openai.azure.com/

# Service URLs (Nieuw!)
BACKEND_API_URL=https://backend-aiagents-gov.westeurope-01.azurecontainerapps.io
FRONTEND_SITE_NAME=https://frontend-aiagents-gov.westeurope-01.azurecontainerapps.io

# Monitoring & Logging
OTEL_PYTHON_LOG_CORRELATION=true
OTEL_PYTHON_LOG_LEVEL=info
PYTHON_ENV=production
```

## 🛡️ Veiligheidsfeatures

### Bevestiging Vereist
Het script vraagt **altijd** om bevestiging voordat het naar productie deployed (tenzij `--skip-confirm`):
```
⚠️  This will deploy to PRODUCTION environment!
⚠️  Container App: backend-aiagents-gov in Resource Group: rg-info-2259
⚠️  Image: ca2a76f03945acr.azurecr.io/backend-aiagents-gov:20250122-143052-a1b2c3d
🤔 Are you sure you want to continue? (yes/no):
```

### Dry-Run Mode
Test **veilig** zonder echte deployment:
- Valideert alle prerequisites
- Toont deployment plan
- Geen echte Azure wijzigingen
- Perfect voor CI/CD validation

### Automatische Rollback
Bij deployment failures wordt automatisch teruggerold naar de vorige working image.

### Uitgebreide Error Handling
- Validation op elke stap
- Duidelijke error messages met emoji's
- Docker daemon checks
- Configuration validation
- Azure connectivity tests

## 📊 Output Voorbeeld

### Standaard Deployment
```
✅ Configuration loaded from: deployment-config.env
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
```

### Dry-Run Output
```
🧪 DRY RUN SUMMARY
==================================================================
✅ Container App: backend-aiagents-gov
✅ Resource Group: rg-info-2259
✅ Image: ca2a76f03945acr.azurecr.io/backend-aiagents-gov:20250122-143052-a1b2c3d
✅ Timestamp: 20250122-143052
🔗 Expected URL: https://backend-aiagents-gov.westeurope-01.azurecontainerapps.io
==================================================================
✅ Dry run completed successfully! No actual deployment was performed.
```

## 🔍 Troubleshooting

### Veelvoorkomende Problemen

#### Configuration Issues
```bash
# Check configuration file
cat deployment-config.env
# Test with dry-run
./deploy-backend-auto.sh --dry-run
```

#### Azure Login Issues
```bash
az login
az account set --subscription "Your-Subscription-ID"
# Test connection
az account show
```

#### Docker Issues
```bash
# Check Docker daemon
docker info
# Start Docker (if needed)
sudo systemctl start docker  # Linux
# or start Docker Desktop on Windows/Mac
```

#### Permission Issues
```bash
# Check Azure RBAC permissions
az role assignment list --assignee your-email@domain.com
# Test ACR access
az acr login --name ca2a76f03945acr
```

### Configuration Validation
Het script valideert nu automatisch:
- Alle benodigde configuratie variabelen
- Docker daemon status
- Azure CLI installation
- File paths en permissions

### Dry-Run voor Debugging
Gebruik dry-run mode om issues te identificeren:
```bash
./deploy-backend-auto.sh --dry-run
```

## 📈 Best Practices

1. **Gebruik Dry-Run Eerst**: Test altijd met `--dry-run` voordat je echt deployed
2. **Check Configuration**: Valideer `deployment-config.env` na wijzigingen
3. **Monitor Deployments**: Hou deployment logs in de gaten in Azure Portal
4. **Version Control**: Commit code wijzigingen voordat je deployed
5. **Backup Strategy**: Houd altijd een working image tag bij de hand
6. **Scheduled Deployments**: Gebruik tijdens onderhoudsvensters
7. **Environment Specific**: Gebruik verschillende config files voor dev/staging/prod

## 🔗 Gerelateerde Scripts

- `deploy-backend-manual.sh`: Manual deployment voor ad-hoc testing
- `deploy-manual.sh`: Volledige stack deployment
- `deployment-config.env`: **Nieuwe** centralized configuration
- GitHub Actions: Automatische CI/CD workflows (nu consistent met script)

## 📞 Support

Voor vragen of problemen:
1. **Test eerst met dry-run**: `./deploy-backend-auto.sh --dry-run`
2. Check dit document en configuration
3. Controleer Azure Portal logs
4. Bekijk Container App logs in Azure
5. Contact DevOps team voor complexe issues

## 🆕 Changelog

### Versie 2.0 (Huidige)
- ✅ **Configuration management** met externe file
- ✅ **Dry-run mode** voor veilig testen
- ✅ **Uitgebreide validatie** van prerequisites
- ✅ **Consistente environment variables** met GitHub Actions
- ✅ **Verbeterde error handling** en logging
- ✅ **Flexible argument handling** met multiple options
- ✅ **Custom configuration** file support

### Versie 1.0 (Vorige)
- Basic automated deployment
- Hardcoded configuration
- Limited validation
- No dry-run support