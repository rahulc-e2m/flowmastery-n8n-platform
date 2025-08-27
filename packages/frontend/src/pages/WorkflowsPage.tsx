import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { WorkflowsApi, type WorkflowListItem } from '@/services/workflowsApi'
import { ClientApi } from '@/services/clientApi'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'sonner'
import { MoreHorizontal, Clock, Search, X } from 'lucide-react'

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

export function WorkflowsPage() {
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
                    {wf.success_rate}%
                  </span>
                </TableCell>
                <TableCell className="text-right">{wf.last_execution ? new Date(wf.last_execution).toLocaleString() : '-'}</TableCell>
                <TableCell className="text-right flex items-center justify-end space-x-1">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span>{Math.floor((wf.time_saved_per_execution_minutes || 0)/60)}h {(wf.time_saved_per_execution_minutes||0)%60}m</span>
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
                <TableCell colSpan={isAdmin ? 8 : 7} className="text-center py-8 text-gray-500">
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

export default WorkflowsPage


