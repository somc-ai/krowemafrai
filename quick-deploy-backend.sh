#!/bin/bash
# 🚀 Quick Deploy Backend - One-Click Production Deployment
# Deze script zorgt voor de snelste weg naar een live backend deployment
# Automatische checks, een bevestiging, en je backend is live!

set -e

# 🎨 Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================================="
echo "🚀 QUICK DEPLOY BACKEND - ONE CLICK TO LIVE!"
echo "=================================================================="
echo -e "${NC}"

echo "This script will:"
echo "✅ Validate your environment"
echo "✅ Build and push your backend to Azure"
echo "✅ Deploy to production with ONE confirmation"
echo "✅ Verify your deployment is working"
echo ""

# Check if main deployment script exists
if [[ ! -f "deploy-backend-auto.sh" ]]; then
    echo "❌ deploy-backend-auto.sh not found!"
    echo "Please run this script from the repository root directory."
    exit 1
fi

echo -e "${YELLOW}🔍 Quick Environment Check...${NC}"

# Quick checks
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI first."
    echo "   Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   Install: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker."
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure."
    echo "Please run: az login"
    exit 1
fi

SUBSCRIPTION=$(az account show --query "name" -o tsv)
echo -e "${GREEN}✅ Azure CLI ready (Subscription: $SUBSCRIPTION)${NC}"
echo -e "${GREEN}✅ Docker ready${NC}"

echo ""
echo -e "${YELLOW}🎯 Ready for deployment!${NC}"
echo ""
echo "Would you like to:"
echo "1) 🧪 Test deployment (dry-run) - Recommended first time"
echo "2) 🚀 Deploy to PRODUCTION immediately"
echo "3) ❌ Cancel"
echo ""

read -p "Enter your choice (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🧪 Running dry-run test...${NC}"
        ./deploy-backend-auto.sh --dry-run
        echo ""
        echo -e "${GREEN}✅ Dry-run completed! Your setup looks good.${NC}"
        echo ""
        read -p "🚀 Would you like to deploy to production now? (yes/no): " deploy_now
        if [[ $deploy_now =~ ^[Yy][Ee][Ss]$ ]]; then
            echo ""
            echo -e "${BLUE}🚀 Deploying to production...${NC}"
            ./deploy-backend-auto.sh
        else
            echo "👍 No problem! Run this script again when you're ready to deploy."
        fi
        ;;
    2)
        echo ""
        echo -e "${BLUE}🚀 Deploying directly to production...${NC}"
        ./deploy-backend-auto.sh
        ;;
    3)
        echo "👋 Deployment cancelled. Run this script again when you're ready!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}"
echo "=================================================================="
echo "🎉 QUICK DEPLOY COMPLETED!"
echo "=================================================================="
echo -e "${NC}"
echo "Your backend should now be live and running!"
echo ""
echo "Next steps:"
echo "📱 Test your API endpoints"
echo "📊 Monitor in Azure Portal"
echo "🔍 Check logs if needed"
echo ""
echo "Need help? Check: DEPLOYMENT_AUTOMATION.md"