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
import { MoreHorizontal, Clock, Search, X, MessageCircle, Mail, Calendar, FileText, Bot, ArrowLeft, ExternalLink } from 'lucide-react'
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
  const clientId = isAdmin && clientFilter && clientFilter !== 'all' ? Number(clientFilter) : undefined

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

// Workflow Interface Component for different workflow types
function WorkflowInterface({ workflowType }: { workflowType: string }) {
  const workflowConfigs = {
    chatbot: {
      title: 'Chatbot Workflows',
      description: 'Create and manage AI-powered chatbot interfaces',
      icon: MessageCircle,
      color: 'bg-blue-500',
      features: [
        'AI-powered conversation flows',
        'Multi-platform deployment',
        'Custom training data integration',
        'Real-time analytics and insights'
      ],
      templates: [
        {
          name: 'Customer Support Bot',
          description: 'Handle common customer inquiries automatically',
          setupTime: '15 minutes',
          complexity: 'Beginner'
        },
        {
          name: 'Lead Qualification Bot',
          description: 'Qualify leads through interactive conversations',
          setupTime: '30 minutes',
          complexity: 'Intermediate'
        },
        {
          name: 'FAQ Assistant',
          description: 'Instant answers to frequently asked questions',
          setupTime: '10 minutes',
          complexity: 'Beginner'
        }
      ]
    },
    email: {
      title: 'Email Automation',
      description: 'Design sophisticated email marketing and automation sequences',
      icon: Mail,
      color: 'bg-green-500',
      features: [
        'Drag-and-drop email builder',
        'A/B testing capabilities',
        'Advanced segmentation',
        'Behavioral triggers'
      ],
      templates: [
        {
          name: 'Welcome Series',
          description: 'Onboard new subscribers with a warm welcome sequence',
          setupTime: '20 minutes',
          complexity: 'Beginner'
        },
        {
          name: 'Abandoned Cart Recovery',
          description: 'Recover lost sales with strategic reminder emails',
          setupTime: '25 minutes',
          complexity: 'Intermediate'
        },
        {
          name: 'Re-engagement Campaign',
          description: 'Win back inactive subscribers',
          setupTime: '30 minutes',
          complexity: 'Advanced'
        }
      ]
    },
    calendar: {
      title: 'Calendar Integration',
      description: 'Streamline scheduling and booking processes',
      icon: Calendar,
      color: 'bg-purple-500',
      features: [
        'Smart scheduling algorithms',
        'Multi-calendar sync',
        'Automated reminders',
        'Time zone handling'
      ],
      templates: [
        {
          name: 'Meeting Scheduler',
          description: 'Allow clients to book meetings automatically',
          setupTime: '15 minutes',
          complexity: 'Beginner'
        },
        {
          name: 'Event Registration',
          description: 'Manage event registrations and capacity',
          setupTime: '25 minutes',
          complexity: 'Intermediate'
        },
        {
          name: 'Resource Booking',
          description: 'Book rooms, equipment, and other resources',
          setupTime: '35 minutes',
          complexity: 'Advanced'
        }
      ]
    },
    documents: {
      title: 'Document Processing',
      description: 'Automate document creation, processing, and management',
      icon: FileText,
      color: 'bg-orange-500',
      features: [
        'OCR and text extraction',
        'Template generation',
        'Digital signatures',
        'Workflow approvals'
      ],
      templates: [
        {
          name: 'Invoice Generator',
          description: 'Automatically generate and send invoices',
          setupTime: '20 minutes',
          complexity: 'Intermediate'
        },
        {
          name: 'Contract Workflow',
          description: 'Streamline contract creation and approval',
          setupTime: '40 minutes',
          complexity: 'Advanced'
        },
        {
          name: 'Report Automation',
          description: 'Generate periodic reports automatically',
          setupTime: '30 minutes',
          complexity: 'Intermediate'
        }
      ]
    },
    custom: {
      title: 'Custom Workflows',
      description: 'Build completely custom automation workflows',
      icon: Bot,
      color: 'bg-indigo-500',
      features: [
        'Visual workflow builder',
        'Custom integrations',
        'Advanced logic flows',
        'API connections'
      ],
      templates: [
        {
          name: 'Data Sync Workflow',
          description: 'Sync data between different platforms',
          setupTime: '45 minutes',
          complexity: 'Advanced'
        },
        {
          name: 'Notification System',
          description: 'Create complex notification workflows',
          setupTime: '25 minutes',
          complexity: 'Intermediate'
        },
        {
          name: 'Multi-step Process',
          description: 'Build complex multi-step business processes',
          setupTime: '60 minutes',
          complexity: 'Expert'
        }
      ]
    }
  }

  const config = workflowConfigs[workflowType as keyof typeof workflowConfigs]
  const IconComponent = config.icon

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Beginner': return 'bg-green-100 text-green-800'
      case 'Intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'Advanced': return 'bg-orange-100 text-orange-800'
      case 'Expert': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="p-6 space-y-6">
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
              className={`p-3 rounded-xl ${config.color} text-white`}
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
        <Button className="flex items-center space-x-2">
          <ExternalLink className="w-4 h-4" />
          <span>Open n8n Editor</span>
        </Button>
      </div>

      {/* Features Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Key Features</CardTitle>
          <CardDescription>What you can accomplish with this workflow type</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {config.features.map((feature, index) => (
              <motion.div 
                key={feature}
                className="p-4 border rounded-lg text-center hover:shadow-md transition-shadow"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <p className="text-sm font-medium">{feature}</p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Ready-to-Use Templates</CardTitle>
          <CardDescription>Start with these pre-built templates and customize as needed</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {config.templates.map((template, index) => (
              <motion.div 
                key={template.name}
                className="border rounded-lg p-6 hover:shadow-lg transition-all duration-200 cursor-pointer group"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -4 }}
              >
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold group-hover:text-primary transition-colors">
                      {template.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-2">
                      {template.description}
                    </p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">{template.setupTime}</span>
                    </div>
                    <Badge className={getComplexityColor(template.complexity)}>
                      {template.complexity}
                    </Badge>
                  </div>
                  
                  <Button className="w-full" variant="outline">
                    Use Template
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Getting Started Guide */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>Follow these steps to create your first workflow</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                1
              </div>
              <div>
                <h4 className="font-medium">Choose a Template</h4>
                <p className="text-sm text-muted-foreground">Select one of the pre-built templates above or start from scratch</p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                2
              </div>
              <div>
                <h4 className="font-medium">Customize the Workflow</h4>
                <p className="text-sm text-muted-foreground">Use our visual editor to modify the workflow to match your needs</p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-semibold">
                3
              </div>
              <div>
                <h4 className="font-medium">Test and Deploy</h4>
                <p className="text-sm text-muted-foreground">Test your workflow and deploy it to start automation</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default WorkflowsPage


