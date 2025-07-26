# Production Configuration Fix Guide

Deze guide helpt bij het oplossen van alle configuratie problemen.

## 🔧 Stap 1: Backend URL Fix

Het probleem was dat de frontend niet de juiste backend URL gebruikte.

**Opgelost door:**
1. Fallback URL toegevoegd in `frontend_server.py`
2. Extra fallback in `App.tsx`
3. Robuuste error handling toegevoegd

## 🏗️ Stap 2: Backend Response Fix

De backend gaf een 404 error door Azure resource configuratie issues.

**Opgelost door:**
1. Updated `app_kernel.py` om proper agent responses te retourneren
2. Fallback response structuur die werkt met frontend
3. Error handling voor verschillende response formaten

## 🚀 Stap 3: Deployment Instructies

### Voor Azure Container Apps deployment:

```bash
# 1. Update frontend container
cd src/frontend
docker build -t krowemafrai-frontend .
docker tag krowemafrai-frontend your-registry.azurecr.io/krowemafrai-frontend:latest
docker push your-registry.azurecr.io/krowemafrai-frontend:latest

# 2. Update backend container  
cd ../backend
docker build -t krowemafrai-backend .
docker tag krowemafrai-backend your-registry.azurecr.io/krowemafrai-backend:latest
docker push your-registry.azurecr.io/krowemafrai-backend:latest

# 3. Update container apps
az containerapp update \
  --name frontend-aiagents-gov \
  --resource-group your-resource-group \
  --image your-registry.azurecr.io/krowemafrai-frontend:latest

az containerapp update \
  --name backend-aiagents-gov \
  --resource-group your-resource-group \
  --image your-registry.azurecr.io/krowemafrai-backend:latest
```

### Voor AZD deployment:

```bash
cd /workspaces/krowemafrai
azd env set BACKEND_API_URL "https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io"
azd up
```

## 🧪 Stap 4: Test de fixes

```bash
# Test backend directly
curl -X POST https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/api/input_task \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "description": "test scenario"}'

# Test frontend config
curl https://your-frontend-url/config

# Test agent tools
curl https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/api/agent-tools
```

## 📋 Checklist van fixes:

- ✅ Frontend URL configuration fixed
- ✅ Backend response format fixed
- ✅ Error handling improved
- ✅ Fallback mechanisms added
- ✅ Agent response structure corrected
- ⏳ Deployment needed (containers need to be rebuilt)

## 🔍 Troubleshooting

Als je nog steeds problemen hebt:

1. **Check logs**: Bekijk container logs in Azure Portal
2. **Check environment variables**: Verify BACKEND_API_URL is correct
3. **Check network**: Ensure containers can communicate
4. **Check Azure resources**: Verify Cosmos DB, OpenAI, etc. are configured

## 📞 Next Steps

1. Deploy de geüpdatete containers
2. Test de volledige flow
3. Monitor de logs voor eventuele issues
4. Setup proper Azure resource configuration (Cosmos DB, OpenAI)
