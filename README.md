# Prometheus MCP Server

A [Model Context Protocol][mcp] (MCP) server for Prometheus.

This provides access to your Prometheus metrics and queries through standardized MCP interfaces, allowing AI assistants to execute PromQL queries and analyze your metrics data.

<a href="https://glama.ai/mcp/servers/@pab1it0/prometheus-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@pab1it0/prometheus-mcp-server/badge" alt="Prometheus Server MCP server" />
</a>

[mcp]: https://modelcontextprotocol.io

## Quick Start

### 🚀 **For End Users (PyPI)**
```bash
# Install and run in one command
uvx --from raihan0824-prometheus-mcp-server prometheus-mcp-server
```

### 🛠️ **For Developers (Local)**
```bash
# Clone and install in development mode
git clone https://github.com/raihan0824/prometheus-mcp-server.git
cd prometheus-mcp-server
uv pip install -e .
prometheus-mcp-server
```

## Features

- [x] Execute PromQL queries against Prometheus
- [x] Discover and explore metrics
  - [x] List available metrics
  - [x] Get metadata for specific metrics
  - [x] View instant query results
  - [x] View range query results with different step intervals
- [x] Authentication support
  - [x] Basic auth from environment variables
  - [x] Bearer token auth from environment variables
- [x] Docker containerization support

- [x] Provide interactive tools for AI assistants

The list of tools is configurable, so you can choose which tools you want to make available to the MCP client.
This is useful if you don't use certain functionality or if you don't want to take up too much of the context window.

## Installation

### Option 1: Install from PyPI (Recommended for Users)

```bash
# Using uvx (recommended for Claude Desktop)
uvx --from raihan0824-prometheus-mcp-server prometheus-mcp-server

# Using pip
pip install raihan0824-prometheus-mcp-server

# Using uv
uv add raihan0824-prometheus-mcp-server
```

### Option 2: Install from Source (For Development)

```bash
# Clone the repository
git clone https://github.com/raihan0824/prometheus-mcp-server.git
cd prometheus-mcp-server

# Install with uv (development mode)
uv pip install -e .

# Or install with pip (development mode)
pip install -e .
```

## Usage

### For End Users (Using PyPI Package)

If you want to use the pre-built package from PyPI:

```bash
# Install and run in one command
uvx --from raihan0824-prometheus-mcp-server prometheus-mcp-server

# Or install permanently
pip install raihan0824-prometheus-mcp-server
prometheus-mcp-server
```

### For Developers (Local Development)

If you want to modify the code or contribute:

```bash
# Clone and install in development mode
git clone https://github.com/raihan0824/prometheus-mcp-server.git
cd prometheus-mcp-server
uv pip install -e .

# Run the development version
prometheus-mcp-server
```

---

1. Ensure your Prometheus server is accessible from the environment where you'll run this MCP server.

2. Configure the environment variables for your Prometheus server, either through a `.env` file or system environment variables:

```env
# Required: Prometheus configuration
PROMETHEUS_URL=http://your-prometheus-server:9090

# Optional: Authentication credentials (if needed)
# Choose one of the following authentication methods if required:

# For basic auth
PROMETHEUS_USERNAME=your_username
PROMETHEUS_PASSWORD=your_password

# For bearer token auth
PROMETHEUS_TOKEN=your_token

# Optional: Custom MCP configuration
PROMETHEUS_MCP_SERVER_TRANSPORT=stdio # Choose between http, stdio, sse. If undefined, stdio is set as the default transport.

# Optional: Only relevant for non-stdio transports
PROMETHEUS_MCP_BIND_HOST=localhost # if undefined, 127.0.0.1 is set by default.
PROMETHEUS_MCP_BIND_PORT=8080 # if undefined, 8080 is set by default.

# Optional: For multi-tenant setups like Cortex, Mimir or Thanos
ORG_ID=your_organization_id
```

3. Add the server configuration to your client configuration file. For example, for Claude Desktop:

### Option A: Using uvx with PyPI package (Recommended for Users)

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "uvx",
      "args": [
        "--from",
        "raihan0824-prometheus-mcp-server",
        "prometheus-mcp-server"
      ],
      "env": {
        "PROMETHEUS_URL": "<your-prometheus-url>",
        "PROMETHEUS_USERNAME": "<your-username>",
        "PROMETHEUS_PASSWORD": "<your-password>"
      }
    }
  }
}
```

### Option B: Using uvx with local repository

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "uvx",
      "args": [
        "--directory",
        "/path/to/prometheus-mcp-server",
        "run",
        "prometheus-mcp-server"
      ],
      "env": {
        "PROMETHEUS_URL": "<your-prometheus-url>",
        "PROMETHEUS_USERNAME": "<your-username>",
        "PROMETHEUS_PASSWORD": "<your-password>"
      }
    }
  }
}
```

### Option C: Using uvx with Git repository

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "uvx",
      "args": [
        "run",
        "--from",
        "git+https://github.com/raihan0824/prometheus-mcp-server.git",
        "prometheus-mcp-server"
      ],
      "env": {
        "PROMETHEUS_URL": "<your-prometheus-url>",
        "PROMETHEUS_USERNAME": "<your-username>",
        "PROMETHEUS_PASSWORD": "<your-password>"
      }
    }
  }
}
```

### Option D: Using Docker (Legacy)

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "PROMETHEUS_URL",
        "ghcr.io/pab1it0/prometheus-mcp-server:latest"
      ],
      "env": {
        "PROMETHEUS_URL": "<url>",
        "PROMETHEUS_MCP_SERVER_TRANSPORT": "http",
        "PROMETHEUS_MCP_BIND_HOST": "localhost",
        "PROMETHEUS_MCP_BIND_PORT": "8080"
      }
    }
  }
}
```


## Development

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

This project uses [`uv`](https://github.com/astral-sh/uv) to manage dependencies. Install `uv` following the instructions for your platform:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You can then create a virtual environment and install the dependencies with:

```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows
uv pip install -e .
```

## Project Structure

The project has been organized with a `src` directory structure:

```
prometheus-mcp-server/
├── src/
│   └── prometheus_mcp_server/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # MCP server implementation
│       ├── main.py          # Main application logic
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── .dockerignore            # Docker ignore file
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

### Testing

The project includes a comprehensive test suite that ensures functionality and helps prevent regressions.

Run the tests with pytest:

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run the tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```
Tests are organized into:

- Configuration validation tests
- Server functionality tests
- Error handling tests
- Main application tests

When adding new features, please also add corresponding tests.

### Tools

| Tool | Category | Description |
| --- | --- | --- |
| `execute_query` | Query | Execute a PromQL instant query against Prometheus |
| `execute_range_query` | Query | Execute a PromQL range query with start time, end time, and step interval |
| `list_metrics` | Discovery | List all available metrics in Prometheus |
| `get_metric_metadata` | Discovery | Get metadata for a specific metric |
| `get_targets` | Discovery | Get information about all scrape targets |

## License

MIT

---

[mcp]: https://modelcontextprotocol.io