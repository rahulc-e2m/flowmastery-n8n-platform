import { useQuery, useQueryClient } from '@tanstack/react-query'
import ApiService, { N8nMetrics, ConfigStatus } from '@/services/api'

export const useMetrics = (fast = false) => {
  return useQuery({
    queryKey: ['metrics', fast ? 'fast' : 'full'],
    queryFn: () => ApiService.getMetrics(fast),
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}

export const useConfigStatus = () => {
  return useQuery({
    queryKey: ['config', 'status'],
    queryFn: () => ApiService.getConfigStatus(),
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

export const useWorkflows = (active?: boolean) => {
  return useQuery({
    queryKey: ['workflows', active],
    queryFn: () => ApiService.getWorkflows(active),
    retry: 2,
  })
}

export const useExecutions = (status?: string, workflowId?: string) => {
  return useQuery({
    queryKey: ['executions', status, workflowId],
    queryFn: () => ApiService.getExecutions(status, workflowId),
    retry: 2,
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