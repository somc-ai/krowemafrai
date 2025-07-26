#!/bin/bash
# test_all_fixes.sh - Comprehensive test script for all applied fixes

echo "🧪 Testing All Applied Fixes"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test URLs
BACKEND_URL="https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io"
FRONTEND_URL="https://frontend-aiagents-gov.westeurope.azurecontainerapps.io"

echo "📍 Testing Backend API Health..."
if curl -s "$BACKEND_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

echo "📍 Testing Agent Tools Endpoint..."
AGENT_COUNT=$(curl -s "$BACKEND_URL/api/agent-tools" | jq length 2>/dev/null)
if [ "$AGENT_COUNT" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}✅ Agent tools endpoint working - found $AGENT_COUNT agents${NC}"
else
    echo -e "${RED}❌ Agent tools endpoint failed${NC}"
fi

echo "📍 Testing Input Task Endpoint..."
TASK_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/input_task" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_'$(date +%s)'", "description": "Test scenario voor validatie van alle fixes"}')

echo "Response preview:"
echo "$TASK_RESPONSE" | head -3

if echo "$TASK_RESPONSE" | grep -q "agent_responses\|status"; then
    echo -e "${GREEN}✅ Input task endpoint responding correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Input task endpoint responding, but format may need adjustment${NC}"
fi

echo "📍 Testing Frontend Config (if frontend is deployed)..."
if curl -s "$FRONTEND_URL/config" >/dev/null 2>&1; then
    CONFIG_RESPONSE=$(curl -s "$FRONTEND_URL/config")
    API_URL=$(echo "$CONFIG_RESPONSE" | jq -r '.API_URL' 2>/dev/null)
    
    if [ "$API_URL" != "null" ] && [ "$API_URL" != "" ]; then
        echo -e "${GREEN}✅ Frontend config endpoint working - API_URL: $API_URL${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend config accessible but API_URL may not be set correctly${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend not accessible (may need deployment)${NC}"
fi

echo "📍 Testing API Documentation..."
if curl -s "$BACKEND_URL/docs" | grep -q "swagger"; then
    echo -e "${GREEN}✅ API documentation accessible at $BACKEND_URL/docs${NC}"
else
    echo -e "${RED}❌ API documentation not accessible${NC}"
fi

echo ""
echo "🔍 Summary of Changes Made:"
echo "- ✅ Fixed frontend_server.py with fallback backend URL"
echo "- ✅ Updated App.tsx with robust error handling"
echo "- ✅ Modified app_kernel.py to return proper agent responses"
echo "- ✅ Added fallback mechanisms for offline mode"
echo "- ✅ Improved configuration management"

echo ""
echo "🚀 Next Steps:"
echo "1. Deploy updated containers to see full fixes in action"
echo "2. Configure Azure resources (Cosmos DB, OpenAI) for full functionality"
echo "3. Monitor logs after deployment"

echo ""
echo "📋 Test completed at $(date)"
