"""
Test Smart Router Application Name Resolution

This module tests the smart router's ability to automatically resolve
application names to application IDs for alert config operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.smart_router_tool import SmartRouterMCPTool


@pytest.fixture
def smart_router():
    """Create a SmartRouterMCPTool instance for testing."""
    return SmartRouterMCPTool(read_token="test_token", base_url="https://test.instana.io")


@pytest.mark.asyncio
async def test_resolve_application_name_to_id(smart_router):
    """Test that application name is resolved to ID automatically."""

    # Mock the application resources API response
    mock_app_result = MagicMock()
    mock_app_result.to_dict.return_value = {
        "items": [
            {"id": "app-123-456", "label": "All Services"},
            {"id": "app-789-012", "label": "Other App"}
        ]
    }

    # Mock the alert config response
    mock_alert_result = {"configs": []}

    with patch.object(smart_router.app_alert_config_client, 'execute_alert_config_operation',
                     new_callable=AsyncMock) as mock_alert_op:
        with patch('instana_client.api.application_resources_api.ApplicationResourcesApi') as mock_api_class:
            mock_api_instance = MagicMock()
            mock_api_instance.get_applications.return_value = mock_app_result
            mock_api_class.return_value = mock_api_instance

            mock_alert_op.return_value = mock_alert_result

            # Call the smart router with application_name
            result = await smart_router.manage_instana_resources(
                resource_type="alert_config",
                operation="find_active",
                params={"application_name": "All Services"}
            )

            # Verify the application name was resolved
            assert "error" not in result
            assert result["application_name"] == "All Services"
            assert result["application_id"] == "app-123-456"

            # Verify the alert config operation was called with the resolved ID
            mock_alert_op.assert_called_once()
            call_kwargs = mock_alert_op.call_args[1]
            assert call_kwargs["application_id"] == "app-123-456"


@pytest.mark.asyncio
async def test_application_id_takes_precedence(smart_router):
    """Test that application_id is used directly if provided."""

    mock_alert_result = {"configs": []}

    with patch.object(smart_router.app_alert_config_client, 'execute_alert_config_operation',
                     new_callable=AsyncMock) as mock_alert_op:
        mock_alert_op.return_value = mock_alert_result

        # Call with both application_id and application_name
        result = await smart_router.manage_instana_resources(
            resource_type="alert_config",
            operation="find_active",
            params={
                "application_id": "direct-app-id",
                "application_name": "All Services"
            }
        )

        # Verify application_id was used directly (no resolution)
        assert "error" not in result
        assert result["application_id"] == "direct-app-id"

        # Verify the alert config operation was called with the direct ID
        mock_alert_op.assert_called_once()
        call_kwargs = mock_alert_op.call_args[1]
        assert call_kwargs["application_id"] == "direct-app-id"


@pytest.mark.asyncio
async def test_application_name_not_found(smart_router):
    """Test error handling when application name is not found."""

    # Mock empty application results
    mock_app_result = MagicMock()
    mock_app_result.to_dict.return_value = {"items": []}

    with patch('instana_client.api.application_resources_api.ApplicationResourcesApi') as mock_api_class:
        mock_api_instance = MagicMock()
        mock_api_instance.get_applications.return_value = mock_app_result
        mock_api_class.return_value = mock_api_instance

        # Call with non-existent application name
        result = await smart_router.manage_instana_resources(
            resource_type="alert_config",
            operation="find_active",
            params={"application_name": "NonExistent App"}
        )

        # Verify error is returned
        assert "error" in result
        assert "NonExistent App" in result["error"]


@pytest.mark.asyncio
async def test_case_insensitive_matching(smart_router):
    """Test that application name matching is case-insensitive."""

    # Mock the application resources API response
    mock_app_result = MagicMock()
    mock_app_result.to_dict.return_value = {
        "items": [
            {"id": "app-123-456", "label": "All Services"}
        ]
    }

    mock_alert_result = {"configs": []}

    with patch.object(smart_router.app_alert_config_client, 'execute_alert_config_operation',
                     new_callable=AsyncMock) as mock_alert_op:
        with patch('instana_client.api.application_resources_api.ApplicationResourcesApi') as mock_api_class:
            mock_api_instance = MagicMock()
            mock_api_instance.get_applications.return_value = mock_app_result
            mock_api_class.return_value = mock_api_instance

            mock_alert_op.return_value = mock_alert_result

            # Call with different case
            result = await smart_router.manage_instana_resources(
                resource_type="alert_config",
                operation="find_active",
                params={"application_name": "all services"}  # lowercase
            )

            # Verify the application was found despite case difference
            assert "error" not in result
            assert result["application_id"] == "app-123-456"
