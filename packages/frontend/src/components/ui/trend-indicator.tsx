import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

interface TrendIndicatorProps {
  value?: number | null
  /**
   * Whether the trend represents a positive change (green) or negative (red)
   * For metrics like error rate, a negative trend is actually positive
   */
  isPositive?: boolean
  /**
   * Override the automatic positive/negative detection
   */
  inverseLogic?: boolean
  /**
   * Display size variant
   */
  size?: 'sm' | 'md' | 'lg'
  /**
   * Show the value as percentage
   */
  showValue?: boolean
  /**
   * Custom className
   */
  className?: string
  /**
   * Hide the icon
   */
  hideIcon?: boolean
  /**
   * Prefix text (e.g., "vs last week")
   */
  prefix?: string
}

export function TrendIndicator({
  value,
  isPositive,
  inverseLogic = false,
  size = 'sm',
  showValue = true,
  className,
  hideIcon = false,
  prefix
}: TrendIndicatorProps) {
  // Safely handle the trend value
  const safeTrend = React.useMemo(() => {
    if (value === null || value === undefined || isNaN(value)) {
      return 0
    }
    // Cap extreme values to prevent display issues
    if (value > 500) return 500
    if (value < -100) return -100
    return value
  }, [value])

  // Determine if this is actually positive or negative
  const actuallyPositive = React.useMemo(() => {
    if (isPositive !== undefined) {
      return isPositive
    }
    // If inverseLogic is true, negative values are good (e.g., error rate decrease)
    if (inverseLogic) {
      return safeTrend <= 0
    }
    return safeTrend >= 0
  }, [safeTrend, isPositive, inverseLogic])

  // Determine the icon to show
  const TrendIcon = React.useMemo(() => {
    if (Math.abs(safeTrend) < 0.01) {
      return Minus
    }
    return safeTrend > 0 ? TrendingUp : TrendingDown
  }, [safeTrend])

  // Size classes
  const sizeClasses = {
    sm: {
      container: 'text-xs',
      icon: 'w-3 h-3',
      value: 'text-xs'
    },
    md: {
      container: 'text-sm',
      icon: 'w-4 h-4',
      value: 'text-sm'
    },
    lg: {
      container: 'text-base',
      icon: 'w-5 h-5',
      value: 'text-base'
    }
  }

  const sizes = sizeClasses[size]

  // Color classes based on positive/negative
  const colorClass = actuallyPositive 
    ? 'text-green-600 dark:text-green-400' 
    : 'text-red-600 dark:text-red-400'

  // Format the display value
  const displayValue = React.useMemo(() => {
    const absValue = Math.abs(safeTrend)
    // Round to 1 decimal place for cleaner display
    return absValue.toFixed(1).replace(/\.0$/, '')
  }, [safeTrend])

  // Don't render if no value
  if (value === null || value === undefined) {
    return null
  }

  // Don't render if value is effectively zero
  if (Math.abs(safeTrend) < 0.01) {
    return (
      <span className={cn(sizes.container, 'text-muted-foreground', className)}>
        {!hideIcon && <Minus className={cn(sizes.icon, 'inline mr-1')} />}
        {showValue && <span className={sizes.value}>No change</span>}
      </span>
    )
  }

  return (
    <motion.div 
      className={cn(
        'inline-flex items-center font-medium',
        sizes.container,
        colorClass,
        className
      )}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      {!hideIcon && (
        <TrendIcon className={cn(sizes.icon, 'mr-1')} />
      )}
      {showValue && (
        <span className={sizes.value}>
          {prefix && <span className="text-muted-foreground mr-1">{prefix}</span>}
          {safeTrend > 0 && '+'}
          {displayValue}%
        </span>
      )}
    </motion.div>
  )
}

// Compound component for metric cards
interface MetricTrendProps extends TrendIndicatorProps {
  label?: string
}

export function MetricTrend({ label, ...props }: MetricTrendProps) {
  return (
    <div className="flex items-center justify-between mt-2">
      {label && (
        <span className="text-xs text-muted-foreground">{label}</span>
      )}
      <TrendIndicator {...props} />
    </div>
  )
}
