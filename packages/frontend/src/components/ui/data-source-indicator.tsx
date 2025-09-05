
import { formatDistanceToNow } from 'date-fns'
import { Clock, CheckCircle2, AlertTriangle, XCircle, Wifi } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface DataSourceIndicatorProps {
  /** Last updated timestamp */
  lastUpdated?: string | Date | null
  /** Display variant */
  variant?: 'full' | 'compact' | 'icon' | 'minimal'
  /** Whether to show in compact mode (for topbar) - deprecated, use variant */
  compact?: boolean
  /** Custom className */
  className?: string
  /** Show debug info (timestamp details) */
  debug?: boolean
}

export function DataSourceIndicator({
  lastUpdated,
  variant = 'full',
  compact = false,
  className = '',
  debug = false
}: DataSourceIndicatorProps) {
  // Handle legacy compact prop
  const displayVariant = compact ? 'compact' : variant

  const getLastUpdatedText = () => {
    if (!lastUpdated) return 'Never'

    try {
      const date = new Date(lastUpdated)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        if (debug) {
          console.warn('Invalid date in DataSourceIndicator:', lastUpdated)
        }
        return 'Invalid date'
      }
      
      // formatDistanceToNow already handles timezone properly by comparing to local time
      return formatDistanceToNow(date, { addSuffix: true })
    } catch (error) {
      if (debug) {
        console.error('Error parsing date in DataSourceIndicator:', error, lastUpdated)
      }
      return 'Unknown'
    }
  }

  const getDataFreshness = () => {
    if (!lastUpdated) {
      return {
        status: 'never',
        color: 'text-destructive',
        bgColor: 'bg-destructive/10',
        borderColor: 'border-destructive/20',
        icon: XCircle,
        pulse: false
      }
    }

    try {
      const date = new Date(lastUpdated)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return {
          status: 'error',
          color: 'text-destructive',
          bgColor: 'bg-destructive/10',
          borderColor: 'border-destructive/20',
          icon: XCircle,
          pulse: false
        }
      }
      
      // Calculate time difference properly - both dates are already in local timezone
      const now = new Date()
      const minutesAgo = (now.getTime() - date.getTime()) / (1000 * 60)

      if (minutesAgo <= 15) {
        return {
          status: 'fresh',
          color: 'text-success dark:text-success',
          bgColor: 'bg-success/10',
          borderColor: 'border-success/20',
          icon: CheckCircle2,
          pulse: true
        }
      } else if (minutesAgo <= 60) {
        return {
          status: 'stale',
          color: 'text-warning dark:text-warning',
          bgColor: 'bg-warning/10',
          borderColor: 'border-warning/20',
          icon: AlertTriangle,
          pulse: false
        }
      } else {
        return {
          status: 'old',
          color: 'text-muted-foreground',
          bgColor: 'bg-muted/50',
          borderColor: 'border-muted',
          icon: Clock,
          pulse: false
        }
      }
    } catch (error) {
      return {
        status: 'error',
        color: 'text-destructive',
        bgColor: 'bg-destructive/10',
        borderColor: 'border-destructive/20',
        icon: XCircle,
        pulse: false
      }
    }
  }

  const freshness = getDataFreshness()
  const StatusIcon = freshness.icon
  const timeText = getLastUpdatedText()

  // Don't render anything for compact variant (topbar)
  if (displayVariant === 'compact') {
    return null
  }

  // Icon only variant
  if (displayVariant === 'icon') {
    return (
      <motion.div
        className={cn(
          'flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200',
          freshness.bgColor,
          freshness.borderColor,
          'border backdrop-blur-sm',
          className
        )}
        animate={freshness.pulse ? { scale: [1, 1.05, 1] } : {}}
        transition={freshness.pulse ? { duration: 2, repeat: Infinity } : {}}
        title={`Data ${timeText.toLowerCase()}`}
      >
        <StatusIcon className={cn('w-4 h-4', freshness.color)} />
      </motion.div>
    )
  }

  // Minimal variant
  if (displayVariant === 'minimal') {
    return (
      <motion.div
        className={cn(
          'flex items-center space-x-2 px-2 py-1 rounded-md transition-all duration-200',
          freshness.bgColor,
          className
        )}
        animate={freshness.pulse ? { opacity: [0.7, 1, 0.7] } : {}}
        transition={freshness.pulse ? { duration: 2, repeat: Infinity } : {}}
      >
        <StatusIcon className={cn('w-3 h-3', freshness.color)} />
        <span className={cn('text-xs font-medium', freshness.color)}>
          {timeText}
        </span>
      </motion.div>
    )
  }

  // Full variant (default)
  return (
    <motion.div
      className={cn(
        'flex items-center space-x-3 px-4 py-2 rounded-xl transition-all duration-300',
        freshness.bgColor,
        freshness.borderColor,
        'border backdrop-blur-sm shadow-sm hover:shadow-md',
        'group cursor-default',
        className
      )}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ 
        opacity: 1, 
        scale: 1,
        ...(freshness.pulse ? { boxShadow: ['0 0 0 0 rgba(34, 197, 94, 0.4)', '0 0 0 8px rgba(34, 197, 94, 0)', '0 0 0 0 rgba(34, 197, 94, 0)'] } : {})
      }}
      transition={{ 
        opacity: { duration: 0.2 },
        scale: { duration: 0.2 },
        ...(freshness.pulse ? { boxShadow: { duration: 2, repeat: Infinity } } : {})
      }}
    >
      <div className="flex items-center space-x-2">
        <motion.div
          animate={freshness.pulse ? { rotate: [0, 360] } : {}}
          transition={freshness.pulse ? { duration: 2, repeat: Infinity, ease: 'linear' } : {}}
        >
          <StatusIcon className={cn('w-4 h-4', freshness.color)} />
        </motion.div>
        <div className="flex flex-col">
          <span className={cn('text-sm font-medium', freshness.color)}>
            Data {freshness.status === 'fresh' ? 'Live' : 'Updated'}
          </span>
          <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
            {timeText}
          </span>
        </div>
      </div>
      
      {freshness.status === 'fresh' && (
        <motion.div
          className="flex items-center space-x-1 px-2 py-1 bg-success/20 rounded-md"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Wifi className="w-3 h-3 text-success" />
          <span className="text-xs font-medium text-success">Live</span>
        </motion.div>
      )}
      

    </motion.div>
  )
}

export default DataSourceIndicator