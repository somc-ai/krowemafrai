# 🚀 Backend Deployment - Quick Start

Dit is de **snelste manier** om je backend automatisch te deployen naar Azure Container Apps.

## ⚡ One-Click Deployment

### Optie 1: Super Eenvoudig (Aanbevolen)
```bash
./quick-deploy-backend.sh
```
- 🎯 **Alles-in-één** script met begeleiding
- ✅ Automatische environment checks
- 🧪 Optie voor dry-run test eerst
- 🚀 Direct naar productie met één bevestiging

### Optie 2: Direct Script
```bash
./deploy-backend-auto.sh
```
- 🔧 **Volledige controle** over deployment
- 🧪 Test eerst: `./deploy-backend-auto.sh --dry-run`
- 🚀 Live deployment met bevestiging

## 📋 Wat Heb Je Nodig?

### Eenmalige Setup (5 minuten)
1. **Azure CLI** → [Download hier](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Docker** → [Download hier](https://docs.docker.com/get-docker/)
3. **Login bij Azure**: `az login`

### Klaar!
Je bent nu klaar om met **één bevestiging live te gaan**! 🎉

## 🎯 Voorbeelden

### Eerste Keer? Test Eerst!
```bash
# Veilig testen zonder echte deployment
./deploy-backend-auto.sh --dry-run

# Als test goed gaat, echte deployment
./deploy-backend-auto.sh
```

### Voor CI/CD
```bash
# Zonder handmatige bevestiging
./deploy-backend-auto.sh --skip-confirm
```

### Custom Configuratie
```bash
# Gebruik andere configuratie file
./deploy-backend-auto.sh --config staging-config.env
```

## 🆘 Problemen?

### Snel Oplossen
1. **Docker niet draaiend?** → Start Docker Desktop
2. **Azure login vergeten?** → Run `az login`
3. **Permissions issue?** → Check je Azure toegang

### Uitgebreide Hulp
📖 **Volledige documentatie**: [DEPLOYMENT_AUTOMATION.md](DEPLOYMENT_AUTOMATION.md)

## ✨ Wat Doet Het Script?

1. ✅ **Valideert** je environment (Azure, Docker, files)
2. 🐳 **Bouwt** Docker image met timestamp tag
3. 📤 **Pusht** naar Azure Container Registry
4. 🚀 **Deployed** naar Azure Container App
5. ✅ **Verifieert** dat alles werkt
6. 📊 **Toont** je live URL

**Alles geautomatiseerd, één bevestiging, en je bent live!** 🎉

---
*Voor ontwikkelaars: Dit script zorgt voor consistente deployment met automatische rollback, health checks, en proper tagging. Zie DEPLOYMENT_AUTOMATION.md voor technische details.*