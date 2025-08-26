import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: 'success' | 'error' | 'warning' | 'pending' | 'info'
  text?: string
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  showIcon?: boolean
}

export function StatusBadge({ 
  status, 
  text, 
  size = 'md', 
  animated = true,
  showIcon = true 
}: StatusBadgeProps) {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    pending: Clock,
    info: CheckCircle
  }
  
  const statusConfig = {
    success: {
      className: 'status-success',
      defaultText: 'Success'
    },
    error: {
      className: 'status-error',
      defaultText: 'Error'
    },
    warning: {
      className: 'status-warning',
      defaultText: 'Warning'
    },
    pending: {
      className: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
      defaultText: 'Pending'
    },
    info: {
      className: 'status-info',
      defaultText: 'Info'
    }
  }
  
  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  }
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  }

  const Icon = icons[status]
  const config = statusConfig[status]
  const displayText = text || config.defaultText

  const BadgeContent = () => (
    <>
      {showIcon && (
        <Icon className={cn(iconSizes[size], text && 'mr-1.5')} />
      )}
      {text && <span>{displayText}</span>}
    </>
  )

  if (!animated) {
    return (
      <span className={cn(
        'inline-flex items-center rounded-full border font-medium',
        sizes[size],
        config.className
      )}>
        <BadgeContent />
      </span>
    )
  }

  return (
    <motion.span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        sizes[size],
        config.className
      )}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ 
        type: 'spring', 
        stiffness: 200, 
        damping: 15,
        delay: Math.random() * 0.2 
      }}
      whileHover={{ scale: 1.05 }}
    >
      <BadgeContent />
    </motion.span>
  )
}