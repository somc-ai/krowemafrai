#!/bin/bash
# 🚀 Automated Backend Deployment to Azure Container App
# Build, push en deploy backend-aiagents-gov container image naar Azure Container App
# Voorkomt handmatige fouten en zorgt voor snelle, betrouwbare productie-deployment

set -e

# 🎯 Azure Configuration
ACR_NAME="ca2a76f03945acr"
REGISTRY_SERVER="ca2a76f03945acr.azurecr.io"
RESOURCE_GROUP="rg-info-2259"
CONTAINER_APP="backend-aiagents-gov"
ENVIRONMENT_NAME="managedEnvironment-rginfo2259-8048"
BACKEND_DIR="src/backend"
DOCKERFILE="$BACKEND_DIR/Dockerfile.azure"

# 🏷️ Image configuration
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${TIMESTAMP}-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
IMAGE_NAME="$REGISTRY_SERVER/$CONTAINER_APP:$IMAGE_TAG"
LATEST_IMAGE="$REGISTRY_SERVER/$CONTAINER_APP:latest"

# 🎨 Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 📋 Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Dockerfile exists
    if [[ ! -f "$DOCKERFILE" ]]; then
        log_error "Dockerfile not found at $DOCKERFILE"
        exit 1
    fi
    
    # Check if backend directory exists
    if [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "Backend directory not found at $BACKEND_DIR"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

verify_azure_login() {
    log_info "Verifying Azure login..."
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first"
        exit 1
    fi
    
    local subscription=$(az account show --query "name" -o tsv)
    log_success "Logged in to Azure subscription: $subscription"
}

show_deployment_info() {
    echo "=================================================================="
    echo "🚀 AZURE CONTAINER APP DEPLOYMENT"
    echo "=================================================================="
    echo "📦 Container App: $CONTAINER_APP"
    echo "🏷️  Resource Group: $RESOURCE_GROUP"
    echo "🐳 Image: $IMAGE_NAME"
    echo "📂 Backend Directory: $BACKEND_DIR"
    echo "🐋 Dockerfile: $DOCKERFILE"
    echo "⏰ Timestamp: $TIMESTAMP"
    echo "=================================================================="
}

confirm_deployment() {
    log_warning "This will deploy to PRODUCTION environment!"
    log_warning "Container App: $CONTAINER_APP in Resource Group: $RESOURCE_GROUP"
    
    read -p "🤔 Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Deployment cancelled by user"
        exit 0
    fi
}

build_docker_image() {
    log_info "Building Docker image..."
    log_info "Building from: $DOCKERFILE"
    log_info "Image tag: $IMAGE_NAME"
    
    # Build with current directory as context, specify dockerfile
    if docker build -t "$IMAGE_NAME" -t "$LATEST_IMAGE" -f "$DOCKERFILE" .; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

login_to_acr() {
    log_info "Logging in to Azure Container Registry..."
    if az acr login --name "$ACR_NAME"; then
        log_success "Successfully logged in to ACR: $ACR_NAME"
    else
        log_error "Failed to login to Azure Container Registry"
        exit 1
    fi
}

push_image_to_acr() {
    log_info "Pushing image to Azure Container Registry..."
    log_info "Pushing: $IMAGE_NAME"
    
    if docker push "$IMAGE_NAME" && docker push "$LATEST_IMAGE"; then
        log_success "Image pushed successfully to ACR"
    else
        log_error "Failed to push image to ACR"
        exit 1
    fi
}

get_current_image() {
    local current_image=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.template.containers[0].image" \
        -o tsv 2>/dev/null || echo "none")
    echo "$current_image"
}

deploy_to_container_app() {
    log_info "Deploying to Azure Container App..."
    
    # Get current image for rollback purposes
    local current_image=$(get_current_image)
    log_info "Current image: $current_image"
    
    # Check if Container App exists
    if az containerapp show --name "$CONTAINER_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_info "Container App exists, updating..."
        
        # Update existing Container App
        if az containerapp update \
            --name "$CONTAINER_APP" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$IMAGE_NAME" \
            --set-env-vars \
                PORT=8000 \
                AZURE_OPENAI_ENDPOINT="https://somc-ai-gov-openai.openai.azure.com/" \
                AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
                AZURE_OPENAI_API_VERSION="2024-10-21" \
                AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002" \
                AZURE_AI_SUBSCRIPTION_ID="05cc117e-29ea-49f3-9428-c5d042340a91" \
                AZURE_AI_RESOURCE_GROUP="rg-info-2259" \
                AZURE_AI_PROJECT_NAME="ai-project-default" \
                AZURE_AI_AGENT_ENDPOINT="https://somc-ai-gov-openai.openai.azure.com/" \
                OTEL_PYTHON_LOG_CORRELATION="true" \
                OTEL_PYTHON_LOG_LEVEL="info" \
                PYTHON_ENV="production"; then
            log_success "Container App updated successfully"
        else
            log_error "Failed to update Container App"
            if [[ "$current_image" != "none" ]]; then
                log_warning "Attempting rollback to previous image: $current_image"
                rollback_deployment "$current_image"
            fi
            exit 1
        fi
    else
        log_info "Container App does not exist, creating..."
        
        # Create new Container App
        if az containerapp create \
            --name "$CONTAINER_APP" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ENVIRONMENT_NAME" \
            --image "$IMAGE_NAME" \
            --registry-server "$REGISTRY_SERVER" \
            --cpu 1.0 \
            --memory 2.0Gi \
            --min-replicas 1 \
            --max-replicas 3 \
            --target-port 8000 \
            --ingress external \
            --env-vars \
                PORT=8000 \
                AZURE_OPENAI_ENDPOINT="https://somc-ai-gov-openai.openai.azure.com/" \
                AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
                AZURE_OPENAI_API_VERSION="2024-10-21" \
                AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002" \
                AZURE_AI_SUBSCRIPTION_ID="05cc117e-29ea-49f3-9428-c5d042340a91" \
                AZURE_AI_RESOURCE_GROUP="rg-info-2259" \
                AZURE_AI_PROJECT_NAME="ai-project-default" \
                AZURE_AI_AGENT_ENDPOINT="https://somc-ai-gov-openai.openai.azure.com/" \
                OTEL_PYTHON_LOG_CORRELATION="true" \
                OTEL_PYTHON_LOG_LEVEL="info" \
                PYTHON_ENV="production"; then
            log_success "Container App created successfully"
        else
            log_error "Failed to create Container App"
            exit 1
        fi
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait a moment for deployment to settle
    sleep 10
    
    # Get Container App URL
    local app_url=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$app_url" ]]; then
        log_success "Container App is available at: https://$app_url"
        
        # Test health endpoint if available
        log_info "Testing health endpoint..."
        if curl -f -s "https://$app_url/health" > /dev/null 2>&1; then
            log_success "Health check passed"
        else
            log_warning "Health check failed or endpoint not available"
            log_info "This might be normal if the app is still starting up"
        fi
    else
        log_error "Could not retrieve Container App URL"
        exit 1
    fi
    
    # Show deployment status
    local status=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.runningStatus" \
        -o tsv 2>/dev/null || echo "unknown")
    
    log_info "Container App status: $status"
}

rollback_deployment() {
    local previous_image="$1"
    log_warning "Rolling back to previous image: $previous_image"
    
    if az containerapp update \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$previous_image"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed! Manual intervention required"
    fi
}

show_summary() {
    echo "=================================================================="
    echo "🎉 DEPLOYMENT SUMMARY"
    echo "=================================================================="
    echo "✅ Container App: $CONTAINER_APP"
    echo "✅ Resource Group: $RESOURCE_GROUP"
    echo "✅ Image: $IMAGE_NAME"
    echo "✅ Timestamp: $TIMESTAMP"
    
    local app_url=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv 2>/dev/null || echo "unknown")
    
    if [[ "$app_url" != "unknown" ]]; then
        echo "🔗 URL: https://$app_url"
    fi
    
    echo "=================================================================="
    log_success "Backend deployment completed successfully!"
}

# 🚀 Main execution
main() {
    echo "🚀 Starting automated backend deployment..."
    
    show_deployment_info
    check_prerequisites
    verify_azure_login
    confirm_deployment
    
    log_info "Starting deployment process..."
    build_docker_image
    login_to_acr
    push_image_to_acr
    deploy_to_container_app
    verify_deployment
    show_summary
    
    log_success "🎉 Deployment process completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "🚀 Automated Backend Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --skip-confirm Skip deployment confirmation (use with caution!)"
        echo ""
        echo "This script automates the build, push, and deployment of the backend"
        echo "container to Azure Container App, preventing manual errors and enabling"
        echo "quick, reliable production deployment with user confirmation."
        echo ""
        echo "Prerequisites:"
        echo "  - Azure CLI installed and logged in (az login)"
        echo "  - Docker installed and running"
        echo "  - Access to Azure Container Registry: $ACR_NAME"
        echo "  - Access to Resource Group: $RESOURCE_GROUP"
        exit 0
        ;;
    --skip-confirm)
        SKIP_CONFIRM=true
        ;;
    "")
        # No arguments, continue with normal execution
        ;;
    *)
        log_error "Unknown argument: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

# Override confirm_deployment if skip-confirm is set
if [[ "${SKIP_CONFIRM:-false}" == "true" ]]; then
    confirm_deployment() {
        log_warning "Skipping confirmation (--skip-confirm flag used)"
    }
fi

# Execute main function
main
