/**
 * React Hook for Resolution Management
 *
 * Provides easy access to resolution data and operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { apiClient, Resolution } from '@/lib/api';

export interface UseResolutionOptions {
  resolutionId?: string;
  conversationId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function useResolution(options: UseResolutionOptions = {}) {
  const { resolutionId, conversationId, autoRefresh = false, refreshInterval = 5000 } = options;
  const queryClient = useQueryClient();

  // Fetch single resolution by ID
  const {
    data: resolution,
    isLoading: isLoadingResolution,
    error: resolutionError,
    refetch: refetchResolution,
  } = useQuery({
    queryKey: ['resolution', resolutionId],
    queryFn: () => (resolutionId ? apiClient.getResolution(resolutionId) : null),
    enabled: !!resolutionId,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch resolutions by conversation ID
  const {
    data: resolutions,
    isLoading: isLoadingResolutions,
    error: resolutionsError,
    refetch: refetchResolutions,
  } = useQuery({
    queryKey: ['resolutions', conversationId],
    queryFn: () =>
      conversationId ? apiClient.getResolutionsByConversation(conversationId) : [],
    enabled: !!conversationId,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Update resolution mutation
  const updateResolutionMutation = useMutation({
    mutationFn: ({
      resolutionId,
      editedText,
      repId,
      editReason,
    }: {
      resolutionId: string;
      editedText: string;
      repId: string;
      editReason?: string;
    }) => apiClient.updateResolution(resolutionId, editedText, repId, editReason),
    onSuccess: (data) => {
      // Update cache
      queryClient.setQueryData(['resolution', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['resolutions', conversationId] });
    },
  });

  // Approve resolution mutation
  const approveResolutionMutation = useMutation({
    mutationFn: ({
      resolutionId,
      repId,
      action,
      feedback,
    }: {
      resolutionId: string;
      repId: string;
      action: 'approve' | 'reject' | 'edit';
      feedback?: string;
    }) => apiClient.approveResolution(resolutionId, { rep_id: repId, action, feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resolution', resolutionId] });
      queryClient.invalidateQueries({ queryKey: ['resolutions', conversationId] });
    },
  });

  // Submit feedback mutation
  const submitFeedbackMutation = useMutation({
    mutationFn: ({
      resolutionId,
      rating,
      feedbackText,
    }: {
      resolutionId: string;
      rating: number;
      feedbackText?: string;
    }) => apiClient.submitResolutionFeedback(resolutionId, rating, feedbackText),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resolution', resolutionId] });
    },
  });

  // Helper functions
  const updateResolution = useCallback(
    (editedText: string, repId: string, editReason?: string) => {
      if (!resolutionId) {
        throw new Error('No resolution ID provided');
      }
      return updateResolutionMutation.mutateAsync({
        resolutionId,
        editedText,
        repId,
        editReason,
      });
    },
    [resolutionId, updateResolutionMutation]
  );

  const approveResolution = useCallback(
    (repId: string, action: 'approve' | 'reject' | 'edit', feedback?: string) => {
      if (!resolutionId) {
        throw new Error('No resolution ID provided');
      }
      return approveResolutionMutation.mutateAsync({ resolutionId, repId, action, feedback });
    },
    [resolutionId, approveResolutionMutation]
  );

  const submitFeedback = useCallback(
    (rating: number, feedbackText?: string) => {
      if (!resolutionId) {
        throw new Error('No resolution ID provided');
      }
      return submitFeedbackMutation.mutateAsync({ resolutionId, rating, feedbackText });
    },
    [resolutionId, submitFeedbackMutation]
  );

  return {
    // Data
    resolution,
    resolutions: resolutions || [],

    // Loading states
    isLoading: isLoadingResolution || isLoadingResolutions,
    isLoadingResolution,
    isLoadingResolutions,

    // Errors
    error: resolutionError || resolutionsError,
    resolutionError,
    resolutionsError,

    // Mutations
    updateResolution,
    approveResolution,
    submitFeedback,

    // Mutation states
    isUpdating: updateResolutionMutation.isPending,
    isApproving: approveResolutionMutation.isPending,
    isSubmittingFeedback: submitFeedbackMutation.isPending,

    // Manual refresh
    refetch: refetchResolution,
    refetchResolutions,
  };
}

/**
 * Hook for fetching resolution scores
 */
export function useResolutionScores(resolutionId?: string) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['resolutionScores', resolutionId],
    queryFn: () => (resolutionId ? apiClient.getResolutionScores(resolutionId) : null),
    enabled: !!resolutionId,
  });

  return {
    scores: data,
    isLoading,
    error,
    refetch,
  };
}
