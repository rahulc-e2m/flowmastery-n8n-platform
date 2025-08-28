import React from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Timer,
  TrendingUp, 
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'

interface ClientMetricsCardProps {
  client: {
    client_id: number
    client_name: string
    total_workflows: number
    active_workflows: number
    total_executions: number
    success_rate: number
    last_activity?: string
    avg_execution_time?: number
    time_saved_hours?: number
  }
  index: number
  onClick?: () => void
}

export function ClientMetricsCard({ client, index, onClick }: ClientMetricsCardProps) {
  const successRate = client.success_rate || 0
  const isHighPerformance = successRate >= 90
  const isMediumPerformance = successRate >= 70
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ scale: 1.02, y: -4 }}
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card className="group relative overflow-hidden border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-lg">
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <motion.div 
                className="w-12 h-12 bg-gradient-to-br from-primary/20 to-accent/20 rounded-xl flex items-center justify-center"
                whileHover={{ rotate: 5, scale: 1.1 }}
              >
                <Activity className="w-6 h-6 text-primary" />
              </motion.div>
              <div>
                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  {client.client_name}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Client ID: {client.client_id}
                </p>
              </div>
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="text-center">
              <p className="text-xl font-bold text-foreground">{client.total_workflows}</p>
              <p className="text-xs text-muted-foreground">Workflows</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-foreground">{client.total_executions.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Executions</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-orange-600">{client.time_saved_hours ? `${client.time_saved_hours}h` : '0h'}</p>
              <p className="text-xs text-muted-foreground">Time Saved</p>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium">{client.active_workflows} active</span>
            </div>
            <Badge 
              variant={isHighPerformance ? 'default' : isMediumPerformance ? 'secondary' : 'destructive'}
              className="font-medium"
            >
              {successRate.toFixed(1)}% success
            </Badge>
          </div>

          {/* Performance Indicator */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-1">
              {successRate >= 90 ? (
                <TrendingUp className="w-3 h-3 text-green-500" />
              ) : successRate >= 70 ? (
                <TrendingUp className="w-3 h-3 text-yellow-500" />
              ) : (
                <TrendingDown className="w-3 h-3 text-red-500" />
              )}
              <span className={`font-medium ${
                successRate >= 90 ? 'text-green-600' : 
                successRate >= 70 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {successRate >= 90 ? 'Excellent' : successRate >= 70 ? 'Good' : 'Needs Attention'}
              </span>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">
                {client.last_activity ? 
                  formatDistanceToNow(new Date(client.last_activity), { addSuffix: true }) : 
                  'No recent activity'
                }
              </p>
            </div>
          </div>

          {/* Average Execution Time */}
          {client.avg_execution_time && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Avg Time</span>
                </div>
                <span className="font-medium text-foreground">
                  {client.avg_execution_time.toFixed(2)}s
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}