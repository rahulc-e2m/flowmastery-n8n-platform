/**
 * Utility functions for safe number formatting
 */

/**
 * Safely format a number with toFixed
 * @param value The value to format
 * @param decimals Number of decimal places (default: 2)
 * @param fallback Fallback value if formatting fails (default: '0')
 * @returns Formatted string
 */
export function safeToFixed(
  value: number | null | undefined,
  decimals: number = 2,
  fallback: string = '0'
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return fallback
  }
  
  try {
    return value.toFixed(decimals)
  } catch {
    return fallback
  }
}

/**
 * Safely format a percentage value
 * @param value The percentage value
 * @param decimals Number of decimal places (default: 1)
 * @param includeSign Whether to include % sign (default: true)
 * @returns Formatted percentage string
 */
export function safePercentage(
  value: number | null | undefined,
  decimals: number = 1,
  includeSign: boolean = true
): string {
  const formatted = safeToFixed(value, decimals, '0')
  return includeSign ? `${formatted}%` : formatted
}

/**
 * Safely format large numbers with commas
 * @param value The value to format
 * @param fallback Fallback value if formatting fails
 * @returns Formatted string with commas
 */
export function safeNumberFormat(
  value: number | null | undefined,
  fallback: string = '0'
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return fallback
  }
  
  try {
    return value.toLocaleString()
  } catch {
    return fallback
  }
}

/**
 * Format duration in seconds to human-readable format
 * @param seconds Duration in seconds
 * @returns Formatted duration string (e.g., "2.5s", "1.2m", "1.5h")
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || isNaN(seconds)) return 'N/A'
  
  if (seconds < 60) {
    return `${safeToFixed(seconds, 1)}s`
  } else if (seconds < 3600) {
    const minutes = seconds / 60
    return `${safeToFixed(minutes, 1)}m`
  } else {
    const hours = seconds / 3600
    return `${safeToFixed(hours, 1)}h`
  }
}

/**
 * Format hours saved with proper units
 * @param hours Number of hours
 * @returns Formatted string (e.g., "2.5h", "3d", "1.2w")
 */
export function formatHoursSaved(hours: number | null | undefined): string {
  if (!hours || isNaN(hours)) return '0h'
  
  if (hours < 24) {
    return `${safeToFixed(hours, 1, '0').replace(/\.0$/, '')}h`
  } else if (hours < 168) { // Less than a week
    const days = hours / 24
    return `${safeToFixed(days, 1, '0').replace(/\.0$/, '')}d`
  } else if (hours < 730) { // Less than a month (~30 days)
    const weeks = hours / 168
    return `${safeToFixed(weeks, 1, '0').replace(/\.0$/, '')}w`
  } else {
    const months = hours / 730
    return `${safeToFixed(months, 1, '0').replace(/\.0$/, '')}mo`
  }
}

/**
 * Cap a value within bounds
 * @param value The value to cap
 * @param min Minimum value
 * @param max Maximum value
 * @returns Capped value
 */
export function capValue(
  value: number | null | undefined,
  min: number = -100,
  max: number = 500
): number {
  if (!value || isNaN(value)) return 0
  return Math.max(min, Math.min(max, value))
}

/**
 * Determine if a trend value should be considered positive
 * @param value The trend value
 * @param metric The metric type (for inverse logic)
 * @returns Whether the trend is positive
 */
export function isTrendPositive(
  value: number | null | undefined,
  metric?: 'error_rate' | 'execution_time' | 'failures'
): boolean {
  if (!value || isNaN(value)) return true // Neutral if no value
  
  // For error-related metrics, negative trends are good
  if (metric === 'error_rate' || metric === 'failures' || metric === 'execution_time') {
    return value <= 0
  }
  
  // For most metrics, positive trends are good
  return value >= 0
}
