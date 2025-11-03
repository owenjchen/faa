# Frontend Setup and Configuration Guide

Complete guide for setting up and running the FAA Next.js frontend that connects to the FastAPI backend.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Client Usage](#api-client-usage)
- [WebSocket Integration](#websocket-integration)
- [React Hooks Reference](#react-hooks-reference)
- [Component Examples](#component-examples)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

### Required Software

- **Node.js 18+** - JavaScript runtime
- **npm 9+** or **yarn 1.22+** or **pnpm 8+** - Package manager
- **Backend API** - FastAPI server running on http://localhost:8000

### Check Prerequisites

```bash
# Check Node.js version
node --version  # Should be v18.0.0 or higher

# Check npm version
npm --version   # Should be 9.0.0 or higher

# Verify backend is running
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.1.0","environment":"development"}
```

## Installation

### Step 1: Install Dependencies

```bash
cd frontend

# Using npm (default)
npm install

# Or using yarn
yarn install

# Or using pnpm
pnpm install
```

**Installation time**: ~2-3 minutes for first install

### Step 2: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env.local

# Edit .env.local with your settings
nano .env.local  # or use your preferred editor
```

**Required environment variables**:

```bash
# API Endpoints
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

**Important Notes**:
- Variables must start with `NEXT_PUBLIC_` to be accessible in the browser
- `.env.local` is git-ignored and safe for local secrets
- Restart dev server after changing environment variables

### Step 3: Verify Installation

```bash
# Check for syntax errors
npm run lint

# Check TypeScript compilation
npx tsc --noEmit
```

## Configuration

### Backend CORS Setup

The backend must allow requests from the frontend origin.

**File**: `backend/app/config.py`

```python
# Update CORS_ORIGINS setting
CORS_ORIGINS = [
    "http://localhost:3000",      # Next.js dev server
    "http://127.0.0.1:3000",      # Alternative localhost
    "https://your-domain.com",    # Production URL (when deployed)
]
```

**After updating**: Restart the backend server

```bash
cd backend
uvicorn app.main:app --reload
```

### API Client Configuration

The API client is pre-configured in `frontend/src/lib/api.ts` with:

- **Base URL**: From `NEXT_PUBLIC_API_URL` environment variable
- **Timeout**: 30 seconds (configurable)
- **Authentication**: Bearer token from localStorage
- **Error Handling**: Automatic 401 redirect to login

**To customize**:

```typescript
// frontend/src/lib/api.ts

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_URL,
    timeout: 30000,  // Change timeout here
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Modify interceptors as needed
  return client;
};
```

### WebSocket Configuration

The WebSocket client is configured in `frontend/src/lib/websocket.ts`:

- **URL**: From `NEXT_PUBLIC_WS_URL` environment variable
- **Transports**: WebSocket (primary), polling (fallback)
- **Reconnection**: Automatic with exponential backoff
- **Max Reconnection Attempts**: 5

**To customize**:

```typescript
// frontend/src/lib/websocket.ts

this.socket = io(`${WS_URL}/api/v1/ws/conversations/${conversationId}`, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,        // Change initial delay
  reconnectionAttempts: 5,        // Change max attempts
});
```

## Running the Application

### Development Mode

```bash
cd frontend

# Start development server
npm run dev

# Server starts at http://localhost:3000
```

**Features in development mode**:
- Hot reload on file changes
- Detailed error messages
- React DevTools integration
- Source maps for debugging

### Production Build

```bash
# Create optimized production build
npm run build

# Start production server
npm start
```

### Custom Port

```bash
# Run on different port
PORT=3001 npm run dev
```

### Opening in Browser

Once the server is running, open:
- **Local**: http://localhost:3000
- **Network**: http://192.168.x.x:3000 (shown in terminal)

## API Client Usage

### Basic REST API Calls

```typescript
import { apiClient } from '@/lib/api';

// Example: Create a conversation
async function createNewConversation() {
  try {
    const conversation = await apiClient.createConversation({
      rep_id: 'rep_001',
      customer_id: 'cust_12345',
      channel: 'chat',
      metadata: {
        department: 'customer_service',
        priority: 'normal'
      }
    });

    console.log('Conversation created:', conversation.id);
    return conversation;
  } catch (error) {
    console.error('Failed to create conversation:', error);
    throw error;
  }
}

// Example: Add a message
async function addCustomerMessage(conversationId: string, content: string) {
  try {
    const message = await apiClient.addMessage(conversationId, {
      role: 'customer',
      content: content
    });

    console.log('Message added:', message.id);
    return message;
  } catch (error) {
    console.error('Failed to add message:', error);
    throw error;
  }
}

// Example: Trigger workflow
async function triggerAIAssistance(conversationId: string) {
  try {
    const result = await apiClient.triggerWorkflow(conversationId, {
      rep_id: 'rep_001',
      force: false  // Set to true to bypass trigger detection
    });

    console.log('Workflow triggered:', result);
    return result;
  } catch (error) {
    console.error('Failed to trigger workflow:', error);
    throw error;
  }
}

// Example: Get resolutions
async function fetchResolutions(conversationId: string) {
  try {
    const resolutions = await apiClient.getResolutionsByConversation(conversationId);

    console.log(`Found ${resolutions.length} resolutions`);
    return resolutions;
  } catch (error) {
    console.error('Failed to fetch resolutions:', error);
    throw error;
  }
}

// Example: Approve resolution
async function approveAIResponse(resolutionId: string) {
  try {
    const result = await apiClient.approveResolution(resolutionId, {
      rep_id: 'rep_001',
      action: 'approve',
      feedback: 'Looks good!'
    });

    console.log('Resolution approved:', result);
    return result;
  } catch (error) {
    console.error('Failed to approve resolution:', error);
    throw error;
  }
}
```

### Complete Workflow Example

```typescript
import { apiClient } from '@/lib/api';

async function completeConversationWorkflow() {
  // 1. Create conversation
  const conversation = await apiClient.createConversation({
    rep_id: 'rep_001',
    customer_id: 'cust_789',
    channel: 'chat'
  });

  console.log('Created conversation:', conversation.id);

  // 2. Add customer message
  await apiClient.addMessage(conversation.id, {
    role: 'customer',
    content: 'How do I reset my 401k password?'
  });

  // 3. Add rep trigger message
  await apiClient.addMessage(conversation.id, {
    role: 'rep',
    content: 'Let me check that for you.'
  });

  // 4. Trigger AI workflow
  const triggerResult = await apiClient.triggerWorkflow(conversation.id, {
    rep_id: 'rep_001',
    force: false
  });

  console.log('Workflow status:', triggerResult.status);

  // 5. Wait for workflow completion (use WebSocket in production)
  await new Promise(resolve => setTimeout(resolve, 5000));

  // 6. Get resolutions
  const resolutions = await apiClient.getResolutionsByConversation(conversation.id);

  if (resolutions.length > 0) {
    const resolution = resolutions[0];
    console.log('Resolution:', resolution.resolution_text);
    console.log('Evaluation scores:', resolution.evaluation_scores);

    // 7. Approve if evaluation passed
    if (resolution.status === 'pending_review') {
      await apiClient.approveResolution(resolution.id, {
        rep_id: 'rep_001',
        action: 'approve'
      });

      console.log('Resolution approved and ready to send to customer');
    }
  }

  // 8. Mark conversation as completed
  await apiClient.updateConversationStatus(conversation.id, 'completed');
}
```

## WebSocket Integration

### Using the WebSocket Hook

```typescript
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useState } from 'react';

function LiveWorkflowMonitor({ conversationId }: { conversationId: string }) {
  const [workflowStatus, setWorkflowStatus] = useState('idle');
  const [progress, setProgress] = useState<string[]>([]);

  useWebSocket({
    conversationId,
    autoConnect: true,
    events: [
      'workflow_started',
      'query_optimized',
      'search_complete',
      'resolution_generated',
      'evaluation_complete',
      'workflow_complete',
      'workflow_failed'
    ],
    onConnected: (data) => {
      console.log('WebSocket connected:', data);
      setProgress(prev => [...prev, 'Connected to live updates']);
    },
    onWorkflowStarted: (data) => {
      setWorkflowStatus('processing');
      setProgress(prev => [...prev, '✓ Workflow started']);
    },
    onQueryOptimized: (data) => {
      setProgress(prev => [...prev, `✓ Query optimized: ${data.data?.query || ''}`]);
    },
    onSearchComplete: (data) => {
      setProgress(prev => [...prev, `✓ Search complete: ${data.data?.results_count || 0} results`]);
    },
    onResolutionGenerated: (data) => {
      setProgress(prev => [...prev, '✓ AI resolution generated']);
    },
    onEvaluationComplete: (data) => {
      const passed = data.data?.evaluation_passed;
      setProgress(prev => [...prev, `✓ Evaluation ${passed ? 'PASSED' : 'FAILED'}`]);
    },
    onWorkflowComplete: (data) => {
      setWorkflowStatus('complete');
      setProgress(prev => [...prev, '✓ Workflow complete!']);
    },
    onWorkflowFailed: (data) => {
      setWorkflowStatus('failed');
      setProgress(prev => [...prev, `✗ Workflow failed: ${data.data?.error || 'Unknown error'}`]);
    }
  });

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-2">
        Workflow Status: <span className="text-blue-600">{workflowStatus}</span>
      </h3>

      <div className="space-y-1">
        {progress.map((step, idx) => (
          <div key={idx} className="text-sm text-gray-700">
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Manual WebSocket Control

```typescript
import { wsClient } from '@/lib/websocket';

// Connect to conversation
wsClient.connect('conv_12345');

// Subscribe to specific events
wsClient.subscribe([
  'workflow_started',
  'resolution_generated',
  'workflow_complete'
]);

// Listen to resolution generation
wsClient.on('resolution_generated', (data) => {
  console.log('New resolution:', data);
  // Update UI with new resolution
});

// Disconnect when done
wsClient.disconnect();
```

## React Hooks Reference

### useConversation

Manages conversation data and operations.

```typescript
import { useConversation } from '@/hooks/useConversation';

function ConversationView({ conversationId }: { conversationId: string }) {
  const {
    conversation,
    messages,
    isLoading,
    error,
    addMessage,
    isAddingMessage,
    updateStatus,
    refetch
  } = useConversation({
    conversationId,
    autoRefresh: true,      // Auto-refresh every 5 seconds
    refreshInterval: 5000
  });

  if (isLoading) return <div>Loading conversation...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Conversation {conversation?.id}</h2>
      <p>Status: {conversation?.status}</p>

      {/* Display messages */}
      <div>
        {messages.map(msg => (
          <div key={msg.id}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      {/* Add message */}
      <button
        onClick={() => addMessage({ role: 'rep', content: 'Hello!' })}
        disabled={isAddingMessage}
      >
        Send Message
      </button>

      {/* Complete conversation */}
      <button onClick={() => updateStatus('completed')}>
        Mark as Complete
      </button>
    </div>
  );
}
```

### useResolution

Manages resolution data and operations.

```typescript
import { useResolution } from '@/hooks/useResolution';

function ResolutionPanel({ conversationId }: { conversationId: string }) {
  const {
    resolutions,
    isLoading,
    approveResolution,
    isApproving,
    updateResolution,
    isUpdating
  } = useResolution({ conversationId });

  if (isLoading) return <div>Loading resolutions...</div>;

  const latestResolution = resolutions[0];

  if (!latestResolution) {
    return <div>No resolutions yet</div>;
  }

  return (
    <div>
      <h3>AI-Generated Resolution</h3>

      <div className="prose">
        {latestResolution.resolution_text}
      </div>

      <div className="mt-4">
        <h4>Evaluation Scores</h4>
        <ul>
          <li>Accuracy: {latestResolution.evaluation_scores.accuracy}/5</li>
          <li>Relevancy: {latestResolution.evaluation_scores.relevancy}/5</li>
          <li>Factual Grounding: {latestResolution.evaluation_scores.factual_grounding}/5</li>
        </ul>
      </div>

      <div className="mt-4 space-x-2">
        <button
          onClick={() => approveResolution('rep_001', 'approve')}
          disabled={isApproving}
        >
          Approve
        </button>

        <button
          onClick={() => approveResolution('rep_001', 'reject', 'Not accurate')}
          disabled={isApproving}
        >
          Reject
        </button>

        <button
          onClick={() => {
            const edited = prompt('Edit resolution:', latestResolution.resolution_text);
            if (edited) {
              updateResolution(edited, 'rep_001', 'Made it more concise');
            }
          }}
          disabled={isUpdating}
        >
          Edit
        </button>
      </div>
    </div>
  );
}
```

### useCreateConversation

Creates new conversations.

```typescript
import { useCreateConversation } from '@/hooks/useConversation';

function NewConversationButton() {
  const { createConversation, isCreating, data } = useCreateConversation();

  const handleCreate = async () => {
    const conversation = await createConversation({
      rep_id: 'rep_001',
      customer_id: 'cust_123',
      channel: 'chat'
    });

    // Redirect to conversation page
    window.location.href = `/conversations/${conversation.id}`;
  };

  return (
    <button onClick={handleCreate} disabled={isCreating}>
      {isCreating ? 'Creating...' : 'New Conversation'}
    </button>
  );
}
```

### useTriggerWorkflow

Triggers the AI workflow.

```typescript
import { useTriggerWorkflow } from '@/hooks/useConversation';

function TriggerButton({ conversationId }: { conversationId: string }) {
  const { triggerWorkflow, isTriggering } = useTriggerWorkflow(conversationId);

  const handleTrigger = async () => {
    try {
      const result = await triggerWorkflow({
        repId: 'rep_001',
        force: false
      });

      console.log('Workflow triggered:', result);
      alert('AI assistance activated!');
    } catch (error) {
      alert('Failed to trigger workflow');
    }
  };

  return (
    <button onClick={handleTrigger} disabled={isTriggering}>
      {isTriggering ? 'Processing...' : 'Get AI Assistance'}
    </button>
  );
}
```

## Component Examples

### Complete Conversation Component

```typescript
'use client';

import { useConversation, useTriggerWorkflow } from '@/hooks/useConversation';
import { useResolution } from '@/hooks/useResolution';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useState } from 'react';

export default function ConversationPage({ params }: { params: { id: string } }) {
  const conversationId = params.id;
  const [messageInput, setMessageInput] = useState('');

  // Fetch conversation data
  const {
    conversation,
    messages,
    isLoading,
    addMessage,
    isAddingMessage
  } = useConversation({ conversationId, autoRefresh: true });

  // Fetch resolutions
  const {
    resolutions,
    approveResolution,
    isApproving
  } = useResolution({ conversationId });

  // Trigger workflow
  const { triggerWorkflow, isTriggering } = useTriggerWorkflow(conversationId);

  // WebSocket for real-time updates
  useWebSocket({
    conversationId,
    autoConnect: true,
    onResolutionGenerated: (data) => {
      console.log('New resolution generated!', data);
      // Resolutions will auto-refresh due to react-query
    },
    onWorkflowComplete: (data) => {
      alert('AI assistance complete!');
    }
  });

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim()) return;

    await addMessage({
      role: 'rep',
      content: messageInput
    });

    setMessageInput('');
  };

  const handleTrigger = async () => {
    await triggerWorkflow({ repId: 'rep_001' });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-2 gap-4">
        {/* Left: Conversation */}
        <div className="border rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">
            Conversation {conversation?.id}
          </h2>

          {/* Messages */}
          <div className="space-y-2 mb-4 h-96 overflow-y-auto">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`p-2 rounded ${
                  msg.role === 'customer' ? 'bg-blue-100' : 'bg-gray-100'
                }`}
              >
                <strong className="text-sm">{msg.role}:</strong>
                <p>{msg.content}</p>
              </div>
            ))}
          </div>

          {/* Message input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 border rounded px-3 py-2"
            />
            <button
              type="submit"
              disabled={isAddingMessage}
              className="bg-blue-500 text-white px-4 py-2 rounded"
            >
              Send
            </button>
          </form>

          {/* Trigger button */}
          <button
            onClick={handleTrigger}
            disabled={isTriggering}
            className="mt-4 bg-green-500 text-white px-4 py-2 rounded w-full"
          >
            {isTriggering ? 'Processing...' : 'Get AI Assistance'}
          </button>
        </div>

        {/* Right: Resolutions */}
        <div className="border rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">AI Resolutions</h2>

          {resolutions.length === 0 ? (
            <p className="text-gray-500">No resolutions yet</p>
          ) : (
            <div className="space-y-4">
              {resolutions.map(resolution => (
                <div key={resolution.id} className="border-b pb-4">
                  <div className="prose prose-sm mb-2">
                    {resolution.resolution_text}
                  </div>

                  <div className="text-sm text-gray-600 mb-2">
                    Scores: Accuracy {resolution.evaluation_scores.accuracy}/5,
                    Relevancy {resolution.evaluation_scores.relevancy}/5
                  </div>

                  {resolution.status === 'pending_review' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => approveResolution('rep_001', 'approve')}
                        disabled={isApproving}
                        className="bg-green-500 text-white px-3 py-1 rounded text-sm"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => approveResolution('rep_001', 'reject')}
                        disabled={isApproving}
                        className="bg-red-500 text-white px-3 py-1 rounded text-sm"
                      >
                        Reject
                      </button>
                    </div>
                  )}

                  {resolution.status === 'approved' && (
                    <span className="text-green-600 font-semibold">✓ Approved</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## Troubleshooting

### CORS Errors

**Symptoms**:
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solutions**:

1. **Update backend CORS settings** (`backend/app/config.py`):
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

2. **Restart backend**:
```bash
cd backend
uvicorn app.main:app --reload
```

3. **Clear browser cache** and refresh

4. **Verify CORS headers** in browser DevTools → Network tab:
   - Look for `Access-Control-Allow-Origin` header in response

### WebSocket Connection Failures

**Symptoms**:
```
WebSocket connection to 'ws://localhost:8000' failed
```

**Solutions**:

1. **Verify backend is running**:
```bash
curl http://localhost:8000/health
```

2. **Check WebSocket URL** in `.env.local`:
```bash
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

3. **Test WebSocket endpoint** with a tool like [Postman](https://www.postman.com/) or [wscat](https://github.com/websockets/wscat):
```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/ws/conversations/test123
```

4. **Check firewall/antivirus** - may block WebSocket connections

5. **Review backend logs** for WebSocket errors

### API Request Timeouts

**Symptoms**:
```
Error: timeout of 30000ms exceeded
```

**Solutions**:

1. **Increase timeout** in `frontend/src/lib/api.ts`:
```typescript
const client = axios.create({
  baseURL: API_URL,
  timeout: 60000, // Increase to 60 seconds
});
```

2. **Check backend performance** - workflow may take longer than expected

3. **Optimize backend** - add caching, improve search performance

4. **Use WebSocket for long-running operations** instead of polling

### Environment Variables Not Loading

**Symptoms**:
```
API URL is undefined
process.env.NEXT_PUBLIC_API_URL is undefined
```

**Solutions**:

1. **Ensure file is named `.env.local`** (not `.env` or `.env.example`)

2. **Restart dev server** after changing `.env.local`:
```bash
# Stop server (Ctrl+C)
npm run dev  # Start again
```

3. **Verify variable names** start with `NEXT_PUBLIC_`:
```bash
# Correct
NEXT_PUBLIC_API_URL=http://localhost:8000

# Wrong (won't work in browser)
API_URL=http://localhost:8000
```

4. **Check for typos** in variable names

5. **Print environment variables** for debugging:
```typescript
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL);
```

### Type Errors After Installation

**Symptoms**:
```
Type error: Cannot find module '@/lib/api' or its corresponding type declarations
```

**Solutions**:

1. **Clear Next.js cache**:
```bash
rm -rf .next
```

2. **Reinstall dependencies**:
```bash
rm -rf node_modules package-lock.json
npm install
```

3. **Check TypeScript paths** in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

4. **Restart TypeScript server** in VSCode:
   - Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
   - Type "TypeScript: Restart TS Server"

### React Query DevTools Not Showing

**Symptoms**: DevTools panel not appearing in development

**Solutions**:

1. **Install React Query DevTools** (if not already):
```bash
npm install @tanstack/react-query-devtools
```

2. **Add to root layout** (`src/app/layout.tsx`):
```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

## Production Deployment

### Build Optimization

```bash
# Create production build
npm run build

# Analyze bundle size
npm run build -- --profile

# Start production server locally
npm start
```

### Environment Variables for Production

Create `.env.production` or set environment variables in your deployment platform:

```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Deployment Platforms

#### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_WS_URL production
```

#### Docker

```bash
# Build image
docker build -t faa-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api:8000 \
  -e NEXT_PUBLIC_WS_URL=ws://api:8000 \
  faa-frontend
```

#### AWS Amplify

1. Connect GitHub repository
2. Set build settings:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```
3. Add environment variables in Amplify Console

### Performance Optimization

1. **Enable compression**:
```javascript
// next.config.js
module.exports = {
  compress: true,
};
```

2. **Optimize images**:
```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  width={200}
  height={50}
  alt="Logo"
  priority
/>
```

3. **Code splitting**:
```typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
  loading: () => <p>Loading...</p>,
});
```

4. **API response caching**:
```typescript
const { data } = useQuery({
  queryKey: ['conversation', id],
  queryFn: () => apiClient.getConversation(id),
  staleTime: 60000, // Cache for 1 minute
});
```

## Resources

- **Next.js Documentation**: https://nextjs.org/docs
- **React Query**: https://tanstack.com/query/latest
- **shadcn/ui**: https://ui.shadcn.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Socket.IO**: https://socket.io/docs/v4/
- **Axios**: https://axios-http.com/docs/intro
- **FAA Backend API**: http://localhost:8000/api/docs

## Support

For frontend issues:
- Check browser console for errors
- Review backend API logs
- Test endpoints in Swagger UI: http://localhost:8000/api/docs
- Check Network tab in DevTools for failed requests

---

**Ready to start building!** Follow this guide to get your frontend connected to the backend and start creating the FAA user interface.
