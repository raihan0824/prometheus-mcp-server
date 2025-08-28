#!/usr/bin/env python

import os
import json
import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass
import time
from datetime import datetime, timedelta, timezone
from enum import Enum

import dotenv
import requests
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from prometheus_mcp_server.logging_config import get_logger

dotenv.load_dotenv()
server = Server("Prometheus MCP")

# Get logger instance
logger = get_logger()

# MCP Tool definitions using official SDK approach

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Prometheus MCP tools."""
    return [
        types.Tool(
            name="health_check",
            description="Health check endpoint for container monitoring and status verification",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="execute_query",
            description="Execute a PromQL instant query against Prometheus",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PromQL query string"
                    },
                    "time": {
                        "type": "string",
                        "description": "Optional RFC3339 or Unix timestamp (default: current time)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="execute_range_query",
            description="Execute a PromQL range query with start time, end time, and step interval",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PromQL query string"
                    },
                    "start": {
                        "type": "string",
                        "description": "Start time as RFC3339 or Unix timestamp"
                    },
                    "end": {
                        "type": "string",
                        "description": "End time as RFC3339 or Unix timestamp"
                    },
                    "step": {
                        "type": "string",
                        "description": "Query resolution step width (e.g., '15s', '1m', '1h')"
                    }
                },
                "required": ["query", "start", "end", "step"]
            }
        ),
        types.Tool(
            name="list_metrics",
            description="List all available metrics in Prometheus",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_metric_metadata",
            description="Get metadata for a specific metric",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "The name of the metric to retrieve metadata for"
                    }
                },
                "required": ["metric"]
            }
        ),
        types.Tool(
            name="get_targets",
            description="Get information about all scrape targets",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls and return structured responses."""
    
    if name == "health_check":
        try:
            health_data = {
                "status": "healthy",
                "service": "prometheus-mcp-server", 
                "version": "1.2.11",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "transport": config.mcp_server_config.mcp_server_transport if config.mcp_server_config else "stdio",
                "configuration": {
                    "prometheus_url_configured": bool(config.url),
                    "authentication_configured": bool(config.username or config.token),
                    "org_id_configured": bool(config.org_id)
                },
                "checks": {
                    "server": "healthy",
                    "prometheus": "unknown"
                }
            }
            
            # Test Prometheus connectivity if configured
            if config.url:
                try:
                    # Quick connectivity test
                    make_prometheus_request("query", params={"query": "up", "time": str(int(time.time()))})
                    health_data["prometheus_connectivity"] = "healthy"
                    health_data["prometheus_url"] = config.url
                    health_data["checks"]["prometheus"] = "healthy"
                except Exception as e:
                    health_data["prometheus_connectivity"] = "unhealthy"
                    health_data["prometheus_error"] = str(e)
                    health_data["status"] = "degraded"
                    health_data["checks"]["prometheus"] = "unhealthy"
            else:
                health_data["status"] = "unhealthy"
                health_data["error"] = "PROMETHEUS_URL not configured"
                health_data["checks"]["prometheus"] = "not_configured"
            
            logger.info("Health check completed", status=health_data["status"])
            return [
                types.TextContent(
                    type="text",
                    text=f"Service: {health_data['service']}\nStatus: {health_data['status']}\nVersion: {health_data['version']}\nTimestamp: {health_data['timestamp']}"
                ),
                types.TextContent(
                    type="text",
                    text=f"Prometheus URL configured: {health_data['configuration']['prometheus_url_configured']}\nAuthentication configured: {health_data['configuration']['authentication_configured']}\nOrg ID configured: {health_data['configuration']['org_id_configured']}"
                )
            ]
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Health check failed: {str(e)}"
                )
            ]
    
    elif name == "execute_query":
        try:
            query = arguments["query"]
            time_param = arguments.get("time")
            
            params = {"query": query}
            if time_param:
                params["time"] = time_param
            
            logger.info("Executing instant query", query=query, time=time_param)
            data = make_prometheus_request("query", params=params)
            
            result_count = len(data["result"]) if isinstance(data["result"], list) else 1
            
            logger.info("Instant query completed", 
                        query=query, 
                        result_type=data["resultType"], 
                        result_count=result_count)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Query: {query}\nResult Type: {data['resultType']}\nResults Count: {result_count}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                ),
                types.TextContent(
                    type="text", 
                    text=f"Results: {json.dumps(data['result'], indent=2)}"
                )
            ]
            
        except Exception as e:
            logger.error("Query execution failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Query execution failed: {str(e)}"
                )
            ]
    
    elif name == "execute_range_query":
        try:
            query = arguments["query"]
            start = arguments["start"]
            end = arguments["end"]
            step = arguments["step"]
            
            params = {
                "query": query,
                "start": start,
                "end": end,
                "step": step
            }
            
            logger.info("Executing range query", query=query, start=start, end=end, step=step)
            data = make_prometheus_request("query_range", params=params)
            
            result_count = len(data["result"]) if isinstance(data["result"], list) else 1
            
            logger.info("Range query completed", 
                        query=query, 
                        result_type=data["resultType"], 
                        result_count=result_count)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Query: {query}\nStart: {start}\nEnd: {end}\nStep: {step}\nResult Type: {data['resultType']}\nResults Count: {result_count}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                ),
                types.TextContent(
                    type="text",
                    text=f"Results: {json.dumps(data['result'], indent=2)}"
                )
            ]
            
        except Exception as e:
            logger.error("Range query execution failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Range query execution failed: {str(e)}"
                )
            ]
    
    elif name == "list_metrics":
        try:
            logger.info("Listing available metrics")
            data = make_prometheus_request("label/__name__/values")
            logger.info("Metrics list retrieved", metric_count=len(data))
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Total metrics available: {len(data)}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                ),
                types.TextContent(
                    type="text",
                    text="All available metrics:\n" + "\n".join([f"- {metric}" for metric in data])
                )
            ]
            
        except Exception as e:
            logger.error("List metrics failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to list metrics: {str(e)}"
                )
            ]
    
    elif name == "get_metric_metadata":
        try:
            metric = arguments["metric"]
            
            logger.info("Retrieving metric metadata", metric=metric)
            params = {"metric": metric}
            data = make_prometheus_request("metadata", params=params)
            logger.info("Metric metadata retrieved", metric=metric, metadata_count=len(data["metadata"]))
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Metric: {metric}\nMetadata entries: {len(data['metadata'])}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                ),
                types.TextContent(
                    type="text",
                    text=f"Metadata: {json.dumps(data['metadata'], indent=2)}"
                )
            ]
            
        except Exception as e:
            logger.error("Get metric metadata failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to get metric metadata: {str(e)}"
                )
            ]
    
    elif name == "get_targets":
        try:
            logger.info("Retrieving scrape targets information")
            data = make_prometheus_request("targets")
            
            active_count = len(data["activeTargets"])
            dropped_count = len(data["droppedTargets"])
            total_count = active_count + dropped_count
            
            logger.info("Scrape targets retrieved", 
                        active_targets=active_count, 
                        dropped_targets=dropped_count)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Active targets: {active_count}\nDropped targets: {dropped_count}\nTotal targets: {total_count}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                ),
                types.TextContent(
                    type="text",
                    text=f"Active targets: {json.dumps(data['activeTargets'], indent=2)}"
                ),
                types.TextContent(
                    type="text",
                    text=f"Dropped targets: {json.dumps(data['droppedTargets'], indent=2)}"
                )
            ]
            
        except Exception as e:
            logger.error("Get targets failed", error=str(e))
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to get targets: {str(e)}"
                )
            ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


class TransportType(str, Enum):
    """Supported MCP server transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"

    @classmethod
    def values(cls) -> list[str]:
        """Get all valid transport values."""
        return [transport.value for transport in cls]

@dataclass
class MCPServerConfig:
    """Global Configuration for MCP."""
    mcp_server_transport: TransportType = None
    mcp_bind_host: str = None
    mcp_bind_port: int = None

    def __post_init__(self):
        """Validate mcp configuration."""
        if not self.mcp_server_transport:
            raise ValueError("MCP SERVER TRANSPORT is required")
        if not self.mcp_bind_host:
            raise ValueError(f"MCP BIND HOST is required")
        if not self.mcp_bind_port:
            raise ValueError(f"MCP BIND PORT is required")

@dataclass
class PrometheusConfig:
    url: str
    # Optional credentials
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    # Optional Org ID for multi-tenant setups
    org_id: Optional[str] = None
    # Optional Custom MCP Server Configuration
    mcp_server_config: Optional[MCPServerConfig] = None

config = PrometheusConfig(
    url=os.environ.get("PROMETHEUS_URL", ""),
    username=os.environ.get("PROMETHEUS_USERNAME", ""),
    password=os.environ.get("PROMETHEUS_PASSWORD", ""),
    token=os.environ.get("PROMETHEUS_TOKEN", ""),
    org_id=os.environ.get("ORG_ID", ""),
    mcp_server_config=MCPServerConfig(
        mcp_server_transport=os.environ.get("PROMETHEUS_MCP_SERVER_TRANSPORT", "stdio").lower(),
        mcp_bind_host=os.environ.get("PROMETHEUS_MCP_BIND_HOST", "127.0.0.1"),
        mcp_bind_port=int(os.environ.get("PROMETHEUS_MCP_BIND_PORT", "8080"))
    )
)

def get_prometheus_auth():
    """Get authentication for Prometheus based on provided credentials."""
    if config.token:
        return {"Authorization": f"Bearer {config.token}"}
    elif config.username and config.password:
        return requests.auth.HTTPBasicAuth(config.username, config.password)
    return None

def make_prometheus_request(endpoint, params=None):
    """Make a request to the Prometheus API with proper authentication and headers."""
    if not config.url:
        logger.error("Prometheus configuration missing", error="PROMETHEUS_URL not set")
        raise ValueError("Prometheus configuration is missing. Please set PROMETHEUS_URL environment variable.")

    url = f"{config.url.rstrip('/')}/api/v1/{endpoint}"
    auth = get_prometheus_auth()
    headers = {"User-Agent": "prometheus-mcp-server/1.2.11"}

    if isinstance(auth, dict):  # Token auth is passed via headers
        headers.update(auth)
        auth = None  # Clear auth for requests.get if it's already in headers
    
    # Add OrgID header if specified
    if config.org_id:
        headers["X-Scope-OrgID"] = config.org_id

    try:
        logger.debug("Making Prometheus API request", endpoint=endpoint, url=url, params=params)
        
        # Make the request with appropriate headers, auth, and timeout
        response = requests.get(
            url, 
            params=params, 
            auth=auth, 
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result["status"] != "success":
            error_msg = result.get('error', 'Unknown error')
            logger.error("Prometheus API returned error", endpoint=endpoint, error=error_msg, status=result["status"])
            raise ValueError(f"Prometheus API error: {error_msg}")
        
        data_field = result.get("data", {})
        if isinstance(data_field, dict):
            result_type = data_field.get("resultType")
        else:
            result_type = "list"
        logger.debug("Prometheus API request successful", endpoint=endpoint, result_type=result_type)
        return result["data"]
    
    except requests.exceptions.Timeout as e:
        logger.error("Request timed out", endpoint=endpoint, url=url, timeout="30s")
        raise ValueError(f"Prometheus server at {config.url} is not responding (timeout after 30s)")
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection failed", endpoint=endpoint, url=url, error=str(e))
        raise ValueError(f"Cannot connect to Prometheus server at {config.url}")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        logger.error("HTTP error", endpoint=endpoint, url=url, status_code=status_code, error=str(e))
        if status_code == 401:
            raise ValueError("Authentication failed. Please check your Prometheus credentials.")
        elif status_code == 403:
            raise ValueError("Access forbidden. Please check your Prometheus permissions.")
        else:
            raise ValueError(f"HTTP {status_code} error from Prometheus server")
    except requests.exceptions.RequestException as e:
        logger.error("HTTP request to Prometheus failed", endpoint=endpoint, url=url, error=str(e), error_type=type(e).__name__)
        raise ValueError(f"Request failed: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Prometheus response as JSON", endpoint=endpoint, url=url, error=str(e))
        raise ValueError(f"Invalid JSON response from Prometheus: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error during Prometheus request", endpoint=endpoint, url=url, error=str(e), error_type=type(e).__name__)
        raise ValueError(f"Unexpected error: {str(e)}")


async def main():
    """Run the MCP server with stdio transport."""
    
    # Server capabilities
    init_options = InitializationOptions(
        server_name="prometheus-mcp-server",
        server_version="1.2.11",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    # Run server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            init_options
        )

if __name__ == "__main__":
    logger.info("Starting Prometheus MCP Server", mode="direct")
    asyncio.run(main())
