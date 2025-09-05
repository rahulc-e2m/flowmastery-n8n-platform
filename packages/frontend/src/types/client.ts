export interface ClientConfigStatus {
  configured: boolean
  connection_healthy?: boolean
  n8n_connection_status?: 'healthy' | 'error' | 'unknown'
  last_sync?: string
  sync_status?: 'success' | 'error' | 'pending'
}

export interface Client {
  id: string
  name: string
  n8n_api_url?: string
  has_n8n_api_key: boolean
  created_at: string
  config_status?: ClientConfigStatus  // New optional field when requested
}

export interface ClientCreate {
  name: string
}

export interface ClientUpdate {
  name?: string
  n8n_api_url?: string
}

export interface ClientN8nConfig {
  n8n_api_url: string
  n8n_api_key: string
}