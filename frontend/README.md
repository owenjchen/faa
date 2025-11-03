# FAA Frontend

Modern Next.js 14 frontend for the Fidelity Agent Assistant (FAA) system.

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running at http://localhost:8000 (see [backend README](../backend/README.md))

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

**Important**: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

### Backend Connection

The frontend connects to the FastAPI backend via:

1. **REST API** - HTTP requests for CRUD operations
2. **WebSocket** - Real-time updates for workflow events

Make sure the backend is running before starting the frontend:

```bash
# In backend directory
source .venv/bin/activate  # or: source venv/bin/activate
uvicorn app.main:app --reload
```

### CORS Configuration

The backend must allow requests from the frontend origin. Update `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
    # Add production URLs here
]
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js 14 App Router
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Home page
│   │   ├── conversations/   # Conversation pages
│   │   └── dashboard/       # Dashboard pages
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── chat/           # Chat interface components
│   │   ├── resolution/     # Resolution display/editing
│   │   └── layout/         # Layout components
│   ├── lib/                # Utility libraries
│   │   ├── api.ts          # API client (REST)
│   │   └── websocket.ts    # WebSocket client
│   ├── hooks/              # Custom React hooks
│   │   ├── useConversation.ts
│   │   ├── useResolution.ts
│   │   └── useWebSocket.ts
│   └── types/              # TypeScript type definitions
├── public/                 # Static assets
├── .env.example           # Example environment variables
├── .env.local            # Your local environment (git-ignored)
├── next.config.js        # Next.js configuration
├── tailwind.config.ts    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies and scripts
```

## Using the API Client

The API client provides type-safe access to all backend endpoints.

### Basic Usage

```typescript
import { apiClient } from '@/lib/api';

// Create a conversation
const conversation = await apiClient.createConversation({
  rep_id: 'rep_001',
  customer_id: 'cust_123',
  channel: 'chat'
});

// Add a message
const message = await apiClient.addMessage(conversation.id, {
  role: 'customer',
  content: 'How do I reset my password?'
});

// Trigger the workflow
await apiClient.triggerWorkflow(conversation.id, {
  rep_id: 'rep_001',
  force: false
});

// Get resolutions
const resolutions = await apiClient.getResolutionsByConversation(conversation.id);

// Approve a resolution
await apiClient.approveResolution(resolutions[0].id, {
  rep_id: 'rep_001',
  action: 'approve'
});
```

### Using React Hooks

The frontend provides custom hooks for easier data management:

```typescript
'use client';

import { useConversation, useTriggerWorkflow } from '@/hooks/useConversation';
import { useResolution } from '@/hooks/useResolution';

function ConversationPage({ conversationId }: { conversationId: string }) {
  // Fetch conversation and messages
  const {
    conversation,
    messages,
    isLoading,
    addMessage,
    isAddingMessage
  } = useConversation({ conversationId, autoRefresh: true });

  // Fetch resolutions
  const { resolutions, isLoading: resolutionsLoading } = useResolution({
    conversationId
  });

  // Trigger workflow
  const { triggerWorkflow, isTriggering } = useTriggerWorkflow(conversationId);

  const handleSendMessage = async (content: string) => {
    await addMessage({
      role: 'rep',
      content
    });
  };

  const handleTrigger = async () => {
    await triggerWorkflow({ repId: 'rep_001' });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Conversation {conversation?.id}</h1>

      {/* Messages display */}
      {messages.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}

      {/* Trigger button */}
      <button onClick={handleTrigger} disabled={isTriggering}>
        Trigger Workflow
      </button>

      {/* Resolutions */}
      {resolutions.map(res => (
        <div key={res.id}>{res.resolution_text}</div>
      ))}
    </div>
  );
}
```

## WebSocket Integration

### Using the WebSocket Hook

```typescript
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useState } from 'react';

function LiveConversation({ conversationId }: { conversationId: string }) {
  const [status, setStatus] = useState('idle');

  useWebSocket({
    conversationId,
    autoConnect: true,
    events: [
      'workflow_started',
      'resolution_generated',
      'evaluation_complete',
      'workflow_complete'
    ],
    onWorkflowStarted: (data) => {
      console.log('Workflow started:', data);
      setStatus('processing');
    },
    onResolutionGenerated: (data) => {
      console.log('Resolution generated:', data);
      setStatus('resolution_ready');
    },
    onEvaluationComplete: (data) => {
      console.log('Evaluation complete:', data);
    },
    onWorkflowComplete: (data) => {
      console.log('Workflow complete:', data);
      setStatus('complete');
    },
    onWorkflowFailed: (data) => {
      console.error('Workflow failed:', data);
      setStatus('failed');
    }
  });

  return (
    <div>
      <p>Status: {status}</p>
    </div>
  );
}
```

### Manual WebSocket Control

```typescript
import { wsClient } from '@/lib/websocket';

// Connect to a conversation
wsClient.connect('conv_12345');

// Subscribe to specific events
wsClient.subscribe(['workflow_started', 'resolution_generated']);

// Listen to events
wsClient.on('resolution_generated', (data) => {
  console.log('Resolution:', data);
});

// Disconnect
wsClient.disconnect();

// Check connection status
const connected = wsClient.isConnected();
```

## Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type checking
npm run type-check
```

### Code Style

This project uses:

- **TypeScript** - Type safety
- **ESLint** - Code linting
- **Prettier** - Code formatting (if configured)
- **Tailwind CSS** - Utility-first styling

### Component Development

Components use shadcn/ui for consistent UI elements:

```bash
# Add a new shadcn/ui component
npx shadcn-ui@latest add button
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add card
```

## Testing the Connection

### 1. Start the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Backend should be running at http://localhost:8000

### 2. Verify Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"0.1.0","environment":"development"}
```

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend should be running at http://localhost:3000

### 4. Test the Connection

Open your browser's console and run:

```javascript
// Test REST API
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('Backend health:', data));

// Test from the app
import { apiClient } from '@/lib/api';
const info = await apiClient.getApiInfo();
console.log('API Info:', info);
```

## Troubleshooting

### CORS Errors

**Error**: `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution**: Update backend CORS settings in `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

Restart the backend after making changes.

### WebSocket Connection Failed

**Error**: WebSocket connection to 'ws://localhost:8000' failed

**Solution**:
1. Verify backend is running
2. Check WebSocket URL in `.env.local`
3. Ensure no firewall blocking WebSocket connections
4. Check backend logs for WebSocket errors

### API Requests Timeout

**Error**: Request timeout or network error

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check for VPN/proxy interference
4. Increase timeout in `src/lib/api.ts` if needed:

```typescript
const client = axios.create({
  baseURL: API_URL,
  timeout: 60000, // Increase to 60 seconds
});
```

### Environment Variables Not Working

**Error**: API URL is undefined or using wrong value

**Solution**:
1. Ensure `.env.local` exists (not just `.env.example`)
2. Restart the dev server after changing `.env.local`
3. Verify variables start with `NEXT_PUBLIC_` for browser access
4. Check for typos in variable names

### Type Errors

**Error**: TypeScript compilation errors

**Solution**:
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Run type check
npm run type-check
```

## Production Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Variables

Set production environment variables:

```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Deployment Platforms

This Next.js app can be deployed to:

- **Vercel** (recommended) - Zero-config deployment
- **AWS Amplify**
- **Docker** - Use the included Dockerfile
- **Traditional hosting** - Build and serve the `.next` directory

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query (TanStack Query)](https://tanstack.com/query/latest)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
- [FAA Backend API Docs](http://localhost:8000/api/docs)

## Support

For issues with the frontend:
- Check backend logs: `docker-compose logs backend`
- Check frontend console for errors
- Review API documentation: http://localhost:8000/api/docs
- Test endpoints with Swagger UI: http://localhost:8000/api/docs

---

**Ready to build!** Start by creating conversation components and integrating the hooks.
