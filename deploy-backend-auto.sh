#!/bin/bash
# 🚀 Automated Backend Deployment to Azure Container App
# Build, push en deploy backend-aiagents-gov container image naar Azure Container App
# Voorkomt handmatige fouten en zorgt voor snelle, betrouwbare productie-deployment

set -e

# 📋 Load configuration from external file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/deployment-config.env"

if [[ -f "$CONFIG_FILE" ]]; then
    # Source configuration file
    source "$CONFIG_FILE"
    echo "✅ Configuration loaded from: $CONFIG_FILE"
else
    echo "❌ Configuration file not found: $CONFIG_FILE"
    echo "🔧 Creating default configuration file..."
    exit 1
fi

# 🎯 Validate required configuration
DOCKERFILE="$BACKEND_DIR/Dockerfile.azure"

# 🏷️ Image configuration
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${TIMESTAMP}-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
IMAGE_NAME="$REGISTRY_SERVER/$IMAGE_REPOSITORY:$IMAGE_TAG"
LATEST_IMAGE="$REGISTRY_SERVER/$IMAGE_REPOSITORY:latest"

# 🎨 Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 🔧 Global flags
DRY_RUN=false
SKIP_CONFIRM=false

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
    
    # Check if configuration file was loaded
    if [[ -z "$ACR_NAME" || -z "$REGISTRY_SERVER" || -z "$RESOURCE_GROUP" ]]; then
        log_error "Configuration not properly loaded. Required variables missing."
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
    
    # Check Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

verify_azure_login() {
    log_info "Verifying Azure login..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Skipping Azure login verification"
        return 0
    fi
    
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
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No actual deployment will be performed"
        return 0
    fi
    
    if [[ "$SKIP_CONFIRM" == "true" ]]; then
        log_warning "Skipping confirmation (--skip-confirm flag used)"
        return 0
    fi
    
    log_warning "This will deploy to PRODUCTION environment!"
    log_warning "Container App: $CONTAINER_APP in Resource Group: $RESOURCE_GROUP"
    log_warning "Image: $IMAGE_NAME"
    
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
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would build Docker image: $IMAGE_NAME"
        return 0
    fi
    
    # Build with current directory as context, specify dockerfile
    if docker build -t "$IMAGE_NAME" -t "$LATEST_IMAGE" -f "$DOCKERFILE" .; then
        log_success "Docker image built successfully"
        
        # Show image size
        local image_size=$(docker images "$IMAGE_NAME" --format "{{.Size}}" | head -1)
        log_info "Image size: $image_size"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

login_to_acr() {
    log_info "Logging in to Azure Container Registry..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would login to ACR: $ACR_NAME"
        return 0
    fi
    
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
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would push images: $IMAGE_NAME and $LATEST_IMAGE"
        return 0
    fi
    
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
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would deploy to Container App: $CONTAINER_APP"
        log_info "DRY RUN: Would use image: $IMAGE_NAME"
        return 0
    fi
    
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
                PORT="$APP_PORT" \
                AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
                AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
                AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
                AZURE_OPENAI_EMBEDDING_MODEL="$AZURE_OPENAI_EMBEDDING_MODEL" \
                AZURE_AI_SUBSCRIPTION_ID="$AZURE_AI_SUBSCRIPTION_ID" \
                AZURE_AI_RESOURCE_GROUP="$AZURE_AI_RESOURCE_GROUP" \
                AZURE_AI_PROJECT_NAME="$AZURE_AI_PROJECT_NAME" \
                AZURE_AI_AGENT_ENDPOINT="$AZURE_AI_AGENT_ENDPOINT" \
                BACKEND_API_URL="$BACKEND_API_URL" \
                FRONTEND_SITE_NAME="$FRONTEND_SITE_NAME" \
                OTEL_PYTHON_LOG_CORRELATION="$OTEL_PYTHON_LOG_CORRELATION" \
                OTEL_PYTHON_LOG_LEVEL="$OTEL_PYTHON_LOG_LEVEL" \
                PYTHON_ENV="$PYTHON_ENV"; then
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
            --cpu "$CONTAINER_CPU" \
            --memory "$CONTAINER_MEMORY" \
            --min-replicas "$MIN_REPLICAS" \
            --max-replicas "$MAX_REPLICAS" \
            --target-port "$TARGET_PORT" \
            --ingress "$INGRESS_TYPE" \
            --env-vars \
                PORT="$APP_PORT" \
                AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
                AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
                AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
                AZURE_OPENAI_EMBEDDING_MODEL="$AZURE_OPENAI_EMBEDDING_MODEL" \
                AZURE_AI_SUBSCRIPTION_ID="$AZURE_AI_SUBSCRIPTION_ID" \
                AZURE_AI_RESOURCE_GROUP="$AZURE_AI_RESOURCE_GROUP" \
                AZURE_AI_PROJECT_NAME="$AZURE_AI_PROJECT_NAME" \
                AZURE_AI_AGENT_ENDPOINT="$AZURE_AI_AGENT_ENDPOINT" \
                BACKEND_API_URL="$BACKEND_API_URL" \
                FRONTEND_SITE_NAME="$FRONTEND_SITE_NAME" \
                OTEL_PYTHON_LOG_CORRELATION="$OTEL_PYTHON_LOG_CORRELATION" \
                OTEL_PYTHON_LOG_LEVEL="$OTEL_PYTHON_LOG_LEVEL" \
                PYTHON_ENV="$PYTHON_ENV"; then
            log_success "Container App created successfully"
        else
            log_error "Failed to create Container App"
            exit 1
        fi
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would verify deployment status"
        log_success "DRY RUN: Container App would be available at: https://${CONTAINER_APP}.${AZURE_LOCATION}-01.azurecontainerapps.io"
        return 0
    fi
    
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
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🧪 DRY RUN SUMMARY"
    else
        echo "🎉 DEPLOYMENT SUMMARY"
    fi
    echo "=================================================================="
    echo "✅ Container App: $CONTAINER_APP"
    echo "✅ Resource Group: $RESOURCE_GROUP"
    echo "✅ Image: $IMAGE_NAME"
    echo "✅ Timestamp: $TIMESTAMP"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🔗 Expected URL: https://${CONTAINER_APP}.${AZURE_LOCATION}-01.azurecontainerapps.io"
    else
        local app_url=$(az containerapp show \
            --name "$CONTAINER_APP" \
            --resource-group "$RESOURCE_GROUP" \
            --query "properties.configuration.ingress.fqdn" \
            -o tsv 2>/dev/null || echo "unknown")
        
        if [[ "$app_url" != "unknown" ]]; then
            echo "🔗 URL: https://$app_url"
        fi
    fi
    
    echo "=================================================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        log_success "Dry run completed successfully! No actual deployment was performed."
    else
        log_success "Backend deployment completed successfully!"
    fi
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

# Process arguments first
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "🚀 Automated Backend Deployment Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --help, -h        Show this help message"
            echo "  --skip-confirm    Skip deployment confirmation (use with caution!)"
            echo "  --dry-run         Validate and show what would be deployed without actual deployment"
            echo "  --config FILE     Use custom configuration file (default: deployment-config.env)"
            echo ""
            echo "This script automates the build, push, and deployment of the backend"
            echo "container to Azure Container App, preventing manual errors and enabling"
            echo "quick, reliable production deployment with user confirmation."
            echo ""
            echo "Prerequisites:"
            echo "  - Azure CLI installed and logged in (az login)"
            echo "  - Docker installed and running"
            echo "  - Configuration file with Azure settings"
            echo ""
            echo "Examples:"
            echo "  $0                    # Standard deployment with confirmation"
            echo "  $0 --dry-run          # Test deployment without actual changes"
            echo "  $0 --skip-confirm     # Deploy without confirmation (CI/CD)"
            exit 0
            ;;
        --skip-confirm)
            SKIP_CONFIRM=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --config)
            if [[ -n "$2" ]]; then
                CONFIG_FILE="$2"
                shift 2
            else
                echo "❌ --config requires a file path argument"
                exit 1
            fi
            ;;
        *)
            echo "❌ Unknown argument: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Execute main function
main
