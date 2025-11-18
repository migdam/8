"""API and HTTP request tools for Deep Agents v2"""

from typing import Optional, Dict, Any
import httpx
import json

from .base import BaseTool, ToolOutput
from ..utils.logger import get_logger

logger = get_logger(__name__)


class APICallerTool(BaseTool):
    """Make HTTP API requests"""

    def __init__(self, timeout: int = 30):
        super().__init__()
        self.description = "Make HTTP requests to APIs (GET, POST, PUT, DELETE)"
        self.timeout = timeout

    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[str] = None
    ) -> ToolOutput:
        """
        Execute HTTP request

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Request URL
            headers: Optional headers
            params: Optional query parameters
            json_data: Optional JSON body
            data: Optional raw body data

        Returns:
            ToolOutput with response
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data
                )

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text

                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "url": str(response.url)
                }

                logger.info(f"API request to {url}: {response.status_code}")
                return ToolOutput(success=True, result=result)

        except httpx.TimeoutException:
            logger.error(f"API request timeout: {url}")
            return ToolOutput(success=False, result=None, error="Request timeout")
        except Exception as e:
            logger.error(f"API request error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))


class WebhookTool(BaseTool):
    """Send webhook notifications"""

    def __init__(self):
        super().__init__()
        self.description = "Send webhook notifications to external services"

    async def execute(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> ToolOutput:
        """
        Send webhook

        Args:
            webhook_url: Webhook URL
            payload: Data to send
            headers: Optional headers

        Returns:
            ToolOutput with result
        """
        try:
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers
                )

                logger.info(f"Webhook sent to {webhook_url}: {response.status_code}")
                return ToolOutput(
                    success=True,
                    result={
                        "status_code": response.status_code,
                        "response": response.text[:500]
                    }
                )

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return ToolOutput(success=False, result=None, error=str(e))
