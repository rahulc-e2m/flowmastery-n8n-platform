import { useQuery, useQueryClient } from '@tanstack/react-query'
import ApiService from '@/services/api'
import { MetricsApi } from '@/services/metricsApi'
import { WorkflowsApi } from '@/services/workflowsApi'
import { AutomationApi } from '@/services/chatbotApi'
import { SystemApi } from '@/services/api'
import type { ExecutionFilters, HistoricalFilters } from '@/types'

// Standardized query keys
export const queryKeys = {
  // Metrics
  metricsOverview: (clientId?: string) => ['metrics', 'overview', clientId],
  metricsWorkflows: (clientId?: string) => ['metrics', 'workflows', clientId],
  metricsExecutions: (clientId?: string, filters?: ExecutionFilters) => 
    ['metrics', 'executions', clientId, filters],
  metricsExecutionStats: (clientId?: string) => ['metrics', 'execution-stats', clientId],
  metricsHistorical: (clientId?: string, filters?: HistoricalFilters) =>
    ['metrics', 'historical', clientId, filters],
  metricsDataFreshness: () => ['metrics', 'data-freshness'],
  
  // Workflows
  workflows: (clientId?: string, active?: boolean) => 
    ['workflows', clientId, active],
  workflow: (workflowId: string) => ['workflow', workflowId],
  
  // Automation
  chatbots: (clientId?: string) => ['automation', 'chatbots', clientId],
  chatbot: (chatbotId: string) => ['automation', 'chatbot', chatbotId],
  chatHistory: (chatbotId: string, filters?: any) => 
    ['automation', 'chat', chatbotId, 'history', filters],
  
  // System
  cacheStats: () => ['system', 'cache', 'stats'],
  taskStatus: (taskId: string) => ['system', 'task', taskId],
  workerStats: () => ['system', 'worker-stats'],
  
  // Legacy keys for backward compatibility
  metrics: (fast?: boolean) => ['metrics', fast ? 'fast' : 'full'],
  executions: (status?: string, workflowId?: string) => ['executions', status, workflowId],
  health: () => ['health'],
  configStatus: () => ['config', 'status'],
}

// New consolidated hooks
export const useMetricsOverview = (clientId?: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metricsOverview(clientId),
    queryFn: () => MetricsApi.getOverview(clientId),
    enabled,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })
}

export const useWorkflowsConsolidated = (clientId?: string, active?: boolean, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.workflows(clientId, active),
    queryFn: () => WorkflowsApi.getWorkflows(clientId, active),
    enabled,
    retry: 1,
  })
}

export const useExecutionsConsolidated = (clientId?: string, filters?: ExecutionFilters, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metricsExecutions(clientId, filters),
    queryFn: () => MetricsApi.getExecutions(clientId, filters),
    enabled,
    retry: 1,
  })
}

export const useExecutionStats = (clientId?: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metricsExecutionStats(clientId),
    queryFn: () => MetricsApi.getExecutionStats(clientId),
    enabled,
    retry: 1,
  })
}

export const useHistoricalMetrics = (clientId?: string, filters?: HistoricalFilters, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metricsHistorical(clientId, filters),
    queryFn: () => {
      // Convert HistoricalFilters to MetricsFilters if needed
      const metricsFilters = filters ? {
        ...filters,
        period_type: filters.period as 'DAILY' | 'WEEKLY' | 'MONTHLY',
        workflow_id: filters.workflow_id?.toString()
      } : undefined
      return MetricsApi.getHistorical(clientId, metricsFilters)
    },
    enabled,
    retry: 1,
  })
}

export const useDataFreshness = (enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metricsDataFreshness(),
    queryFn: () => MetricsApi.getDataFreshness(),
    enabled,
    refetchInterval: 2 * 60 * 1000, // 2 minutes
    retry: 1,
  })
}

export const useChatbots = (clientId?: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.chatbots(clientId),
    queryFn: () => AutomationApi.getChatbots(clientId),
    enabled,
    retry: 1,
  })
}

export const useCacheStats = (enabled = true) => {
  return useQuery({
    queryKey: queryKeys.cacheStats(),
    queryFn: () => SystemApi.getCacheStats(),
    enabled,
    retry: 1,
  })
}

export const useWorkerStats = (enabled = true) => {
  return useQuery({
    queryKey: queryKeys.workerStats(),
    queryFn: () => SystemApi.getWorkerStats(),
    enabled,
    refetchInterval: 30 * 1000, // 30 seconds
    retry: 1,
  })
}

// Legacy hooks for backward compatibility
export const useMetrics = (fast = false, enabled = true) => {
  console.warn('useMetrics is deprecated. Use useMetricsOverview instead.')
  return useQuery({
    queryKey: queryKeys.metrics(fast),
    queryFn: () => MetricsApi.getMyMetrics(),
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    enabled,
  })
}

export const useWorkflows = (active?: boolean, enabled = true) => {
  console.warn('useWorkflows is deprecated. Use useWorkflowsConsolidated instead.')
  return useQuery({
    queryKey: queryKeys.workflows(undefined, active),
    queryFn: () => WorkflowsApi.getWorkflows(undefined, active),
    retry: 1,
    enabled,
  })
}

export const useExecutions = (status?: string, workflowId?: string, enabled = true) => {
  console.warn('useExecutions is deprecated. Use useExecutionsConsolidated instead.')
  return useQuery({
    queryKey: queryKeys.executions(status, workflowId),
    queryFn: () => MetricsApi.getMyExecutions(10),
    retry: 1,
    enabled,
  })
}

export const useConfigStatus = () => {
  return useQuery({
    queryKey: queryKeys.configStatus(),
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
    queryKey: queryKeys.health(),
    queryFn: () => ApiService.checkHealth(),
    refetchInterval: 30 * 1000, // 30 seconds
    retry: 1,
  })
}

// Enhanced refresh utilities
export const useRefreshMetrics = () => {
  const queryClient = useQueryClient()
  
  return {
    // New consolidated refresh methods
    refreshOverview: (clientId?: string) => 
      queryClient.invalidateQueries({ queryKey: queryKeys.metricsOverview(clientId) }),
    refreshWorkflows: (clientId?: string) => 
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows(clientId) }),
    refreshExecutions: (clientId?: string) => 
      queryClient.invalidateQueries({ queryKey: queryKeys.metricsExecutions(clientId) }),
    refreshChatbots: (clientId?: string) => 
      queryClient.invalidateQueries({ queryKey: queryKeys.chatbots(clientId) }),
    refreshSystemStats: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cacheStats() })
      queryClient.invalidateQueries({ queryKey: queryKeys.workerStats() })
    },
    
    // Legacy refresh methods
    refreshFast: () => queryClient.invalidateQueries({ queryKey: queryKeys.metrics(true) }),
    refreshFull: () => queryClient.invalidateQueries({ queryKey: queryKeys.metrics(false) }),
    refreshAll: () => queryClient.invalidateQueries({ queryKey: ['metrics'] }),
  }
}