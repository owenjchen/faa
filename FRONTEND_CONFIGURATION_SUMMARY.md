# Frontend Configuration Summary

Complete summary of the frontend setup for connecting to the FAA backend API.

## What Was Created

### Core Library Files

1. **[frontend/src/lib/api.ts](frontend/src/lib/api.ts)** - REST API Client
   - TypeScript interfaces for all API entities (Conversation, Message, Resolution, Citation, EvaluationScores)
   - Axios-based client with interceptors for auth and error handling
   - All backend endpoint methods (conversations, resolutions, evaluations)
   - Automatic token management from localStorage
   - 401 redirect to login page

2. **[frontend/src/lib/websocket.ts](frontend/src/lib/websocket.ts)** - WebSocket Client
   - Socket.IO client for real-time updates
   - Event-driven architecture with typed events
   - Automatic reconnection with exponential backoff
   - Subscribe/unsubscribe to specific event types
   - Connection lifecycle management

### React Hooks

3. **[frontend/src/hooks/useConversation.ts](frontend/src/hooks/useConversation.ts)** - Conversation Management
   - `useConversation()` - Fetch and manage conversation data
   - `useCreateConversation()` - Create new conversations
   - `useTriggerWorkflow()` - Trigger AI workflow
   - React Query integration with auto-refresh
   - Mutations for adding messages, updating status, deleting conversations

4. **[frontend/src/hooks/useResolution.ts](frontend/src/hooks/useResolution.ts)** - Resolution Management
   - `useResolution()` - Fetch and manage resolution data
   - `useResolutionScores()` - Get evaluation scores
   - Mutations for updating, approving, and providing feedback on resolutions
   - React Query integration with cache management

5. **[frontend/src/hooks/useWebSocket.ts](frontend/src/hooks/useWebSocket.ts)** - WebSocket Integration
   - `useWebSocket()` - Manage WebSocket connection lifecycle
   - `useWebSocketEvent()` - Listen to specific events
   - Auto-connect/disconnect based on conversationId
   - Event handler registration with cleanup

### Configuration Files

6. **[frontend/.env.example](frontend/.env.example)** - Environment Template
   - API URL configuration
   - WebSocket URL configuration
   - Environment settings
   - Feature flags

7. **[frontend/README.md](frontend/README.md)** - Quick Start Guide
   - Installation instructions
   - Configuration guide
   - API client usage examples
   - WebSocket integration examples
   - Troubleshooting section
   - Production deployment guide

### Documentation

8. **[docs/FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md)** - Comprehensive Setup Guide (60+ pages)
   - Detailed prerequisites and installation
   - Complete configuration instructions
   - API client usage with examples
   - WebSocket integration guide
   - React hooks reference with examples
   - Complete component examples
   - Extensive troubleshooting section
   - Production deployment guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env.local

# Edit with your settings
nano .env.local
```

**Required variables**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### 3. Configure Backend CORS

Update `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

Restart backend:
```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Run Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at http://localhost:3000

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Components (React)                                             │
│  ├── Chat Interface                                             │
│  ├── Resolution Display                                         │
│  └── Dashboard                                                  │
│                                                                 │
│  Custom Hooks                                                   │
│  ├── useConversation() ─────> React Query ──> API Client       │
│  ├── useResolution()                                            │
│  └── useWebSocket() ────────> WebSocket Client                 │
│                                                                 │
│  Core Libraries                                                 │
│  ├── api.ts (REST)           HTTP/HTTPS                         │
│  └── websocket.ts (Real-time) WebSocket                         │
│                                                                 │
└─────────────────┬───────────────────────┬───────────────────────┘
                  │                       │
                  │ REST API              │ WebSocket
                  │ (Axios)               │ (Socket.IO)
                  │                       │
┌─────────────────▼───────────────────────▼───────────────────────┐
│                      Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API Endpoints                WebSocket Endpoints               │
│  ├── /api/v1/conversations   ├── /api/v1/ws/conversations/{id} │
│  ├── /api/v1/resolutions     └── Events:                        │
│  └── /api/v1/evaluations         ├── workflow_started          │
│                                   ├── resolution_generated      │
│  LangGraph Workflow                └── workflow_complete         │
│  └── Agent Nodes                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Type-Safe API Client

All API calls are fully typed with TypeScript:

```typescript
import { apiClient } from '@/lib/api';

// Type-safe conversation creation
const conversation = await apiClient.createConversation({
  rep_id: 'rep_001',        // Required, string
  customer_id: 'cust_123',  // Optional, string
  channel: 'chat'           // Required, 'voice' | 'chat' | 'email'
});

// TypeScript knows the response shape
console.log(conversation.id);        // string
console.log(conversation.status);    // 'active' | 'completed' | 'escalated'
console.log(conversation.messages);  // Message[]
```

### 2. Real-Time Updates

WebSocket integration provides instant updates:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

useWebSocket({
  conversationId,
  onResolutionGenerated: (data) => {
    // Triggered instantly when backend generates resolution
    console.log('New resolution:', data);
  },
  onWorkflowComplete: (data) => {
    // Workflow finished
    alert('AI assistance complete!');
  }
});
```

### 3. Automatic Cache Management

React Query handles caching and revalidation:

```typescript
const { conversation, messages } = useConversation({
  conversationId,
  autoRefresh: true,      // Auto-refresh every 5 seconds
  refreshInterval: 5000
});

// Data is automatically cached and shared across components
// Mutations automatically invalidate relevant queries
```

### 4. Authentication Ready

Built-in authentication handling:

```typescript
// API client automatically:
// 1. Retrieves token from localStorage
// 2. Adds Bearer token to requests
// 3. Redirects to /login on 401 responses

// To set token:
localStorage.setItem('auth_token', 'your_jwt_token');

// To clear token (logout):
localStorage.removeItem('auth_token');
```

### 5. Error Handling

Comprehensive error handling at all levels:

```typescript
try {
  const conversation = await apiClient.createConversation(data);
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      // Unauthorized - redirected to login
    } else if (error.response?.status === 422) {
      // Validation error
      console.log('Validation errors:', error.response.data);
    } else {
      // Other error
      console.error('API error:', error.message);
    }
  }
}
```

## Usage Examples

### Complete Conversation Flow

```typescript
'use client';

import { useConversation, useTriggerWorkflow } from '@/hooks/useConversation';
import { useResolution } from '@/hooks/useResolution';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function ConversationPage({ params }: { params: { id: string } }) {
  const conversationId = params.id;

  // Fetch data
  const { conversation, messages, addMessage } = useConversation({ conversationId });
  const { resolutions, approveResolution } = useResolution({ conversationId });
  const { triggerWorkflow, isTriggering } = useTriggerWorkflow(conversationId);

  // Real-time updates
  useWebSocket({
    conversationId,
    onResolutionGenerated: () => {
      // Resolution will auto-refresh via react-query
      console.log('New resolution available!');
    }
  });

  return (
    <div>
      {/* Chat interface */}
      {messages.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}

      {/* Trigger AI */}
      <button onClick={() => triggerWorkflow({ repId: 'rep_001' })}>
        Get AI Assistance
      </button>

      {/* Display resolutions */}
      {resolutions.map(res => (
        <div key={res.id}>
          <p>{res.resolution_text}</p>
          <button onClick={() => approveResolution('rep_001', 'approve')}>
            Approve
          </button>
        </div>
      ))}
    </div>
  );
}
```

### Standalone API Usage (Outside React)

```typescript
import { apiClient } from '@/lib/api';

async function completeWorkflow() {
  // 1. Create conversation
  const conv = await apiClient.createConversation({
    rep_id: 'rep_001',
    channel: 'chat'
  });

  // 2. Add messages
  await apiClient.addMessage(conv.id, {
    role: 'customer',
    content: 'How do I reset my password?'
  });

  await apiClient.addMessage(conv.id, {
    role: 'rep',
    content: 'Let me check that for you.'
  });

  // 3. Trigger AI
  await apiClient.triggerWorkflow(conv.id, {
    rep_id: 'rep_001'
  });

  // 4. Poll for resolutions (better: use WebSocket)
  await new Promise(resolve => setTimeout(resolve, 5000));

  // 5. Get resolutions
  const resolutions = await apiClient.getResolutionsByConversation(conv.id);

  // 6. Approve
  if (resolutions.length > 0) {
    await apiClient.approveResolution(resolutions[0].id, {
      rep_id: 'rep_001',
      action: 'approve'
    });
  }
}
```

### WebSocket-Only Usage

```typescript
import { wsClient } from '@/lib/websocket';

// Connect
wsClient.connect('conv_12345');

// Subscribe to events
wsClient.subscribe([
  'workflow_started',
  'resolution_generated',
  'workflow_complete'
]);

// Listen to events
wsClient.on('resolution_generated', (data) => {
  console.log('Resolution:', data.data);
  // Update UI
});

wsClient.on('workflow_complete', (data) => {
  console.log('Complete!');
  // Fetch final data via API
});

// Cleanup
wsClient.disconnect();
```

## API Reference

### REST Endpoints (via apiClient)

#### Conversations

```typescript
// Create
createConversation(data: CreateConversationRequest): Promise<Conversation>

// Get
getConversation(conversationId: string): Promise<Conversation>

// Messages
addMessage(conversationId: string, data: CreateMessageRequest): Promise<Message>
getMessages(conversationId: string, limit?, offset?): Promise<Message[]>

// Workflow
triggerWorkflow(conversationId: string, data: TriggerWorkflowRequest): Promise<any>

// Status
updateConversationStatus(conversationId: string, status: string): Promise<any>

// Delete
deleteConversation(conversationId: string): Promise<void>
```

#### Resolutions

```typescript
// Get
getResolution(resolutionId: string): Promise<Resolution>
getResolutionsByConversation(conversationId: string): Promise<Resolution[]>

// Update
updateResolution(resolutionId: string, editedText: string, repId: string, editReason?): Promise<Resolution>

// Approve/Reject
approveResolution(resolutionId: string, data: ApproveResolutionRequest): Promise<any>

// Feedback
submitResolutionFeedback(resolutionId: string, rating: number, feedbackText?): Promise<any>
```

#### Evaluations

```typescript
// Metrics
getEvaluationMetrics(params?: {start_date?, end_date?, rep_id?}): Promise<any>

// Scores
getResolutionScores(resolutionId: string): Promise<any>

// Failures
getFailedEvaluations(limit?, minRetries?): Promise<any>
```

### WebSocket Events

```typescript
type WebSocketEvent =
  | 'connected'
  | 'workflow_started'
  | 'query_optimized'
  | 'search_complete'
  | 'resolution_generated'
  | 'evaluation_complete'
  | 'workflow_complete'
  | 'workflow_failed'
  | 'message_added'
  | 'conversation_updated';
```

## Testing the Connection

### 1. Verify Backend

```bash
# Check health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"0.1.0","environment":"development"}
```

### 2. Verify Frontend

```bash
# Start frontend
cd frontend
npm run dev

# Should output:
# - Local: http://localhost:3000
# - ready started server on [::]:3000
```

### 3. Test API Connection

Open browser console at http://localhost:3000 and run:

```javascript
// Test REST API
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('Backend:', data));

// Or test from React component
import { apiClient } from '@/lib/api';
const data = await apiClient.healthCheck();
console.log('API:', data);
```

### 4. Test WebSocket

```javascript
import { wsClient } from '@/lib/websocket';

wsClient.connect('test_conv_123');
wsClient.on('connected', (data) => {
  console.log('WebSocket connected:', data);
});
```

## Common Issues & Solutions

### Issue: CORS Errors

**Solution**: Update backend `CORS_ORIGINS` in `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

Restart backend after changes.

### Issue: Environment Variables Not Working

**Solution**:
1. File must be named `.env.local` (not `.env`)
2. Variables must start with `NEXT_PUBLIC_`
3. Restart dev server after changes

### Issue: WebSocket Won't Connect

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_WS_URL` in `.env.local`
3. Check browser console for detailed errors
4. Test with wscat: `wscat -c ws://localhost:8000/api/v1/ws/conversations/test`

### Issue: Types Not Found

**Solution**:
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

### 1. Create UI Components

Start building the user interface:

```bash
# Install shadcn/ui components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add input
```

### 2. Build Pages

Create the main application pages:

- **Dashboard** - Overview of conversations and metrics
- **Conversation View** - Chat interface with AI assistance
- **Resolution Review** - Review and approve AI-generated responses
- **Analytics** - Evaluation metrics and performance

### 3. Add State Management

If needed, add Zustand for global state:

```typescript
// src/stores/userStore.ts
import create from 'zustand';

interface UserStore {
  repId: string;
  setRepId: (id: string) => void;
}

export const useUserStore = create<UserStore>((set) => ({
  repId: '',
  setRepId: (id) => set({ repId: id }),
}));
```

### 4. Implement Authentication

Add authentication flow:

```typescript
// src/lib/auth.ts
export async function login(username: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const { access_token } = await response.json();
  localStorage.setItem('auth_token', access_token);

  return access_token;
}

export function logout() {
  localStorage.removeItem('auth_token');
  window.location.href = '/login';
}
```

### 5. Add Testing

Set up testing framework:

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Create test files
# src/lib/__tests__/api.test.ts
# src/hooks/__tests__/useConversation.test.tsx
```

## Documentation Reference

- **Quick Start**: [frontend/README.md](frontend/README.md)
- **Complete Setup Guide**: [docs/FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md)
- **Backend API Reference**: http://localhost:8000/api/docs (when running)
- **Backend Setup**: [backend/README.md](backend/README.md)

## Summary

The frontend is now fully configured with:

✅ Type-safe REST API client
✅ Real-time WebSocket integration
✅ React hooks for easy data management
✅ Automatic caching and revalidation
✅ Authentication handling
✅ Error handling
✅ Environment configuration
✅ Comprehensive documentation

**Ready to start building the UI!**

---

**Last Updated**: 2024-11-03
**Frontend Version**: 0.1.0
**Backend Version**: 0.1.0
