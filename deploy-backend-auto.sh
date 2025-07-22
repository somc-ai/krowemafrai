#!/bin/bash
# Automatische backend deployment voor LIVE gang naar Azure Container App
# Build, push en deploy backend-aiagents-gov container image naar Azure Container App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration - can be overridden by environment variables
ACR_NAME=${ACR_NAME:-"ca2a76f03945acr"}
RESOURCE_GROUP=${RESOURCE_GROUP:-"rg-info-2259"}
CONTAINER_APP=${CONTAINER_APP:-"backend-aiagents-gov"}
DOCKERFILE_PATH=${DOCKERFILE_PATH:-"src/backend/Dockerfile.azure"}
REGISTRY_SERVER="$ACR_NAME.azurecr.io"
IMAGE_TAG=${IMAGE_TAG:-"latest"}
IMAGE_NAME="$REGISTRY_SERVER/$CONTAINER_APP:$IMAGE_TAG"

log_info "🚀 Starting automatic backend deployment for LIVE environment"
log_info "Configuration:"
log_info "  - Container Registry: $REGISTRY_SERVER"
log_info "  - Resource Group: $RESOURCE_GROUP"
log_info "  - Container App: $CONTAINER_APP"
log_info "  - Image: $IMAGE_NAME"
log_info "  - Dockerfile: $DOCKERFILE_PATH"

# Pre-deployment checks
log_info "🔍 Running pre-deployment checks..."

# Check if required tools are available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed or not in PATH"
    exit 1
fi

# Check if Azure CLI is logged in
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_PATH" ]; then
    log_error "Dockerfile not found at $DOCKERFILE_PATH"
    exit 1
fi

# Check if backend source directory exists
if [ ! -d "src/backend" ]; then
    log_error "Backend source directory not found at src/backend"
    exit 1
fi

log_success "Pre-deployment checks passed"

# 1. Build Docker image
log_info "🔨 Building Docker image..."
if docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" src/backend; then
    log_success "Docker image built successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# 2. Login to Azure Container Registry
log_info "🔐 Logging in to Azure Container Registry..."
if az acr login --name "$ACR_NAME"; then
    log_success "Successfully logged in to ACR"
else
    log_error "Failed to login to Azure Container Registry"
    exit 1
fi

# 3. Push image to ACR
log_info "📤 Pushing image to ACR..."
if docker push "$IMAGE_NAME"; then
    log_success "Image pushed successfully to ACR"
else
    log_error "Failed to push image to ACR"
    exit 1
fi

# 4. Update Azure Container App with new image
log_info "🔄 Updating Azure Container App..."
if az containerapp update \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$IMAGE_NAME" \
    --output table; then
    log_success "Container App updated successfully"
else
    log_error "Failed to update Container App"
    exit 1
fi

# 5. Post-deployment verification
log_info "✅ Running post-deployment verification..."

# Get the app URL
APP_URL=$(az containerapp show \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.latestRevisionFqdn" \
    --output tsv 2>/dev/null)

if [ -n "$APP_URL" ]; then
    log_success "Container App is available at: https://$APP_URL"
    
    # Basic health check (optional - only if app responds quickly)
    log_info "🏥 Performing basic health check..."
    if curl -f -s --max-time 10 "https://$APP_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_warning "Health check failed or endpoint not available (this might be normal during startup)"
    fi
else
    log_warning "Could not retrieve app URL"
fi

# Display deployment summary
log_success "🎉 Deployment completed successfully!"
log_info "Deployment Summary:"
log_info "  - Image: $IMAGE_NAME"
log_info "  - Container App: $CONTAINER_APP"
log_info "  - Resource Group: $RESOURCE_GROUP"
if [ -n "$APP_URL" ]; then
    log_info "  - App URL: https://$APP_URL"
fi

log_info "💡 Tips:"
log_info "  - Monitor the deployment in Azure Portal"
log_info "  - Check logs with: az containerapp logs show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --follow"
log_info "  - Verify app status with: az containerapp show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP"
