/**
 * React Hook for Conversation Management
 *
 * Provides easy access to conversation data and operations
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Conversation, Message, CreateMessageRequest } from '@/lib/api';

export interface UseConversationOptions {
  conversationId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
}

export function useConversation(options: UseConversationOptions = {}) {
  const { conversationId, autoRefresh = false, refreshInterval = 5000 } = options;
  const queryClient = useQueryClient();

  // Fetch conversation data
  const {
    data: conversation,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => (conversationId ? apiClient.getConversation(conversationId) : null),
    enabled: !!conversationId,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch messages
  const {
    data: messages,
    isLoading: messagesLoading,
    error: messagesError,
    refetch: refetchMessages,
  } = useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => (conversationId ? apiClient.getMessages(conversationId) : []),
    enabled: !!conversationId,
  });

  // Add message mutation
  const addMessageMutation = useMutation({
    mutationFn: ({
      conversationId,
      data,
    }: {
      conversationId: string;
      data: CreateMessageRequest;
    }) => apiClient.addMessage(conversationId, data),
    onSuccess: () => {
      // Invalidate and refetch messages
      queryClient.invalidateQueries({ queryKey: ['messages', conversationId] });
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] });
    },
  });

  // Update conversation status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({
      conversationId,
      status,
    }: {
      conversationId: string;
      status: 'active' | 'completed' | 'escalated';
    }) => apiClient.updateConversationStatus(conversationId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] });
    },
  });

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: (conversationId: string) => apiClient.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] });
    },
  });

  // Helper functions
  const addMessage = useCallback(
    (data: CreateMessageRequest) => {
      if (!conversationId) {
        throw new Error('No conversation ID provided');
      }
      return addMessageMutation.mutateAsync({ conversationId, data });
    },
    [conversationId, addMessageMutation]
  );

  const updateStatus = useCallback(
    (status: 'active' | 'completed' | 'escalated') => {
      if (!conversationId) {
        throw new Error('No conversation ID provided');
      }
      return updateStatusMutation.mutateAsync({ conversationId, status });
    },
    [conversationId, updateStatusMutation]
  );

  const deleteConversation = useCallback(() => {
    if (!conversationId) {
      throw new Error('No conversation ID provided');
    }
    return deleteConversationMutation.mutateAsync(conversationId);
  }, [conversationId, deleteConversationMutation]);

  return {
    // Data
    conversation,
    messages: messages || [],

    // Loading states
    isLoading: isLoading || messagesLoading,
    isLoadingConversation: isLoading,
    isLoadingMessages: messagesLoading,

    // Errors
    error: error || messagesError,
    conversationError: error,
    messagesError,

    // Mutations
    addMessage,
    updateStatus,
    deleteConversation,

    // Mutation states
    isAddingMessage: addMessageMutation.isPending,
    isUpdatingStatus: updateStatusMutation.isPending,
    isDeletingConversation: deleteConversationMutation.isPending,

    // Manual refresh
    refetch,
    refetchMessages,
  };
}

/**
 * Hook for creating a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: apiClient.createConversation.bind(apiClient),
    onSuccess: (data) => {
      // Add to cache
      queryClient.setQueryData(['conversation', data.id], data);
    },
  });

  return {
    createConversation: mutation.mutateAsync,
    isCreating: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
  };
}

/**
 * Hook for triggering workflow
 */
export function useTriggerWorkflow(conversationId?: string) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ repId, force }: { repId: string; force?: boolean }) => {
      if (!conversationId) {
        throw new Error('No conversation ID provided');
      }
      return apiClient.triggerWorkflow(conversationId, { rep_id: repId, force });
    },
    onSuccess: () => {
      // Invalidate conversation to get updated status
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] });
      queryClient.invalidateQueries({ queryKey: ['resolutions', conversationId] });
    },
  });

  return {
    triggerWorkflow: mutation.mutateAsync,
    isTriggering: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
  };
}
