import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "online"

def test_start_session():
    """Test starting a new interview session"""
    response = client.post(
        "/api/session/start",
        json={
            "student_name": "Test Student",
            "project_title": "Test Project"
        }
    )
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert response.json()["status"] == "success"

def test_session_not_found():
    """Test getting a non-existent session"""
    response = client.get("/api/session/invalid_session_id")
    assert response.status_code == 404

def test_list_sessions():
    """Test listing all sessions"""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()
    assert "count" in response.json()

@pytest.mark.asyncio
async def test_ocr_service():
    """Test OCR service functionality"""
    from services.ocr_service import OCRService
    
    ocr = OCRService()
    # Test with a simple base64 encoded image (you'd need actual test data)
    # This is a placeholder test
    assert ocr is not None

@pytest.mark.asyncio
async def test_session_workflow():
    """Test complete session workflow"""
    # Start session
    response = client.post(
        "/api/session/start",
        json={"student_name": "Test", "project_title": "Test"}
    )
    session_id = response.json()["session_id"]
    
    # Get session
    response = client.get(f"/api/session/{session_id}")
    assert response.status_code == 200
    
    # Delete session
    response = client.delete(f"/api/session/{session_id}")
    assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
