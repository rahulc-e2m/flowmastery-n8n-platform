import { useQuery, useQueryClient } from '@tanstack/react-query'
import ApiService from '@/services/api'
import { MetricsApi } from '@/services/metricsApi'
import { WorkflowsApi } from '@/services/workflowsApi'

export const useMetrics = (fast = false, enabled = true) => {
  return useQuery({
    queryKey: ['metrics', fast ? 'fast' : 'full'],
    queryFn: () => MetricsApi.getMyMetrics(),
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Reduced retry to avoid spam
    enabled, // Allow disabling the query
  })
}

export const useConfigStatus = () => {
  return useQuery({
    queryKey: ['config', 'status'],
    queryFn: async () => {
      // Use fetch directly for public config endpoints to avoid auth issues
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/config/app/status`)
      if (!response.ok) throw new Error('Failed to fetch config status')
      return response.json()
    },
    retry: 1,
  })
}

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => ApiService.checkHealth(),
    refetchInterval: 30 * 1000, // 30 seconds
    retry: 1,
  })
}

export const useWorkflows = (active?: boolean, enabled = true) => {
  return useQuery({
    queryKey: ['workflows', active],
    queryFn: () => WorkflowsApi.listAll(undefined, active ? 'active' : undefined),
    retry: 1,
    enabled,
  })
}

export const useExecutions = (status?: string, workflowId?: string, enabled = true) => {
  return useQuery({
    queryKey: ['executions', status, workflowId],
    queryFn: () => MetricsApi.getMyExecutions(10),
    retry: 1,
    enabled,
  })
}

// Custom hook for refreshing metrics
export const useRefreshMetrics = () => {
  const queryClient = useQueryClient()
  
  return {
    refreshFast: () => queryClient.invalidateQueries({ queryKey: ['metrics', 'fast'] }),
    refreshFull: () => queryClient.invalidateQueries({ queryKey: ['metrics', 'full'] }),
    refreshAll: () => queryClient.invalidateQueries({ queryKey: ['metrics'] }),
  }
}