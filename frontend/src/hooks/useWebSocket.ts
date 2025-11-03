/**
 * React Hook for WebSocket Management
 *
 * Manages WebSocket connection lifecycle and event subscriptions
 */

import { useEffect, useCallback, useRef } from 'react';
import { wsClient, WebSocketEvent, WebSocketEventData } from '@/lib/websocket';

export interface UseWebSocketOptions {
  conversationId?: string;
  events?: WebSocketEvent[];
  onConnected?: (data: WebSocketEventData) => void;
  onWorkflowStarted?: (data: WebSocketEventData) => void;
  onQueryOptimized?: (data: WebSocketEventData) => void;
  onSearchComplete?: (data: WebSocketEventData) => void;
  onResolutionGenerated?: (data: WebSocketEventData) => void;
  onEvaluationComplete?: (data: WebSocketEventData) => void;
  onWorkflowComplete?: (data: WebSocketEventData) => void;
  onWorkflowFailed?: (data: WebSocketEventData) => void;
  onMessageAdded?: (data: WebSocketEventData) => void;
  onConversationUpdated?: (data: WebSocketEventData) => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    conversationId,
    events = [],
    onConnected,
    onWorkflowStarted,
    onQueryOptimized,
    onSearchComplete,
    onResolutionGenerated,
    onEvaluationComplete,
    onWorkflowComplete,
    onWorkflowFailed,
    onMessageAdded,
    onConversationUpdated,
    autoConnect = true,
  } = options;

  // Use refs to avoid re-registering event handlers on every render
  const handlersRef = useRef({
    onConnected,
    onWorkflowStarted,
    onQueryOptimized,
    onSearchComplete,
    onResolutionGenerated,
    onEvaluationComplete,
    onWorkflowComplete,
    onWorkflowFailed,
    onMessageAdded,
    onConversationUpdated,
  });

  // Update refs when handlers change
  useEffect(() => {
    handlersRef.current = {
      onConnected,
      onWorkflowStarted,
      onQueryOptimized,
      onSearchComplete,
      onResolutionGenerated,
      onEvaluationComplete,
      onWorkflowComplete,
      onWorkflowFailed,
      onMessageAdded,
      onConversationUpdated,
    };
  }, [
    onConnected,
    onWorkflowStarted,
    onQueryOptimized,
    onSearchComplete,
    onResolutionGenerated,
    onEvaluationComplete,
    onWorkflowComplete,
    onWorkflowFailed,
    onMessageAdded,
    onConversationUpdated,
  ]);

  // Connect/disconnect based on conversationId
  useEffect(() => {
    if (autoConnect && conversationId) {
      wsClient.connect(conversationId);

      return () => {
        wsClient.disconnect();
      };
    }
  }, [conversationId, autoConnect]);

  // Register event handlers
  useEffect(() => {
    if (!conversationId) return;

    // Create stable handler references
    const handlers: Record<WebSocketEvent, (data: WebSocketEventData) => void> = {
      connected: (data) => handlersRef.current.onConnected?.(data),
      workflow_started: (data) => handlersRef.current.onWorkflowStarted?.(data),
      query_optimized: (data) => handlersRef.current.onQueryOptimized?.(data),
      search_complete: (data) => handlersRef.current.onSearchComplete?.(data),
      resolution_generated: (data) => handlersRef.current.onResolutionGenerated?.(data),
      evaluation_complete: (data) => handlersRef.current.onEvaluationComplete?.(data),
      workflow_complete: (data) => handlersRef.current.onWorkflowComplete?.(data),
      workflow_failed: (data) => handlersRef.current.onWorkflowFailed?.(data),
      message_added: (data) => handlersRef.current.onMessageAdded?.(data),
      conversation_updated: (data) => handlersRef.current.onConversationUpdated?.(data),
    };

    // Register all handlers
    Object.entries(handlers).forEach(([event, handler]) => {
      wsClient.on(event as WebSocketEvent, handler);
    });

    // Subscribe to specific events if provided
    if (events.length > 0) {
      wsClient.subscribe(events);
    }

    // Cleanup: unregister handlers
    return () => {
      Object.entries(handlers).forEach(([event, handler]) => {
        wsClient.off(event as WebSocketEvent, handler);
      });
    };
  }, [conversationId, events]);

  // Manual connection controls
  const connect = useCallback(() => {
    if (conversationId) {
      wsClient.connect(conversationId);
    }
  }, [conversationId]);

  const disconnect = useCallback(() => {
    wsClient.disconnect();
  }, []);

  const subscribe = useCallback(
    (eventList: WebSocketEvent[]) => {
      wsClient.subscribe(eventList);
    },
    []
  );

  const isConnected = useCallback(() => {
    return wsClient.isConnected();
  }, []);

  return {
    connect,
    disconnect,
    subscribe,
    isConnected,
    conversationId: wsClient.getConversationId(),
  };
}

/**
 * Simple hook for listening to a single WebSocket event
 */
export function useWebSocketEvent(
  event: WebSocketEvent,
  handler: (data: WebSocketEventData) => void,
  conversationId?: string
) {
  useWebSocket({
    conversationId,
    autoConnect: !!conversationId,
    [`on${event.charAt(0).toUpperCase() + event.slice(1)}`]: handler,
  });
}
