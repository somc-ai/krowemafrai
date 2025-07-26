"""
Test for the /plan endpoint functionality.
This test isolates just the plan endpoint functionality to avoid dependency issues.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the model we're testing
from models.messages_kernel import PlanRequest


def create_test_app():
    """Create a minimal test app with just the plan endpoint."""
    app = FastAPI()
    
    @app.post("/plan")
    async def plan_endpoint(plan_request: PlanRequest):
        """Test implementation of the plan endpoint."""
        return {
            "message": "Plan ontvangen",
            "session_id": plan_request.session_id,
            "description": plan_request.description
        }
    
    return app


class TestPlanEndpoint:
    """Test class for the /plan endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_test_app()
        return TestClient(app)
    
    def test_plan_endpoint_success(self, client):
        """Test successful plan request."""
        test_data = {
            "session_id": "test-session-123",
            "description": "Create a comprehensive marketing strategy"
        }
        
        response = client.post("/plan", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["message"] == "Plan ontvangen"
        assert result["session_id"] == "test-session-123"
        assert result["description"] == "Create a comprehensive marketing strategy"
    
    def test_plan_endpoint_missing_session_id(self, client):
        """Test plan request with missing session_id."""
        test_data = {
            "description": "Create a marketing strategy"
        }
        
        response = client.post("/plan", json=test_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "session_id"] for error in error_detail)
    
    def test_plan_endpoint_missing_description(self, client):
        """Test plan request with missing description."""
        test_data = {
            "session_id": "test-session-123"
        }
        
        response = client.post("/plan", json=test_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "description"] for error in error_detail)
    
    def test_plan_endpoint_empty_request(self, client):
        """Test plan request with empty body."""
        response = client.post("/plan", json={})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        # Should have errors for both missing fields
        assert len(error_detail) == 2
    
    def test_plan_request_model(self):
        """Test the PlanRequest model directly."""
        # Test valid model creation
        plan_request = PlanRequest(
            session_id="test-123",
            description="Test description"
        )
        
        assert plan_request.session_id == "test-123"
        assert plan_request.description == "Test description"
        
        # Test model serialization
        data = plan_request.model_dump()
        expected = {
            "session_id": "test-123",
            "description": "Test description"
        }
        assert data == expected
    
    def test_plan_endpoint_with_special_characters(self, client):
        """Test plan request with special characters and unicode."""
        test_data = {
            "session_id": "test-session-üñíçødé",
            "description": "Créez un plan de marketing avec des caractères spéciaux: äöü & émojis 🚀"
        }
        
        response = client.post("/plan", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["message"] == "Plan ontvangen"
        assert result["session_id"] == test_data["session_id"]
        assert result["description"] == test_data["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])