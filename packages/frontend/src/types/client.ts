export interface Client {
  id: string
  name: string
  n8n_api_url?: string
  has_n8n_api_key: boolean
  created_at: string
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