import { formatDistanceToNow } from 'date-fns'

interface DataSourceIndicatorProps {
  /** Last updated timestamp */
  lastUpdated?: string | Date | null
  /** Whether to show in compact mode (for topbar) */
  compact?: boolean
  /** Custom className */
  className?: string
  /** Show debug info (timestamp details) */
  debug?: boolean
}

export function DataSourceIndicator({
  lastUpdated,
  compact = false,
  className = '',
  debug = false
}: DataSourceIndicatorProps) {
  const getLastUpdatedText = () => {
    if (!lastUpdated) return 'Never'

    try {
      const date = new Date(lastUpdated)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'Invalid date'
      }
      
      return formatDistanceToNow(date, { addSuffix: true })
    } catch (error) {
      return 'Unknown'
    }
  }

  const getStatusColor = () => {
    if (!lastUpdated) return 'text-red-500'

    try {
      const date = new Date(lastUpdated)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'text-red-500'
      }
      
      const now = new Date()
      const minutesAgo = (now.getTime() - date.getTime()) / (1000 * 60)

      if (minutesAgo <= 15) return 'text-green-500' // Fresh data
      if (minutesAgo <= 60) return 'text-yellow-500' // Slightly stale
      return 'text-orange-500' // Stale data
    } catch (error) {
      return 'text-red-500'
    }
  }

  if (compact) {
    // Topbar variant - hide completely
    return null
  }

  // Dashboard variant - show status-colored text
  return (
    <div className={`flex items-center ${className}`}>
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        Updated {getLastUpdatedText()}
      </span>
    </div>
  )
}

export default DataSourceIndicator