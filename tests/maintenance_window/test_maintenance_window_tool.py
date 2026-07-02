"""
Tests for Maintenance Window MCP Tools

This module contains comprehensive unit tests for the maintenance window tool,
covering all operations including create, modify, close, list, and validation.
"""

import asyncio
import json
import logging
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Suppress logs during tests
logging.basicConfig(level=logging.ERROR)
tool_logger = logging.getLogger('src.maintenance_window.maintenance_window_tool')
tool_logger.handlers = []
tool_logger.propagate = False

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock instana_client before any src imports
sys.modules['instana_client'] = MagicMock()
sys.modules['instana_client.api'] = MagicMock()
sys.modules['instana_client.api.maintenance_configuration_api'] = MagicMock()
sys.modules['instana_client.models'] = MagicMock()
sys.modules['instana_client.models.maintenance_config_v2'] = MagicMock()

from src.maintenance_window.maintenance_window_tool import MaintenanceWindowMCPTools


class TestMaintenanceWindowMCPTools(unittest.TestCase):
    """Tests for MaintenanceWindowMCPTools"""

    def setUp(self):
        """Set up test fixtures"""
        self.tool = MaintenanceWindowMCPTools(
            read_token="test_token",
            base_url="https://test.instana.com"
        )
        self.ctx = MagicMock()

    # -------------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------------

    def test_init(self):
        """Tool is initialized with correct credentials"""
        self.assertEqual(self.tool.read_token, "test_token")
        self.assertEqual(self.tool.base_url, "https://test.instana.com")

    # -------------------------------------------------------------------------
    # _check_response_status Tests
    # -------------------------------------------------------------------------

    def test_check_response_status_success_200(self):
        """Status 200 returns None (success)"""
        response = MagicMock()
        response.status = 200
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNone(result)

    def test_check_response_status_success_201(self):
        """Status 201 returns None (success)"""
        response = MagicMock()
        response.status = 201
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNone(result)

    def test_check_response_status_success_204(self):
        """Status 204 returns None (success)"""
        response = MagicMock()
        response.status = 204
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNone(result)

    def test_check_response_status_error_404(self):
        """Status 404 returns error dict"""
        response = MagicMock()
        response.status = 404
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNotNone(result)
        self.assertIn("error", result)
        self.assertEqual(result["status_code"], 404)
        self.assertEqual(result["operation"], "test operation")

    def test_check_response_status_error_500(self):
        """Status 500 returns error dict"""
        response = MagicMock()
        response.status = 500
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNotNone(result)
        self.assertIn("error", result)
        self.assertEqual(result["status_code"], 500)

    def test_check_response_status_no_status_attribute(self):
        """Response without status attribute returns None"""
        response = MagicMock(spec=[])
        result = self.tool._check_response_status(response, "test operation")
        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # _get_templates Tests
    # -------------------------------------------------------------------------

    def test_get_templates_returns_all_templates(self):
        """_get_templates returns all predefined templates"""
        result = self.tool._get_templates()
        self.assertEqual(result["status"], "success")
        self.assertIn("templates", result)
        self.assertIn("deployment", result["templates"])
        self.assertIn("database_migration", result["templates"])
        self.assertIn("infrastructure_upgrade", result["templates"])
        self.assertIn("emergency", result["templates"])
        self.assertIn("routine", result["templates"])

    def test_get_templates_structure(self):
        """Templates have correct structure"""
        result = self.tool._get_templates()
        deployment = result["templates"]["deployment"]
        self.assertIn("default_duration", deployment)
        self.assertIn("description", deployment)
        self.assertIn("alert_suppression", deployment)
        self.assertIn("notification_required", deployment)

    # -------------------------------------------------------------------------
    # execute_maintenance_operation Tests
    # -------------------------------------------------------------------------

    @patch.object(MaintenanceWindowMCPTools, '_create_maintenance_window')
    def test_execute_operation_create(self, mock_create):
        """execute_maintenance_operation routes to _create_maintenance_window"""
        mock_create.return_value = {"status": "success", "window_id": "test-id"}
        
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="create",
            imap_code="EAL-012471",
            start_time=1234567890000,
            duration_minutes=60,
            reason="Test",
            ctx=self.ctx
        ))
        
        mock_create.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch.object(MaintenanceWindowMCPTools, '_modify_maintenance_window')
    def test_execute_operation_modify(self, mock_modify):
        """execute_maintenance_operation routes to _modify_maintenance_window"""
        mock_modify.return_value = {"status": "success"}
        
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="modify",
            window_id="test-id",
            duration_minutes=120,
            ctx=self.ctx
        ))
        
        mock_modify.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch.object(MaintenanceWindowMCPTools, '_close_maintenance_window')
    def test_execute_operation_close(self, mock_close):
        """execute_maintenance_operation routes to _close_maintenance_window"""
        mock_close.return_value = {"status": "success"}
        
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="close",
            window_id="test-id",
            ctx=self.ctx
        ))
        
        mock_close.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch.object(MaintenanceWindowMCPTools, '_list_active_windows')
    def test_execute_operation_list_active(self, mock_list):
        """execute_maintenance_operation routes to _list_active_windows"""
        mock_list.return_value = {"status": "success", "windows": []}
        
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="list_active",
            ctx=self.ctx
        ))
        
        mock_list.assert_called_once()
        self.assertEqual(result["status"], "success")

    def test_execute_operation_get_templates(self):
        """execute_maintenance_operation routes to _get_templates"""
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="get_templates",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "success")
        self.assertIn("templates", result)

    def test_execute_operation_invalid(self):
        """execute_maintenance_operation returns error for invalid operation"""
        result = asyncio.run(self.tool.execute_maintenance_operation(
            operation="invalid_operation",
            ctx=self.ctx
        ))
        
        self.assertIn("error", result)

    def test_execute_operation_exception_handling(self):
        """execute_maintenance_operation handles exceptions"""
        with patch.object(MaintenanceWindowMCPTools, '_create_maintenance_window', side_effect=Exception("Test error")):
            result = asyncio.run(self.tool.execute_maintenance_operation(
                operation="create",
                imap_code="EAL-012471",
                ctx=self.ctx
            ))
            
            self.assertIn("error", result)
            self.assertIn("Test error", result["error"])

    # -------------------------------------------------------------------------
    # _validate_window_params Tests
    # -------------------------------------------------------------------------

    @patch('src.maintenance_window.maintenance_window_tool.get_current_timestamp')
    def test_validate_window_params_valid(self, mock_timestamp):
        """_validate_window_params returns success for valid params"""
        # Mock current timestamp to be before start_time
        mock_timestamp.return_value = {"timestamp": 1234567890000 - 1000}
        
        result = asyncio.run(self.tool._validate_window_params(
            application_id="EAL-012471",
            start_time=1234567890000,
            duration_minutes=60,
            template="deployment",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "valid")
        self.assertIn("message", result)

    def test_validate_window_params_missing_application_id(self):
        """_validate_window_params returns error for missing application_id"""
        result = asyncio.run(self.tool._validate_window_params(
            application_id=None,
            start_time=1234567890000,
            duration_minutes=60,
            template="deployment",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "invalid")
        self.assertIn("errors", result)
        self.assertIn("application_id", result["errors"][0])

    def test_validate_window_params_missing_start_time(self):
        """_validate_window_params returns error for missing start_time"""
        result = asyncio.run(self.tool._validate_window_params(
            application_id="EAL-012471",
            start_time=None,
            duration_minutes=60,
            template="deployment",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "invalid")
        self.assertIn("errors", result)
        self.assertIn("start_time", result["errors"][0])

    @patch('src.maintenance_window.maintenance_window_tool.get_current_timestamp')
    def test_validate_window_params_past_start_time(self, mock_timestamp):
        """_validate_window_params returns error for past start_time"""
        # Mock current timestamp to be after start_time
        mock_timestamp.return_value = {"timestamp": 1234567890000 + 1000}
        
        result = asyncio.run(self.tool._validate_window_params(
            application_id="EAL-012471",
            start_time=1234567890000,
            duration_minutes=60,
            template="deployment",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "invalid")
        self.assertIn("errors", result)
        self.assertIn("past", result["errors"][0])

    @patch('src.maintenance_window.maintenance_window_tool.get_current_timestamp')
    def test_validate_window_params_invalid_template(self, mock_timestamp):
        """_validate_window_params returns error for invalid template"""
        # Mock current timestamp to be before start_time
        mock_timestamp.return_value = {"timestamp": 1234567890000 - 1000}
        
        result = asyncio.run(self.tool._validate_window_params(
            application_id="EAL-012471",
            start_time=1234567890000,
            duration_minutes=60,
            template="invalid_template",
            ctx=self.ctx
        ))
        
        self.assertEqual(result["status"], "invalid")
        self.assertIn("errors", result)
        self.assertIn("Invalid template", result["errors"][0])


if __name__ == '__main__':
    unittest.main()
