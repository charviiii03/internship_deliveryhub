# test_integration_workflow.py
# Tests the complete application creation → auth → DB verification workflow.
#
# FIX Bug 4: was mocking "app_manager.send_application_credentials" which doesn't
# exist. The actual function is send_onboarding_email imported from notifications.

from unittest.mock import patch
from app_manager import app as app_manager_app


def test_complete_application_auth_workflow():

    client = app_manager_app.test_client()

    # FIX: patch the correct function name
    with patch("app_manager.send_onboarding_email") as mock_send_email:

        # 1. Create application
        create_response = client.post(
            "/admin/create-application",
            json={
                "application_name": "Integration Test App",
                "user_email": "test@example.com"
            }
        )

        assert create_response.status_code == 201

        create_data = create_response.get_json()

        assert create_data["status"] == "success"
        assert "application_id" in create_data
        assert "application_token" in create_data
        assert "expiry_date" in create_data

        application_id    = create_data["application_id"]
        application_token = create_data["application_token"]

        # 2. Verify notification was called once
        mock_send_email.assert_called_once()

        # 3. Authenticate application
        auth_response = client.post(
            "/validate-auth",
            json={
                "application_id":    application_id,
                "application_token": application_token
            }
        )

        assert auth_response.status_code == 200

        auth_data = auth_response.get_json()
        assert auth_data["status"]  == "valid"
        assert auth_data["message"] == "valid application"

        # 4. Verify application appears in database/API
        apps_response = client.get("/admin/applications")
        assert apps_response.status_code == 200

        apps_data = apps_response.get_json()
        application_ids = [app["application_id"] for app in apps_data["applications"]]
        assert application_id in application_ids

        # 5. Verify auth log was created
        logs_response = client.get("/admin/auth-logs")
        assert logs_response.status_code == 200

        logs_data = logs_response.get_json()
        assert any(
            log["application_id"] == application_id and log["status"] == "success"
            for log in logs_data["logs"]
        )
