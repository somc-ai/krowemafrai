#!/bin/bash
# Azure Web App startup script for SoMC AI - Zeeland Multi-Agent Team

echo "🚀 Starting SoMC AI - Zeeland Multi-Agent Team"
echo "📂 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 Installing dependencies..."

# Set environment variables
export PORT=${PORT:-8000}
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONUNBUFFERED=1

# Function to install dependencies with error handling
install_dependencies() {
    echo "📦 Attempting to install dependencies..."
    
    # Try to install minimal requirements first
    if [ -f "requirements-minimal.txt" ]; then
        echo "📦 Installing minimal requirements..."
        pip install -r requirements-minimal.txt --timeout=30 || echo "⚠️  Minimal requirements failed, continuing..."
    fi
    
    # Try to install full requirements
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing full requirements..."
        pip install -r requirements.txt --timeout=60 || echo "⚠️  Full requirements failed, continuing with minimal setup..."
    fi
    
    echo "📦 Dependencies installation completed (with possible fallbacks)"
}

# Install dependencies with timeout
timeout 300 install_dependencies || echo "⚠️  Dependency installation timed out, continuing with available packages..."

echo "🔧 Environment setup complete"
echo "🏃‍♂️ Starting application..."

# Start the application with error handling
python main.py || {
    echo "❌ Main application failed, trying fallback..."
    python app.py || {
        echo "❌ App fallback failed, starting basic server..."
        python -m http.server ${PORT} || {
            echo "❌ All startup methods failed!"
            exit 1
        }
    }
}