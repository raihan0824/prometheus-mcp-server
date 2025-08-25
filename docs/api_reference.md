# API Reference

This document provides detailed information about the API endpoints and functions provided by the Prometheus MCP Server.

## MCP Tools

### Query Tools

#### `execute_query`

Executes a PromQL instant query against Prometheus.

**Description**: Retrieves current values for a given PromQL expression.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The PromQL query expression |
| `time` | string | No | Evaluation timestamp (RFC3339 or Unix timestamp) |

**Returns**: Object with `resultType` and `result` fields.

```json
{
  "resultType": "vector",
  "result": [
    {
      "metric": { "__name__": "up", "job": "prometheus", "instance": "localhost:9090" },
      "value": [1617898448.214, "1"]
    }
  ]
}
```

#### `execute_range_query`

Executes a PromQL range query with start time, end time, and step interval.

**Description**: Retrieves values for a given PromQL expression over a time range.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The PromQL query expression |
| `start` | string | Yes | Start time (RFC3339 or Unix timestamp) |
| `end` | string | Yes | End time (RFC3339 or Unix timestamp) |
| `step` | string | Yes | Query resolution step (e.g., "15s", "1m", "1h") |

**Returns**: Object with `resultType` and `result` fields.

```json
{
  "resultType": "matrix",
  "result": [
    {
      "metric": { "__name__": "up", "job": "prometheus", "instance": "localhost:9090" },
      "values": [
        [1617898400, "1"],
        [1617898415, "1"],
        [1617898430, "1"]
      ]
    }
  ]
}
```

### Discovery Tools

#### `list_metrics`

List all available metrics in Prometheus.

**Description**: Retrieves a list of all metric names available in the Prometheus server.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of metrics to return (0 = unlimited) |

**Returns**: Array of metric names.

```json
["up", "go_goroutines", "http_requests_total", ...]
```

**Example with pagination**:
```json
// Call with {"limit": 2}
["up", "go_goroutines"]
```

#### `get_metric_metadata`

Get metadata for a specific metric.

**Description**: Retrieves metadata information about a specific metric.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `metric` | string | Yes | The name of the metric |
| `limit` | integer | No | Maximum number of metadata entries to return |

**Returns**: Array of metadata objects.

```json
[
  {
    "metric": "up",
    "type": "gauge",
    "help": "Up indicates if the scrape was successful",
    "unit": ""
  }
]
```

#### `get_targets`

Get information about all scrape targets.

**Description**: Retrieves the current state of all Prometheus scrape targets.

**Parameters**: None

**Returns**: Object with `activeTargets` and `droppedTargets` arrays.

```json
{
  "activeTargets": [
    {
      "discoveredLabels": {
        "__address__": "localhost:9090",
        "__metrics_path__": "/metrics",
        "__scheme__": "http",
        "job": "prometheus"
      },
      "labels": {
        "instance": "localhost:9090",
        "job": "prometheus"
      },
      "scrapePool": "prometheus",
      "scrapeUrl": "http://localhost:9090/metrics",
      "lastError": "",
      "lastScrape": "2023-04-08T12:00:45.123Z",
      "lastScrapeDuration": 0.015,
      "health": "up"
    }
  ],
  "droppedTargets": []
}
```

#### `list_labels`

List all available label names in Prometheus.

**Description**: Retrieves a list of all label names available across all metrics in the Prometheus server.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of label names to return |

**Returns**: Array of label names.

```json
["__name__", "job", "instance", "handler", "method"]
```

#### `get_label_values`

Get all values for a specific label.

**Description**: Retrieves all possible values for a given label name.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `label_name` | string | Yes | The name of the label |
| `limit` | integer | No | Maximum number of label values to return |

**Returns**: Array of label values.

```json
["prometheus", "node-exporter", "alertmanager"]
```

#### `find_series`

Find time series by label matchers.

**Description**: Returns a list of time series that match the specified label selectors.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `match` | array | Yes | Array of series selector expressions |
| `limit` | integer | No | Maximum number of series to return |
| `start` | string | No | Start time for series search (RFC3339 or Unix timestamp) |
| `end` | string | No | End time for series search (RFC3339 or Unix timestamp) |

**Returns**: Array of label sets representing the series.

```json
[
  {
    "__name__": "up",
    "job": "prometheus",
    "instance": "localhost:9090"
  },
  {
    "__name__": "up", 
    "job": "node-exporter",
    "instance": "localhost:9100"
  }
]
```

**Example with multiple matchers**:
```json
// Call with {"match": ["up", "process_start_time_seconds{job=\"prometheus\"}"], "limit": 5}
```

## Pagination Support

Several MCP tools now support pagination through the optional `limit` parameter:

- **`list_metrics`**: Limit the number of metric names returned
- **`get_metric_metadata`**: Limit the number of metadata entries returned  
- **`list_labels`**: Limit the number of label names returned
- **`get_label_values`**: Limit the number of label values returned
- **`find_series`**: Limit the number of time series returned

**Key points about pagination**:
- All pagination parameters are optional - omit them for unlimited results
- `limit=0` disables the limit (returns all results)
- The Prometheus API doesn't support `offset`-based pagination
- Results are returned in the order provided by Prometheus (typically alphabetical for labels/metrics)

## Prometheus API Endpoints

The MCP server interacts with the following Prometheus API endpoints:

### `/api/v1/query`

Used by `execute_query` to perform instant queries.

### `/api/v1/query_range`

Used by `execute_range_query` to perform range queries.

### `/api/v1/label/__name__/values`

Used by `list_metrics` to retrieve all metric names.

### `/api/v1/metadata`

Used by `get_metric_metadata` to retrieve metadata about metrics.

### `/api/v1/targets`

Used by `get_targets` to retrieve information about scrape targets.

### `/api/v1/labels`

Used by `list_labels` to retrieve all label names.

### `/api/v1/label/<label_name>/values`

Used by `get_label_values` to retrieve values for a specific label.

### `/api/v1/series`

Used by `find_series` to find time series matching label selectors.

## Error Handling

All tools return standardized error responses when problems occur:

1. **Connection errors**: When the server cannot connect to Prometheus
2. **Authentication errors**: When credentials are invalid or insufficient
3. **Query errors**: When a PromQL query is invalid or fails to execute
4. **Not found errors**: When requested metrics or data don't exist

Error messages are descriptive and include the specific issue that occurred.

## Result Types

Prometheus returns different result types depending on the query:

### Instant Query Result Types

- **Vector**: A set of time series, each with a single sample (most common for instant queries)
- **Scalar**: A single numeric value
- **String**: A string value

### Range Query Result Types

- **Matrix**: A set of time series, each with multiple samples over time (most common for range queries)

## Time Formats

Time parameters accept either:

1. **RFC3339 timestamps**: `2023-04-08T12:00:00Z`
2. **Unix timestamps**: `1617869245.324`

If not specified, the current time is used for instant queries.