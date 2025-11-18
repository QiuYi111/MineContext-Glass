# MineContext Glass API Documentation

**Generated:** 2025-01-18
**Version:** 1.0.0
**Base URL:** `http://localhost:8000` (default)

## Overview

MineContext Glass provides two main API layers:
- **OpenContext Core**: General-purpose context management framework
- **Glass Extension**: Video-first context capture for smart glasses

All APIs use FastAPI with automatic OpenAPI documentation available at `/docs`.

## Authentication

Most endpoints require authentication. The system uses a dependency-based auth system (`_auth = auth_dependency`). Authentication status can be checked via:

```http
GET /api/auth/status
```

## Response Format

All API responses follow a consistent format through the `convert_resp` utility:

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2025-01-18T10:00:00Z"
}
```

---

## 🏗️ OpenContext Core APIs

### Health Check

#### `GET /health`
Basic health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-18T10:00:00Z"
}
```

#### `GET /api/health`
Detailed health check with component status.

**Response:**
```json
{
  "status": "ok",
  "components": {
    "database": "ok",
    "vector_db": "ok",
    "storage": "ok"
  },
  "timestamp": "2025-01-18T10:00:00Z"
}
```

---

### Context Management (`/contexts`)

#### `POST /contexts/delete`
Delete processed context data.

**Request Body:**
```json
{
  "context_ids": ["id1", "id2"],
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-01-18"
  }
}
```

#### `POST /contexts/detail`
Get detailed context information (HTML response).

**Request Body:**
```json
{
  "context_id": "string",
  "include_metadata": true
}
```

#### `GET /api/context_types`
Get all available context types.

**Response:**
```json
{
  "types": ["screenshot", "document", "video", "audio"],
  "count": 4
}
```

#### `POST /api/vector_search`
Perform vector search without LLM processing.

**Request Body:**
```json
{
  "query": "search query",
  "limit": 10,
  "filters": {
    "context_type": "screenshot",
    "date_range": "last_7_days"
  }
}
```

---

### Screenshot Management (`/screenshots`)

#### `POST /api/add_screenshot`
Add a single screenshot.

**Request Body (multipart/form-data):**
- `file`: Image file
- `metadata`: JSON metadata (optional)
- `timestamp`: Capture timestamp (optional)

#### `POST /api/add_screenshots`
Add multiple screenshots in batch.

**Request Body (multipart/form-data):**
- `files`: Multiple image files
- `metadata`: JSON metadata array
- `timestamps`: Timestamp array

---

### Model Settings (`/model_settings`)

#### `GET /api/model_settings/get`
Get current model configuration.

**Response:**
```json
{
  "llm_provider": "openai",
  "model_name": "gpt-4",
  "api_config": {
    "base_url": "https://api.openai.com/v1",
    "max_tokens": 4096
  }
}
```

#### `POST /api/model_settings/update`
Update model configuration.

**Request Body:**
```json
{
  "llm_provider": "openai",
  "model_name": "gpt-4-turbo",
  "api_config": {
    "base_url": "https://api.openai.com/v1",
    "max_tokens": 8192
  }
}
```

#### `POST /api/model_settings/validate`
Validate LLM configuration.

**Request Body:**
```json
{
  "llm_provider": "openai",
  "model_name": "gpt-4",
  "test_query": "Hello, world!"
}
```

---

### Vault Management (`/vaults`)

#### `GET /api/vaults/list`
Get list of documents in vault.

**Query Parameters:**
- `limit`: Number of documents (default: 50)
- `offset`: Pagination offset (default: 0)
- `search`: Search query (optional)

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "title": "Meeting Notes",
      "created_at": "2025-01-18T10:00:00Z",
      "updated_at": "2025-01-18T11:00:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

#### `POST /api/vaults/create`
Create new document.

**Request Body:**
```json
{
  "title": "Document Title",
  "content": "Document content",
  "tags": ["tag1", "tag2"]
}
```

#### `GET /api/vaults/{document_id}`
Get document details.

**Path Parameters:**
- `document_id`: Document identifier

**Response:**
```json
{
  "id": "doc_123",
  "title": "Document Title",
  "content": "Document content",
  "tags": ["tag1", "tag2"],
  "created_at": "2025-01-18T10:00:00Z",
  "updated_at": "2025-01-18T11:00:00Z"
}
```

#### `POST /api/vaults/{document_id}`
Save document updates.

#### `DELETE /api/vaults/{document_id}`
Delete document.

#### `GET /api/vaults/{document_id}/context`
Get document context processing status.

---

### Agent Chat (`/api/agent`)

#### `POST /api/agent/chat`
Non-streaming intelligent chat interface.

**Request Body:**
```json
{
  "message": "User message",
  "context_id": "optional_context_id",
  "conversation_id": "optional_conversation_id"
}
```

**Response:**
```json
{
  "response": "AI response",
  "conversation_id": "conv_123",
  "context_used": ["ctx_1", "ctx_2"]
}
```

#### `POST /api/agent/chat/stream`
Streaming intelligent chat interface.

**Request Body:** Same as non-streaming endpoint.

**Response:** Server-Sent Events (SSE) stream.

#### `POST /api/agent/resume/{workflow_id}`
Resume workflow execution.

#### `GET /api/agent/state/{workflow_id}`
Get workflow execution state.

#### `DELETE /api/agent/cancel/{workflow_id}`
Cancel workflow execution.

#### `GET /api/agent/test`
Test Context Agent functionality.

---

### Smart Completions (`/api/completions`)

#### `POST /api/completions/suggest`
Get intelligent completion suggestions.

**Request Body:**
```json
{
  "context": "Current text context",
  "cursor_position": 150,
  "document_id": "optional_document_id"
}
```

#### `POST /api/completions/suggest/stream`
Streaming completion suggestions.

#### `POST /api/completions/feedback`
Submit completion feedback.

**Request Body:**
```json
{
  "completion_id": "comp_123",
  "rating": "positive",
  "feedback_text": "Helpful suggestion"
}
```

#### `GET /api/completions/stats`
Get completion service statistics.

#### `GET /api/completions/cache/stats`
Get cache statistics.

#### `POST /api/completions/cache/optimize`
Optimize completion cache.

#### `POST /api/completions/precompute/{document_id}`
Precompute document context.

#### `POST /api/completions/cache/clear`
Clear completion cache.

---

### Content Generation (`/api/content_generation`)

#### `GET /api/content_generation/status`
Get content generation service status.

#### `POST /api/content_generation/start`
Start content generation scheduled task.

#### `POST /api/content_generation/stop`
Stop content generation scheduled task.

---

### Events (`/api/events`)

#### `GET /api/events/fetch`
Fetch and clear cached events.

#### `GET /api/events/status`
Get event cache status.

#### `POST /api/events/publish`
Publish event to system.

**Request Body:**
```json
{
  "event_type": "context_processed",
  "data": {
    "context_id": "ctx_123",
    "status": "completed"
  }
}
```

---

### Monitoring (`/api/monitoring`)

#### `GET /api/monitoring/overview`
Get system monitoring overview.

#### `GET /api/monitoring/context-types`
Get context type statistics.

#### `GET /api/monitoring/token-usage`
Get model token consumption details.

#### `GET /api/monitoring/processing`
Get processor performance metrics.

#### `GET /api/monitoring/todo-stats`
Get TODO task statistics.

#### `GET /api/monitoring/tips-count`
Get tips count.

#### `GET /api/monitoring/activity-count`
Get activity record count.

#### `POST /api/monitoring/refresh-context-stats`
Refresh context type statistics cache.

#### `GET /api/monitoring/health`
Monitoring system health check.

#### `GET /api/monitoring/chromadb-status`
Get ChromaDB model status.

#### `GET /api/monitoring/ffmpeg-status`
Get FFmpeg installation status.

---

### Debug (`/api/debug`)

#### `GET /api/debug/reports`
Get debug report data.

#### `GET /api/debug/todos`
Get debug TODO data.

#### `GET /api/debug/activities`
Get debug activity record data.

#### `GET /api/debug/tips`
Get debug tips data.

#### `PATCH /api/debug/todos/{todo_id}`
Update TODO status.

#### `POST /api/debug/generate/report`
Manually generate debug report.

#### `POST /api/debug/generate/activity`
Manually generate debug activity.

#### `POST /api/debug/generate/tips`
Manually generate debug tips.

#### `POST /api/debug/generate/todos`
Manually generate debug TODO.

#### `GET /api/debug/prompts/export`
Export generation prompts.

#### `POST /api/debug/prompts/restore`
Restore prompts.

#### `GET /api/debug/prompts/{category}`
Get prompts by category.

#### `POST /api/debug/prompts/{category}`
Update prompts by category.

#### `POST /api/debug/generate/{category}/custom`
Generate content using custom prompts.

---

## 🥽 Glass Extension APIs

### Video Processing (`/glass`)

#### `POST /glass/upload`
Upload video file for processing.

**Request Body (multipart/form-data):**
- `file`: Video file (MP4, MOV, etc.)
- `date`: Date for processing (dd-mm format)
- `metadata`: JSON metadata (optional)

**Response:**
```json
{
  "upload_id": "upload_123",
  "status": "processing",
  "timeline_id": "timeline_456"
}
```

#### `GET /glass/uploads/limits`
Get upload limits and constraints.

**Response:**
```json
{
  "max_file_size": "500MB",
  "supported_formats": ["mp4", "mov", "avi"],
  "max_duration": 3600,
  "daily_upload_limit": 10
}
```

#### `GET /glass/timelines`
Get all timelines.

**Query Parameters:**
- `limit`: Number of timelines (default: 20)
- `date`: Filter by date (dd-mm format)

**Response:**
```json
{
  "timelines": [
    {
      "id": "timeline_456",
      "date": "18-01-2025",
      "status": "completed",
      "duration": 1800,
      "context_chunks": 45
    }
  ]
}
```

#### `GET /glass/status/{timeline_id}`
Get timeline processing status.

**Path Parameters:**
- `timeline_id`: Timeline identifier

**Response:**
```json
{
  "timeline_id": "timeline_456",
  "status": "processing",
  "progress": 0.75,
  "stages": {
    "video_ingestion": "completed",
    "audio_extraction": "completed",
    "speech_to_text": "processing",
    "context_generation": "pending"
  }
}
```

#### `GET /glass/context/{timeline_id}`
Get timeline context data.

**Query Parameters:**
- `start_time`: Start time in seconds
- `end_time`: End time in seconds
- `limit`: Number of context chunks

#### `GET /glass/report/{timeline_id}`
Get daily report for timeline.

#### `PUT /glass/report/{timeline_id}`
Update daily report.

**Request Body:**
```json
{
  "title": "Updated Report Title",
  "content": "Updated report content",
  "highlights": ["highlight1", "highlight2"]
}
```

#### `POST /glass/report/{timeline_id}/generate`
Regenerate daily report.

**Request Body:**
```json
{
  "report_type": "standard",
  "include_visual_analysis": true,
  "language": "en"
}
```

---

## Web Interface Routes

### OpenContext Web UI

- `GET /` - Root path, redirects to `/contexts`
- `GET /contexts` - Context list page
- `GET /vector_search` - Vector search page
- `GET /debug` - Debug page
- `GET /chat` - AI chat interface (redirects to advanced chat)
- `GET /advanced_chat` - Advanced AI chat interface (redirects to vault)
- `GET /files/{file_path:path}` - File serving
- `GET /monitoring` - Monitoring page
- `GET /assistant` - Smart assistant page

### Vault Pages

- `GET /vaults` - Vault workspace homepage
- `GET /vaults/editor` - Smart note editor page

### Glass Web UI

- `GET /glass` - Glass dashboard homepage
- `GET /glass/` - Glass dashboard homepage (alias)

---

## CLI Commands

### OpenContext CLI

```bash
# Start OpenContext server
opencontext start --port 8000 --config config/config.yaml --no-capture

# Generate Glass timeline report
opencontext glass report --timeline-id <timeline> --lookback-minutes 120 --output persist/reports/<timeline>.md

# Start Glass video processing
opencontext glass start <dd-mm> --config config/config.yaml
```

### Glass CLI

```bash
# Process video for specific date
glass start <dd-mm> --config config/config.yaml
```

---

## Error Handling

All APIs return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "date",
      "reason": "Invalid date format. Use dd-mm format."
    }
  },
  "timestamp": "2025-01-18T10:00:00Z"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input parameters
- `NOT_FOUND`: Resource not found
- `PERMISSION_DENIED`: Insufficient permissions
- `PROCESSING_ERROR`: Background processing failed
- `EXTERNAL_API_ERROR`: External service error
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## Rate Limiting

- **Upload Endpoints**: 10 uploads per hour per user
- **Chat/Completion**: 100 requests per minute per user
- **Search Endpoints**: 1000 requests per hour per user
- **Debug Endpoints**: No rate limiting (development only)

---

## WebSocket Support

Real-time updates available via WebSocket connections:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/events');

// Listen for events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

**Supported Event Types:**
- `timeline_updated`
- `context_processed`
- `report_generated`
- `system_status`

---

## Development Tools

### OpenAPI Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Debug Endpoints
All `/api/debug/*` endpoints are available for development and troubleshooting. These provide insights into:
- Data generation processes
- System performance metrics
- Content generation prompts
- Processing pipelines

---

## Configuration

API behavior can be configured via `config/config.yaml`:

```yaml
# Server configuration
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

# API settings
api:
  rate_limiting:
    enabled: true
    requests_per_minute: 100

  upload:
    max_file_size: 500MB
    allowed_formats: ["mp4", "mov", "avi"]

# Processing settings
processing:
  batch_size: 32
  max_concurrent_jobs: 4
```

---

## Integration Examples

### Upload and Process Video

```python
import requests

# Upload video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/glass/upload',
        files={'file': f},
        data={'date': '18-01-2025'}
    )

timeline_id = response.json()['timeline_id']

# Check processing status
status = requests.get(f'http://localhost:8000/glass/status/{timeline_id}')
print(status.json())

# Get generated report
report = requests.get(f'http://localhost:8000/glass/report/{timeline_id}')
print(report.json()['content'])
```

### Vector Search

```python
import requests

response = requests.post(
    'http://localhost:8000/api/vector_search',
    json={
        'query': 'meeting notes about project',
        'limit': 10,
        'filters': {
            'context_type': 'document',
            'date_range': 'last_7_days'
        }
    }
)

results = response.json()['data']
for result in results:
    print(f"Score: {result['score']}, Content: {result['content'][:100]}...")
```

---

## Security Considerations

1. **Authentication**: All endpoints except health checks require authentication
2. **File Upload**: Files are validated for type and size before processing
3. **Rate Limiting**: Implemented to prevent abuse
4. **Input Validation**: All inputs are validated using Pydantic models
5. **CORS**: Configured for development, adjust for production
6. **Local Processing**: All processing happens locally, no external data transmission

---

## Support

For API issues or questions:
- Check the debug endpoints at `/api/debug/*`
- Review system monitoring at `/api/monitoring/*`
- Consult the application logs
- Check the health status at `/api/health`

---

*This documentation covers all available API endpoints in MineContext Glass v1.0.0. For the most up-to-date information, refer to the live OpenAPI documentation at `/docs`.*