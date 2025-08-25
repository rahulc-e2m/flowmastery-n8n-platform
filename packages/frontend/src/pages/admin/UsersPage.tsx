import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AuthApi } from '@/services/authApi'
import { ClientApi } from '@/services/clientApi'
import { 
  UserPlus, 
  Mail, 
  Clock, 
  CheckCircle, 
  XCircle,
  Copy,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'
import type { InvitationCreate } from '@/types/auth'

const invitationSchema = z.object({
  email: z.string().email('Invalid email address'),
  role: z.enum(['admin', 'client'], { required_error: 'Role is required' }),
  client_id: z.number().optional(),
})

type InvitationFormData = z.infer<typeof invitationSchema>

export function UsersPage() {
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: invitations, isLoading: invitationsLoading } = useQuery({
    queryKey: ['invitations'],
    queryFn: AuthApi.getInvitations,
  })

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
  })

  const createInvitationMutation = useMutation({
    mutationFn: AuthApi.createInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] })
      setInviteDialogOpen(false)
      reset()
      toast.success('Invitation sent successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to send invitation')
    },
  })

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
    reset,
  } = useForm<InvitationFormData>({
    resolver: zodResolver(invitationSchema),
  })

  const selectedRole = watch('role')

  const onSubmit = (data: InvitationFormData) => {
    const invitationData: InvitationCreate = {
      email: data.email,
      role: data.role,
      client_id: data.role === 'client' ? data.client_id : undefined,
    }
    createInvitationMutation.mutate(invitationData)
  }

  const copyInvitationLink = (token: string) => {
    const link = `${window.location.origin}/accept-invitation?token=${token}`
    navigator.clipboard.writeText(link)
    toast.success('Invitation link copied to clipboard')
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Pending</Badge>
      case 'accepted':
        return <Badge variant="default"><CheckCircle className="w-3 h-3 mr-1" />Accepted</Badge>
      case 'expired':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Expired</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const pendingInvitations = invitations?.filter(inv => inv.status === 'pending') || []
  const acceptedInvitations = invitations?.filter(inv => inv.status === 'accepted') || []
  const expiredInvitations = invitations?.filter(inv => inv.status === 'expired') || []

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Users & Invitations</h1>
          <p className="text-muted-foreground mt-2">Manage user invitations and access</p>
        </div>
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => reset()}>
              <UserPlus className="w-4 h-4 mr-2" />
              Send Invitation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Send User Invitation</DialogTitle>
              <DialogDescription>
                Invite a new user to join the platform. They will receive an email with setup instructions.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="user@example.com"
                  {...register('email')}
                  className={errors.email ? 'border-red-500' : ''}
                />
                {errors.email && (
                  <p className="text-sm text-red-500">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Controller
                  name="role"
                  control={control}
                  render={({ field }) => (
                    <Select onValueChange={field.onChange} value={field.value}>
                      <SelectTrigger className={errors.role ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="client">Client</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
                {errors.role && (
                  <p className="text-sm text-red-500">{errors.role.message}</p>
                )}
              </div>

              {selectedRole === 'client' && (
                <div className="space-y-2">
                  <Label htmlFor="client_id">Client</Label>
                  <Controller
                    name="client_id"
                    control={control}
                    render={({ field }) => (
                      <Select onValueChange={(value) => field.onChange(parseInt(value))} value={field.value?.toString()}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a client" />
                        </SelectTrigger>
                        <SelectContent>
                          {clients?.map((client) => (
                            <SelectItem key={client.id} value={client.id.toString()}>
                              {client.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setInviteDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createInvitationMutation.isPending}>
                  {createInvitationMutation.isPending ? 'Sending...' : 'Send Invitation'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">
            Pending ({pendingInvitations.length})
          </TabsTrigger>
          <TabsTrigger value="accepted">
            Accepted ({acceptedInvitations.length})
          </TabsTrigger>
          <TabsTrigger value="expired">
            Expired ({expiredInvitations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Pending Invitations</CardTitle>
              <CardDescription>
                Invitations that have been sent but not yet accepted
              </CardDescription>
            </CardHeader>
            <CardContent>
              {invitationsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="animate-pulse flex space-x-4">
                      <div className="rounded-full bg-muted h-10 w-10"></div>
                      <div className="flex-1 space-y-2 py-1">
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                        <div className="h-4 bg-muted rounded w-1/2"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : pendingInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Mail className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No pending invitations</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Expires</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingInvitations.map((invitation) => (
                      <TableRow key={invitation.id}>
                        <TableCell className="font-medium">{invitation.email}</TableCell>
                        <TableCell>
                          <Badge variant={invitation.role === 'admin' ? 'default' : 'secondary'}>
                            {invitation.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invitation.client_id ? (
                            clients?.find(c => c.id === invitation.client_id)?.name || 'Unknown'
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          {formatDistanceToNow(new Date(invitation.expiry_date), { addSuffix: true })}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyInvitationLink(invitation.id.toString())}
                          >
                            <Copy className="w-4 h-4 mr-2" />
                            Copy Link
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accepted">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Accepted Invitations</CardTitle>
              <CardDescription>
                Users who have successfully joined the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {acceptedInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No accepted invitations</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Accepted</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {acceptedInvitations.map((invitation) => (
                      <TableRow key={invitation.id}>
                        <TableCell className="font-medium">{invitation.email}</TableCell>
                        <TableCell>
                          <Badge variant={invitation.role === 'admin' ? 'default' : 'secondary'}>
                            {invitation.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invitation.client_id ? (
                            clients?.find(c => c.id === invitation.client_id)?.name || 'Unknown'
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          {formatDistanceToNow(new Date(invitation.created_at), { addSuffix: true })}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="expired">
          <Card className="admin-card">
            <CardHeader>
              <CardTitle>Expired Invitations</CardTitle>
              <CardDescription>
                Invitations that have expired and can no longer be used
              </CardDescription>
            </CardHeader>
            <CardContent>
              {expiredInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <XCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No expired invitations</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Expired</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {expiredInvitations.map((invitation) => (
                      <TableRow key={invitation.id}>
                        <TableCell className="font-medium">{invitation.email}</TableCell>
                        <TableCell>
                          <Badge variant={invitation.role === 'admin' ? 'default' : 'secondary'}>
                            {invitation.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invitation.client_id ? (
                            clients?.find(c => c.id === invitation.client_id)?.name || 'Unknown'
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          {formatDistanceToNow(new Date(invitation.expiry_date), { addSuffix: true })}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}