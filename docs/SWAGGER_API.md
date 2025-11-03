# Swagger UI API Documentation

Complete guide to using the FAA API via Swagger UI.

## Accessing Swagger UI

### URLs

When running locally:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Starting the Server

```bash
cd backend
source .venv/bin/activate  # or: source venv/bin/activate
uvicorn app.main:app --reload
```

The server will start on http://localhost:8000

## Swagger UI Features

### Enhanced Configuration

The FAA API includes custom Swagger UI configuration:

```python
swagger_ui_parameters={
    "defaultModelsExpandDepth": 1,      # Expand model schemas
    "defaultModelExpandDepth": 1,        # Expand model details
    "docExpansion": "list",              # Show endpoints collapsed by tag
    "filter": True,                      # Enable endpoint search/filter
    "showExtensions": True,              # Show OpenAPI extensions
    "showCommonExtensions": True,        # Show common extensions
    "syntaxHighlight.theme": "monokai",  # Dark syntax theme
    "tryItOutEnabled": True,             # Enable "Try it out" by default
}
```

### Custom Styling

- **Theme**: Monokai syntax highlighting for better code readability
- **Filtering**: Search bar to quickly find endpoints
- **Documentation**: Markdown-formatted descriptions with examples

## API Structure

### Tags (Endpoint Groups)

#### 1. **health**
System health and status endpoints

#### 2. **conversations**
Manage customer-rep conversations and messages

**Endpoints:**
- `POST /api/v1/conversations` - Create new conversation
- `GET /api/v1/conversations/{id}` - Get conversation details
- `POST /api/v1/conversations/{id}/messages` - Add message
- `GET /api/v1/conversations/{id}/messages` - List messages
- `POST /api/v1/conversations/{id}/trigger` - Manually trigger workflow
- `PATCH /api/v1/conversations/{id}/status` - Update status
- `DELETE /api/v1/conversations/{id}` - Delete conversation

#### 3. **resolutions**
AI-generated resolutions with citations

**Endpoints:**
- `GET /api/v1/resolutions/{id}` - Get resolution
- `GET /api/v1/resolutions/conversation/{id}` - Get resolutions by conversation
- `PATCH /api/v1/resolutions/{id}` - Update resolution text
- `POST /api/v1/resolutions/{id}/approve` - Approve/reject resolution
- `POST /api/v1/resolutions/{id}/feedback` - Submit feedback

#### 4. **evaluations**
Quality metrics and evaluation scores

**Endpoints:**
- `GET /api/v1/evaluations/metrics` - Get aggregated metrics
- `GET /api/v1/evaluations/scores/{id}` - Get resolution scores
- `GET /api/v1/evaluations/failures` - Get failed evaluations

#### 5. **websocket**
Real-time WebSocket connections

**Endpoint:**
- `WS /api/v1/ws/conversations/{id}` - WebSocket connection

## Using Swagger UI

### 1. Exploring Endpoints

**Step 1**: Open http://localhost:8000/api/docs

**Step 2**: Browse endpoints grouped by tags:
- Click on a tag (e.g., "conversations") to expand all endpoints in that group
- Each endpoint shows:
  - HTTP method (GET, POST, PATCH, DELETE)
  - Path with parameters
  - Summary description
  - Detailed documentation

**Step 3**: Use the search/filter box to quickly find endpoints

### 2. Testing Endpoints

#### Example: Create a Conversation

**Step 1**: Click on `POST /api/v1/conversations`

**Step 2**: Click "Try it out" button (top right of the endpoint)

**Step 3**: Edit the request body JSON:

```json
{
  "rep_id": "rep_12345",
  "customer_id": "cust_67890",
  "channel": "chat",
  "metadata": {
    "department": "customer_service",
    "priority": "normal"
  }
}
```

**Step 4**: Click "Execute"

**Step 5**: View the response:
- Status code: 201 Created
- Response body with conversation ID
- Response headers
- cURL command for replication

#### Example: Add a Message

**Step 1**: Click on `POST /api/v1/conversations/{conversation_id}/messages`

**Step 2**: Click "Try it out"

**Step 3**: Enter the conversation_id from previous step

**Step 4**: Edit request body:

```json
{
  "role": "customer",
  "content": "How do I reset my 401k password?"
}
```

**Step 5**: Click "Execute"

#### Example: Trigger Workflow

**Step 1**: Add a rep message with trigger phrase:

```json
{
  "role": "rep",
  "content": "Let me check that for you."
}
```

**Step 2**: Click on `POST /api/v1/conversations/{conversation_id}/trigger`

**Step 3**: Enter the conversation_id

**Step 4**: Set request body:

```json
{
  "rep_id": "rep_12345",
  "force": false
}
```

**Step 5**: Execute - the workflow will start processing

### 3. Viewing Responses

#### Success Response

```json
{
  "id": "conv_20241103120000",
  "rep_id": "rep_12345",
  "customer_id": "cust_67890",
  "channel": "chat",
  "status": "active",
  "started_at": "2024-11-03T12:00:00Z",
  "messages": []
}
```

**Status Code**: 201 Created

#### Error Response

```json
{
  "error": "Not Found",
  "message": "Conversation conv_123 not found"
}
```

**Status Code**: 404 Not Found

### 4. Understanding Schemas

**Step 1**: Scroll to "Schemas" section at the bottom

**Step 2**: Click on any schema to expand:
- `ConversationCreate` - Request body for creating conversations
- `ConversationResponse` - Response format for conversations
- `MessageCreate` - Request body for messages
- `ResolutionResponse` - Response format for resolutions
- etc.

**Step 3**: View:
- Field names and types
- Required vs optional fields
- Validation rules
- Example values

### 5. Using Filters

**Filter by tag**: Click on tag names to show only those endpoints

**Search**: Use the filter box to search for:
- Endpoint paths: `/conversations`
- Methods: `POST`
- Keywords: `message`, `resolution`

## Advanced Features

### Authentication Testing

Once authentication is implemented:

**Step 1**: Click "Authorize" button (top right)

**Step 2**: Enter JWT token:
```
Bearer eyJhbGciOiJIUzI1NiIs...
```

**Step 3**: Click "Authorize"

**Step 4**: All subsequent requests will include the token

### Copying as cURL

Each executed request shows the equivalent cURL command:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/conversations' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "rep_id": "rep_12345",
  "customer_id": "cust_67890",
  "channel": "chat"
}'
```

Copy this to:
- Test from command line
- Share with team members
- Include in scripts

### Downloading OpenAPI Spec

**Step 1**: Visit http://localhost:8000/api/v1/openapi.json

**Step 2**: Save JSON file

**Use cases:**
- Import into Postman
- Generate client SDKs
- API documentation tools
- Contract testing

## Complete Workflow Example

### Scenario: Rep helping customer reset password

```bash
# 1. Start server
uvicorn app.main:app --reload
```

#### Step 1: Create Conversation

**Request**: `POST /api/v1/conversations`

```json
{
  "rep_id": "rep_001",
  "customer_id": "cust_789",
  "channel": "chat"
}
```

**Response**:
```json
{
  "id": "conv_20241103",
  "status": "active",
  ...
}
```

#### Step 2: Add Customer Message

**Request**: `POST /api/v1/conversations/conv_20241103/messages`

```json
{
  "role": "customer",
  "content": "I forgot my 401k password"
}
```

#### Step 3: Add Rep Trigger Message

**Request**: `POST /api/v1/conversations/conv_20241103/messages`

```json
{
  "role": "rep",
  "content": "Let me check that for you"
}
```

#### Step 4: Trigger Workflow (Auto or Manual)

**Request**: `POST /api/v1/conversations/conv_20241103/trigger`

```json
{
  "rep_id": "rep_001",
  "force": false
}
```

#### Step 5: Monitor via WebSocket (Optional)

Connect to: `ws://localhost:8000/api/v1/ws/conversations/conv_20241103`

Receive real-time events:
```json
{
  "event": "workflow_started",
  "conversation_id": "conv_20241103"
}
```

#### Step 6: Check Resolution

**Request**: `GET /api/v1/resolutions/conversation/conv_20241103`

**Response**:
```json
[
  {
    "id": "res_123",
    "resolution_text": "To reset your 401k password...",
    "citations": [...],
    "evaluation_scores": {
      "accuracy": 5,
      "relevancy": 5,
      "factual_grounding": 4
    },
    "status": "pending_review"
  }
]
```

#### Step 7: Rep Approves

**Request**: `POST /api/v1/resolutions/res_123/approve`

```json
{
  "rep_id": "rep_001",
  "action": "approve"
}
```

## Troubleshooting

### Swagger UI Not Loading

**Check:**
1. Server is running: `curl http://localhost:8000/health`
2. Correct URL: http://localhost:8000/api/docs
3. Browser console for errors

**Solution:**
```bash
# Restart server
uvicorn app.main:app --reload --log-level debug
```

### 422 Validation Errors

**Problem**: Request body doesn't match schema

**Solution**:
1. Check "Schemas" section for correct format
2. Ensure all required fields are present
3. Verify data types match (string, int, etc.)

**Example Fix**:
```json
// Wrong
{
  "rep_id": 12345,  // Should be string
  "channel": "phone"  // Invalid, must be "voice", "chat", or "email"
}

// Correct
{
  "rep_id": "rep_12345",
  "channel": "chat"
}
```

### CORS Errors

**Problem**: Accessing from different origin

**Solution**: Add origin to `CORS_ORIGINS` in settings:
```python
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
```

### Rate Limiting

**Problem**: Too many requests

**Response**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

**Solution**: Wait for retry_after seconds or increase `RATE_LIMIT_PER_MINUTE`

## ReDoc Alternative

For a different documentation view:

**URL**: http://localhost:8000/api/redoc

**Features**:
- Cleaner, more readable layout
- Better for reading documentation
- Three-column layout
- Searchable
- Print-friendly

**When to use**:
- Reading documentation
- Sharing with stakeholders
- Documentation reviews

**Note**: ReDoc is read-only (no "Try it out" feature)

## Tips & Best Practices

### 1. Save Example Requests

Swagger UI doesn't save your test data. Keep a text file with example requests:

```json
// examples.json
{
  "create_conversation": {
    "rep_id": "rep_001",
    "channel": "chat"
  },
  "add_message": {
    "role": "customer",
    "content": "Test message"
  }
}
```

### 2. Use Meaningful IDs

Use descriptive IDs for testing:
- `rep_test_001` instead of `rep_1`
- `conv_password_reset` instead of `conv_123`

### 3. Test Error Cases

Try invalid inputs to see error responses:
- Missing required fields
- Invalid enum values
- Wrong data types

### 4. Check Response Times

Swagger UI shows response times:
- Look for slow endpoints
- Identify performance issues
- Monitor timeout settings

### 5. Export to Postman

**Step 1**: Download OpenAPI JSON

**Step 2**: In Postman, go to Import → Upload Files

**Step 3**: Select the openapi.json file

**Step 4**: All endpoints imported with examples!

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Swagger UI Docs**: https://swagger.io/docs/open-source-tools/swagger-ui/
- **OpenAPI Spec**: https://spec.openapis.org/oas/latest.html
- **ReDoc**: https://redocly.com/redoc

## Support

For issues with the API or Swagger UI:
- Check server logs: `docker-compose logs backend`
- Review FastAPI logs: Look for `ERROR` level messages
- Test with cURL to isolate UI issues
- Contact #faa-support on Slack

---

**Happy API Testing!** 🚀
