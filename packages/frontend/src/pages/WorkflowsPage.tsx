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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { toast } from 'sonner'
import { MoreHorizontal, Clock } from 'lucide-react'

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
  const [editing, setEditing] = React.useState<WorkflowListItem | null>(null)
  const [minutes, setMinutes] = React.useState<number>(30)
  const clientId = isAdmin && clientFilter && clientFilter !== 'all' ? Number(clientFilter) : undefined

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
    enabled: isAdmin,
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['workflows', clientId ?? 'mine'],
    queryFn: () => (isAdmin ? WorkflowsApi.listAll(clientId) : WorkflowsApi.listMine()),
  })

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
        {isAdmin && (
          <div className="flex items-center space-x-2">
            <Select value={clientFilter} onValueChange={setClientFilter}>
              <SelectTrigger className="w-64"><SelectValue placeholder="Filter by client" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All clients</SelectItem>
                {clients?.map((c: any) => (
                  <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
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
            {data?.workflows?.map((wf) => (
              <TableRow key={wf.id}>
                {isAdmin && <TableCell className="font-medium">{wf.client_name}</TableCell>}
                <TableCell className="font-medium">{wf.workflow_name}</TableCell>
                <TableCell>{wf.active ? 'Active' : 'Inactive'}</TableCell>
                <TableCell className="text-right">{wf.total_executions}</TableCell>
                <TableCell className="text-right">{wf.success_rate}%</TableCell>
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


