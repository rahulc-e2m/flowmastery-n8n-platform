import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { WorkflowsApi, type WorkflowListItem } from '@/services/workflowsApi'
import { ClientApi } from '@/services/clientApi'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { MoreHorizontal, Clock, Search, X, MessageCircle, Mail, Calendar, FileText, Bot, ArrowLeft, ExternalLink, Settings, Zap } from 'lucide-react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

function MinutesTimeSelector({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const hours = Math.floor(value / 60)
  const minutes = value % 60
  const setHours = (h: number) => onChange(h * 60 + minutes)
  const setMinutes = (m: number) => onChange(hours * 60 + m)
  return (
    <div className="flex items-center space-x-3">
      <Select value={String(hours)} onValueChange={(v) => setHours(parseInt(v, 10))}>
        <SelectTrigger className="w-24"><SelectValue placeholder="Hours" /></SelectTrigger>
        <SelectContent>
          {Array.from({ length: 25 }).map((_, i) => (
            <SelectItem key={i} value={String(i)}>{i}h</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={String(minutes)} onValueChange={(v) => setMinutes(parseInt(v, 10))}>
        <SelectTrigger className="w-24"><SelectValue placeholder="Minutes" /></SelectTrigger>
        <SelectContent>
          {[0,5,10,15,20,25,30,35,40,45,50,55].map((m) => (
            <SelectItem key={m} value={String(m)}>{m}m</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

interface WorkflowsPageProps {
  workflowType?: 'chatbot' | 'email' | 'calendar' | 'documents' | 'custom'
}

export function WorkflowsPage({ workflowType }: WorkflowsPageProps) {
  const { isAdmin } = useAuth()
  const qc = useQueryClient()
  const [clientFilter, setClientFilter] = React.useState<string>('all')
  const [activeFilter, setActiveFilter] = React.useState<string>('active')
  const [successRateFilter, setSuccessRateFilter] = React.useState<string>('all')
  const [volumeFilter, setVolumeFilter] = React.useState<string>('all')
  const [lastExecutionFilter, setLastExecutionFilter] = React.useState<string>('all')
  const [searchQuery, setSearchQuery] = React.useState<string>('')
  const [editing, setEditing] = React.useState<WorkflowListItem | null>(null)
  const [minutes, setMinutes] = React.useState<number>(30)
  const clientId = isAdmin && clientFilter && clientFilter !== 'all' ? clientFilter : undefined

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
    enabled: isAdmin,
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['workflows', clientId ?? 'mine', activeFilter],
    queryFn: () => (isAdmin ? WorkflowsApi.listAll(clientId, activeFilter) : WorkflowsApi.listMine(activeFilter)),
  })

  // Client-side filtering function
  const filteredWorkflows = React.useMemo(() => {
    if (!data?.workflows) return []
    
    return data.workflows.filter(wf => {
      // Search filter
      if (searchQuery && !wf.workflow_name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      
      // Success rate filter
      if (successRateFilter !== 'all') {
        if (successRateFilter === 'high' && wf.success_rate < 90) return false
        if (successRateFilter === 'medium' && (wf.success_rate < 50 || wf.success_rate >= 90)) return false
        if (successRateFilter === 'low' && wf.success_rate >= 50) return false
      }
      
      // Volume filter
      if (volumeFilter !== 'all') {
        if (volumeFilter === 'high' && wf.total_executions < 100) return false
        if (volumeFilter === 'medium' && (wf.total_executions < 10 || wf.total_executions >= 100)) return false
        if (volumeFilter === 'low' && wf.total_executions >= 10) return false
      }
      
      // Last execution filter
      if (lastExecutionFilter !== 'all' && wf.last_execution) {
        const lastExec = new Date(wf.last_execution)
        const now = new Date()
        const diffHours = (now.getTime() - lastExec.getTime()) / (1000 * 60 * 60)
        
        if (lastExecutionFilter === 'recent' && diffHours > 24) return false
        if (lastExecutionFilter === 'week' && (diffHours <= 24 || diffHours > 168)) return false
        if (lastExecutionFilter === 'month' && (diffHours <= 168 || diffHours > 720)) return false
        if (lastExecutionFilter === 'older' && diffHours <= 720) return false
      }
      
      // Client filter (admin only)
      if (isAdmin && clientFilter !== 'all' && String(wf.client_id) !== clientFilter) {
        return false
      }
      
      return true
    }).sort((a, b) => {
      // Sort by last execution date (most recent first)
      if (!a.last_execution && !b.last_execution) return 0
      if (!a.last_execution) return 1
      if (!b.last_execution) return -1
      return new Date(b.last_execution).getTime() - new Date(a.last_execution).getTime()
    })
  }, [data?.workflows, searchQuery, successRateFilter, volumeFilter, lastExecutionFilter, clientFilter, isAdmin])

  const openEdit = (wf: WorkflowListItem) => {
    setEditing(wf)
    setMinutes(wf.time_saved_per_execution_minutes ?? 30)
  }

  const save = async () => {
    if (!editing) return
    try {
      await WorkflowsApi.updateMinutes(editing.id, minutes)
      toast.success('Updated time saved per execution')
      setEditing(null)
      // Refetch workflows and dashboards
      await Promise.all([
        refetch(),
        qc.invalidateQueries({ queryKey: ['my-metrics'] }),
        qc.invalidateQueries({ queryKey: ['admin-metrics'] }),
        qc.invalidateQueries({ queryKey: ['my-workflows'] }),
      ])
    } catch (e: any) {
      toast.error('Failed to update')
    }
  }

  // If workflowType is specified, show the workflow interface
  if (workflowType) {
    if (workflowType === 'chatbot') {
      return <ChatbotInterface />
    }
    return <WorkflowInterface workflowType={workflowType} />
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Workflows</h1>
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          
          {/* Status Filter */}
          <Select value={activeFilter} onValueChange={setActiveFilter}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active only</SelectItem>
              <SelectItem value="inactive">Inactive only</SelectItem>
              <SelectItem value="all">All status</SelectItem>
            </SelectContent>
          </Select>
          
          {/* Success Rate Filter */}
          <Select value={successRateFilter} onValueChange={setSuccessRateFilter}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Success Rate" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All rates</SelectItem>
              <SelectItem value="high">High (&gt;90%)</SelectItem>
              <SelectItem value="medium">Medium (50-90%)</SelectItem>
              <SelectItem value="low">Low (&lt;50%)</SelectItem>
            </SelectContent>
          </Select>
          
          {/* Volume Filter */}
          <Select value={volumeFilter} onValueChange={setVolumeFilter}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Volume" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All volumes</SelectItem>
              <SelectItem value="high">High (&gt;100)</SelectItem>
              <SelectItem value="medium">Medium (10-100)</SelectItem>
              <SelectItem value="low">Low (&lt;10)</SelectItem>
            </SelectContent>
          </Select>
          
          {/* Last Execution Filter */}
          <Select value={lastExecutionFilter} onValueChange={setLastExecutionFilter}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Last Run" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any time</SelectItem>
              <SelectItem value="recent">Last 24h</SelectItem>
              <SelectItem value="week">This week</SelectItem>
              <SelectItem value="month">This month</SelectItem>
              <SelectItem value="older">Older</SelectItem>
            </SelectContent>
          </Select>
          
          {/* Client Filter (Admin only) */}
          {isAdmin && (
            <Select value={clientFilter} onValueChange={setClientFilter}>
              <SelectTrigger className="w-48"><SelectValue placeholder="Client" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All clients</SelectItem>
                {clients?.map((c: any) => (
                  <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          
          {/* Clear Filters Button */}
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => {
              setSearchQuery('')
              setActiveFilter('active')
              setSuccessRateFilter('all')
              setVolumeFilter('all')
              setLastExecutionFilter('all')
              setClientFilter('all')
            }}
            className="flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Clear
          </Button>
        </div>
      </div>

      {/* Results Summary */}
      <div className="text-sm text-gray-600">
        Showing {filteredWorkflows.length} of {data?.total || 0} workflows
      </div>

      <Card className="p-0 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {isAdmin && <TableHead>Client</TableHead>}
              <TableHead>Workflow</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Executions</TableHead>
              <TableHead className="text-right">Success %</TableHead>
              <TableHead className="text-right">Last Run</TableHead>
              <TableHead className="text-right">Per Exec Saved</TableHead>
              <TableHead className="text-right">Total Time Saved</TableHead>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredWorkflows.map((wf) => (
              <TableRow key={wf.id}>
                {isAdmin && <TableCell className="font-medium">{wf.client_name}</TableCell>}
                <TableCell className="font-medium">{wf.workflow_name}</TableCell>
                <TableCell>{wf.active ? 'Active' : 'Inactive'}</TableCell>
                <TableCell className="text-right">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    wf.total_executions > 100 ? 'bg-green-100 text-green-800' :
                    wf.total_executions > 10 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {wf.total_executions}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    wf.success_rate >= 90 ? 'bg-green-100 text-green-800' :
                    wf.success_rate >= 50 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {wf.success_rate?.toFixed(1) || '0.0'}%
                  </span>
                </TableCell>
                <TableCell className="text-right">{wf.last_execution ? new Date(wf.last_execution).toLocaleString() : '-'}</TableCell>
                <TableCell className="text-right flex items-center justify-end space-x-1">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span>{Math.floor((wf.time_saved_per_execution_minutes || 0)/60)}h {(wf.time_saved_per_execution_minutes||0)%60}m</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800 font-medium">
                    {wf.time_saved_hours ? `${wf.time_saved_hours}h` : '0h'}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openEdit(wf)}>Edit</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            
            {filteredWorkflows.length === 0 && !isLoading && (
              <TableRow>
                <TableCell colSpan={isAdmin ? 9 : 8} className="text-center py-8 text-gray-500">
                  {data?.workflows?.length ? 'No workflows match the current filters' : 'No workflows found'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={!!editing} onOpenChange={(o) => { if (!o) setEditing(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit time saved per execution</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <MinutesTimeSelector value={minutes} onChange={setMinutes} />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditing(null)}>Cancel</Button>
            <Button onClick={save}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Chatbot Interface Component
function ChatbotInterface() {
  const [messages, setMessages] = React.useState([
    {
      id: '1',
      text: 'Hello! I\'m your AI assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)
  const [showConfig, setShowConfig] = React.useState(false)
  const [webhookUrl, setWebhookUrl] = React.useState(localStorage.getItem('chatbot_webhook_url') || '')
  const [apiKey, setApiKey] = React.useState(localStorage.getItem('chatbot_api_key') || '')
  const [isConfigured, setIsConfigured] = React.useState(!!localStorage.getItem('chatbot_webhook_url'))
  const [showDebug, setShowDebug] = React.useState(false)
  const [lastResponse, setLastResponse] = React.useState<any>(null)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSaveConfig = () => {
    if (!webhookUrl.trim()) {
      toast.error('Please enter a valid webhook URL')
      return
    }
    
    localStorage.setItem('chatbot_webhook_url', webhookUrl)
    localStorage.setItem('chatbot_api_key', apiKey)
    setIsConfigured(true)
    setShowConfig(false)
    toast.success('Chatbot configuration saved successfully!')
  }

  const handleClearConfig = () => {
    localStorage.removeItem('chatbot_webhook_url')
    localStorage.removeItem('chatbot_api_key')
    setWebhookUrl('')
    setApiKey('')
    setIsConfigured(false)
    toast.success('Configuration cleared')
  }

  const sendMessage = async () => {
    if (!inputMessage.trim()) return
    if (!isConfigured) {
      toast.error('Please configure the chatbot webhook first')
      setShowConfig(true)
      return
    }

    const userMessage = {
      id: Date.now().toString(),
      text: inputMessage,
      sender: 'user' as const,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Call n8n webhook
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
        },
        body: JSON.stringify({
          message: inputMessage,
          timestamp: new Date().toISOString(),
          sessionId: 'web-chat-' + Date.now()
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Store the last response for debugging
      setLastResponse(data)
      
      // Log the full response for debugging
      console.log('Full n8n webhook response:', data)
      
      // Enhanced response parsing to handle various n8n response formats
      let botResponseText = ''
      
      if (typeof data === 'string') {
        // If the response is a direct string
        botResponseText = data
      } else if (data.response) {
        // Standard response field
        botResponseText = data.response
      } else if (data.message) {
        // Alternative message field
        botResponseText = data.message
      } else if (data.output) {
        // n8n sometimes uses 'output' field
        botResponseText = data.output
      } else if (data.result) {
        // Some workflows use 'result' field
        botResponseText = data.result
      } else if (data.text) {
        // Text field for simple responses
        botResponseText = data.text
      } else if (data.content) {
        // Content field
        botResponseText = data.content
      } else if (data.reply) {
        // Reply field
        botResponseText = data.reply
      } else if (data.data && typeof data.data === 'string') {
        // Data field with string content
        botResponseText = data.data
      } else if (data.data && data.data.response) {
        // Nested response in data object
        botResponseText = data.data.response
      } else if (data.data && data.data.message) {
        // Nested message in data object
        botResponseText = data.data.message
      } else if (Array.isArray(data) && data.length > 0) {
        // If it's an array, try to get the first item
        const firstItem = data[0]
        if (typeof firstItem === 'string') {
          botResponseText = firstItem
        } else if (firstItem.response) {
          botResponseText = firstItem.response
        } else if (firstItem.message) {
          botResponseText = firstItem.message
        } else if (firstItem.output) {
          botResponseText = firstItem.output
        }
      }
      
      // If we still don't have a response, show the structure to the user
      if (!botResponseText) {
        console.warn('Could not parse n8n response. Available fields:', Object.keys(data))
        botResponseText = `I received a response, but couldn't parse it. Response structure: ${JSON.stringify(Object.keys(data))}. Please check the n8n workflow output format.`
      }
      
      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: botResponseText,
        sender: 'bot' as const,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error calling webhook:', error)
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting to my brain right now. Please check the configuration or try again later.',
        sender: 'bot' as const,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Failed to get response from chatbot')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        text: 'Hello! I\'m your AI assistant. How can I help you today?',
        sender: 'bot',
        timestamp: new Date()
      }
    ])
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/workflows">
            <Button variant="ghost" size="sm" className="flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Workflows</span>
            </Button>
          </Link>
          <div className="flex items-center space-x-3">
            <motion.div 
              className="p-3 rounded-xl bg-blue-500 text-white"
              whileHover={{ scale: 1.05 }}
            >
              <MessageCircle className="w-6 h-6" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold">AI Chatbot Interface</h1>
              <p className="text-muted-foreground">Interactive chat with your n8n-powered AI assistant</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConfig(true)}
            className="flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Configure</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDebug(!showDebug)}
            className="flex items-center space-x-2"
          >
            <Bot className="w-4 h-4" />
            <span>Debug</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearChat}
            className="flex items-center space-x-2"
          >
            <X className="w-4 h-4" />
            <span>Clear Chat</span>
          </Button>
        </div>
      </div>

      {/* Debug Panel */}
      {showDebug && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader>
            <CardTitle className="text-purple-900">Debug Information</CardTitle>
            <CardDescription className="text-purple-700">
              This panel shows the raw response from your n8n webhook to help troubleshoot parsing issues.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-purple-900 mb-2">Webhook URL:</h4>
                <code className="text-xs bg-purple-100 p-2 rounded block text-purple-800 break-all">
                  {webhookUrl || 'Not configured'}
                </code>
              </div>
              
              <div>
                <h4 className="font-medium text-purple-900 mb-2">Last Response:</h4>
                <div className="bg-purple-100 p-3 rounded text-xs">
                  {lastResponse ? (
                    <pre className="text-purple-800 whitespace-pre-wrap">
                      {JSON.stringify(lastResponse, null, 2)}
                    </pre>
                  ) : (
                    <span className="text-purple-600">No responses yet. Send a message to see the webhook response.</span>
                  )}
                </div>
              </div>
              
              {lastResponse && (
                <div>
                  <h4 className="font-medium text-purple-900 mb-2">Available Fields:</h4>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(lastResponse).map((key) => (
                      <Badge key={key} variant="outline" className="text-purple-700 border-purple-300">
                        {key}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-xs text-purple-600">
                <p>💡 <strong>Tip:</strong> Make sure your n8n workflow returns a response with one of these fields:</p>
                <p className="mt-1"><code>response</code>, <code>message</code>, <code>output</code>, <code>result</code>, <code>text</code>, <code>content</code>, or <code>reply</code></p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Status */}
      {!isConfigured && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-yellow-800">
              <Bot className="w-5 h-5" />
              <span className="font-medium">Configuration Required</span>
            </div>
            <p className="text-sm text-yellow-700 mt-1">
              Please configure your n8n webhook URL to enable chatbot functionality.
            </p>
            <Button 
              size="sm" 
              className="mt-3" 
              onClick={() => setShowConfig(true)}
            >
              Configure Now
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chat Area */}
        <div className="lg:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <MessageCircle className="w-5 h-5 text-blue-500" />
                    <span>Chat Assistant</span>
                  </CardTitle>
                  <CardDescription>Powered by n8n workflow automation</CardDescription>
                </div>
                <Badge variant={isConfigured ? 'default' : 'secondary'}>
                  {isConfigured ? 'Connected' : 'Not Configured'}
                </Badge>
              </div>
            </CardHeader>
            
            {/* Messages Area */}
            <CardContent className="flex-1 overflow-hidden p-0">
              <div className="h-full overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.sender === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </CardContent>
            
            {/* Input Area */}
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message here..."
                  disabled={isLoading || !isConfigured}
                  className="flex-1"
                />
                <Button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim() || !isConfigured}
                  className="px-6"
                >
                  {isLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  ) : (
                    'Send'
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Chat Info & Settings Panel */}
        <div className="space-y-4">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Chat Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Messages:</span>
                <Badge variant="outline">{messages.length}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status:</span>
                <Badge variant={isConfigured ? 'default' : 'secondary'}>
                  {isConfigured ? 'Ready' : 'Setup Required'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Response Time:</span>
                <Badge variant="outline">~2s avg</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Features */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Bot className="w-4 h-4 text-green-500" />
                  <span className="text-sm">AI-Powered Responses</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span className="text-sm">n8n Integration</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MessageCircle className="w-4 h-4 text-purple-500" />
                  <span className="text-sm">Real-time Chat</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Settings className="w-4 h-4 text-orange-500" />
                  <span className="text-sm">Configurable Webhooks</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <FileText className="w-4 h-4 mr-2" />
                Export Chat History
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <ExternalLink className="w-4 h-4 mr-2" />
                Open n8n Editor
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start" onClick={() => setShowConfig(true)}>
                <Settings className="w-4 h-4 mr-2" />
                Configure Webhook
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Configuration Dialog */}
      <Dialog open={showConfig} onOpenChange={setShowConfig}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Configure Chatbot</DialogTitle>
            <CardDescription>
              Set up your n8n webhook URL and optional API key for the chatbot integration.
            </CardDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">n8n Webhook URL *</label>
              <Input
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://your-n8n-instance.com/webhook/chatbot"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter the webhook URL from your n8n chatbot workflow
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">API Key (Optional)</label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter API key if required"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optional authentication key for secure webhooks
              </p>
            </div>
          </div>
          <DialogFooter className="flex justify-between">
            <Button variant="outline" onClick={handleClearConfig} disabled={!isConfigured}>
              Clear Config
            </Button>
            <div className="space-x-2">
              <Button variant="outline" onClick={() => setShowConfig(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveConfig}>
                Save Configuration
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Generic Workflow Interface Component for other workflow types
function WorkflowInterface({ workflowType }: { workflowType: 'email' | 'calendar' | 'documents' | 'custom' }) {
  const workflowConfig = {
    email: {
      title: 'Email Automation',
      description: 'Automate your email workflows with smart templates and triggers',
      icon: Mail,
      features: ['Email Templates', 'Auto-replies', 'Smart Filtering', 'Bulk Operations']
    },
    calendar: {
      title: 'Calendar Integration', 
      description: 'Sync and automate calendar events across platforms',
      icon: Calendar,
      features: ['Event Sync', 'Meeting Automation', 'Reminder Systems', 'Availability Checks']
    },
    documents: {
      title: 'Document Workflow',
      description: 'Streamline document processing and management',
      icon: FileText,
      features: ['Document Processing', 'Auto-generation', 'Approval Workflows', 'Version Control']
    },
    custom: {
      title: 'Custom Workflow',
      description: 'Build your own custom automation workflows',
      icon: Bot,
      features: ['Custom Logic', 'API Integrations', 'Advanced Triggers', 'Data Processing']
    }
  }

  const config = workflowConfig[workflowType]
  const IconComponent = config.icon

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/workflows">
            <Button variant="ghost" size="sm" className="flex items-center space-x-2">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Workflows</span>
            </Button>
          </Link>
          <div className="flex items-center space-x-3">
            <motion.div 
              className="p-3 rounded-xl bg-blue-500 text-white"
              whileHover={{ scale: 1.05 }}
            >
              <IconComponent className="w-6 h-6" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold">{config.title}</h1>
              <p className="text-muted-foreground">{config.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Coming Soon Notice */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 rounded-full bg-blue-100">
              <IconComponent className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900">{config.title} - Coming Soon</h3>
              <p className="text-blue-700 text-sm">We're working on bringing you this powerful workflow automation.</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Planned Features:</h4>
              <ul className="space-y-1">
                {config.features.map((feature, index) => (
                  <li key={index} className="text-sm text-blue-700 flex items-center space-x-2">
                    <Zap className="w-3 h-3" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Integration Ready:</h4>
              <div className="space-y-2">
                <div className="flex items-center space-x-2 text-sm text-blue-700">
                  <Settings className="w-3 h-3" />
                  <span>n8n Workflow Engine</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-blue-700">
                  <ExternalLink className="w-3 h-3" />
                  <span>API Connectivity</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-blue-700">
                  <Bot className="w-3 h-3" />
                  <span>Smart Automation</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-blue-200">
            <p className="text-sm text-blue-600 mb-3">Want to be notified when {config.title} is available?</p>
            <div className="flex space-x-2">
              <Button size="sm" variant="outline" className="text-blue-600 border-blue-300">
                Get Notified
              </Button>
              <Button size="sm" variant="outline" className="text-blue-600 border-blue-300">
                Request Feature
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <IconComponent className="w-5 h-5" />
              <span>Workflow Preview</span>
            </CardTitle>
            <CardDescription>
              See how {config.title} will work when it's ready
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg bg-gray-50">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm font-medium">Trigger Detection</span>
                </div>
                <p className="text-xs text-gray-600">Automatically detect when {workflowType} events occur</p>
              </div>
              
              <div className="flex justify-center">
                <div className="w-px h-6 bg-gray-300"></div>
              </div>
              
              <div className="p-4 border rounded-lg bg-gray-50">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium">Smart Processing</span>
                </div>
                <p className="text-xs text-gray-600">AI-powered analysis and decision making</p>
              </div>
              
              <div className="flex justify-center">
                <div className="w-px h-6 bg-gray-300"></div>
              </div>
              
              <div className="p-4 border rounded-lg bg-gray-50">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-sm font-medium">Automated Action</span>
                </div>
                <p className="text-xs text-gray-600">Execute the appropriate response or task</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Development Status</CardTitle>
            <CardDescription>Track our progress on this workflow</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Core Architecture</span>
                <Badge variant="default">Complete</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">UI Design</span>
                <Badge variant="outline">In Progress</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">{config.title} Logic</span>
                <Badge variant="secondary">Planned</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Testing & QA</span>
                <Badge variant="secondary">Planned</Badge>
              </div>
              
              <div className="mt-6 pt-4 border-t">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Overall Progress</span>
                  <span className="text-sm text-gray-600">25%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '25%' }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default WorkflowsPage


