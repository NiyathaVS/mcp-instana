"""
E2E tests for Application Topology MCP Tools
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.application_topology import ApplicationTopologyMCPTools
from src.core.server import MCPState, execute_tool


class TestApplicationTopologyE2E:
    """End-to-end tests for Application Topology MCP Tools"""

    @pytest.mark.asyncio
    @pytest.mark.mocked
    async def test_get_application_topology_initialization_error(self, instana_credentials):
        """Test error handling during initialization."""

        with patch('src.application.application_topology.ApplicationTopologyApi',
                  side_effect=Exception("Initialization Error")):

            # This should raise an exception during initialization
            with pytest.raises(Exception) as excinfo:
                _ = ApplicationTopologyMCPTools(
                    read_token=instana_credentials["api_token"],
                    base_url=instana_credentials["base_url"]
                )

            # Verify the exception message
            assert "Initialization Error" in str(excinfo.value)

    @pytest.mark.asyncio
    @pytest.mark.mocked
    async def test_missing_tool_in_mcp(self, instana_credentials):
        """Test handling of missing tool in MCP."""

        # Create MCP state without setting the app_topology_client
        state = MCPState()
        state.instana_api_token = instana_credentials["api_token"]
        state.instana_base_url = instana_credentials["base_url"]

        # Execute a non-existent tool
        result = await execute_tool(
            "non_existent_tool",
            {},
            state
        )

        # Verify the result contains an error message
        assert isinstance(result, str)
        assert "Tool non_existent_tool not found" in result

    @pytest.mark.mocked
    def test_import_error_handling(self):
        """Test handling of import errors in the module."""

        # We can't directly test the import error handling since imports are evaluated
        # at module load time, but we can verify that the code has proper error handling
        # by examining the module source code

        import inspect

        import src.application.application_topology as module

        # Get the source code of the module
        source_code = inspect.getsource(module)

        # Verify that the module has proper import error handling
        assert "try:" in source_code
        assert "from instana_client.api.application_topology_api import (" in source_code
        assert "ApplicationTopologyApi" in source_code
        assert "except ImportError as e:" in source_code
        assert "logger.error(f\"Error importing Instana SDK: {e}\"" in source_code
        assert "traceback.print_exc" in source_code
        assert "raise" in source_code

