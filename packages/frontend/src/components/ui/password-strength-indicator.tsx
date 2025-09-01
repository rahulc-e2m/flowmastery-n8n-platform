import React from 'react'
import { Check, X } from 'lucide-react'
import { 
  validatePasswordStrength, 
  getPasswordStrengthLabel, 
  getPasswordStrengthColor,
  getPasswordStrengthBarColor,
  type PasswordStrength 
} from '@/lib/password'

interface PasswordStrengthIndicatorProps {
  password: string
  showRequirements?: boolean
  className?: string
}

export function PasswordStrengthIndicator({ 
  password, 
  showRequirements = true, 
  className = '' 
}: PasswordStrengthIndicatorProps) {
  const strength = validatePasswordStrength(password)
  
  if (!password) {
    return null
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Strength Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Password Strength</span>
          <span className={`font-medium ${getPasswordStrengthColor(strength.score)}`}>
            {getPasswordStrengthLabel(strength.score)}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthBarColor(strength.score)}`}
            style={{ width: `${(strength.score / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Requirements Checklist */}
      {showRequirements && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Requirements:</p>
          <div className="grid grid-cols-1 gap-1 text-sm">
            <RequirementItem 
              met={strength.requirements.minLength}
              text="At least 12 characters"
            />
            <RequirementItem 
              met={strength.requirements.hasUppercase}
              text="One uppercase letter (A-Z)"
            />
            <RequirementItem 
              met={strength.requirements.hasLowercase}
              text="One lowercase letter (a-z)"
            />
            <RequirementItem 
              met={strength.requirements.hasDigit}
              text="One digit (0-9)"
            />
            <RequirementItem 
              met={strength.requirements.hasSpecialChar}
              text="One special character (!@#$%^&*)"
            />
          </div>
        </div>
      )}
    </div>
  )
}

interface RequirementItemProps {
  met: boolean
  text: string
}

function RequirementItem({ met, text }: RequirementItemProps) {
  return (
    <div className={`flex items-center gap-2 ${met ? 'text-green-600' : 'text-gray-500'}`}>
      {met ? (
        <Check className="w-4 h-4" />
      ) : (
        <X className="w-4 h-4" />
      )}
      <span className="text-sm">{text}</span>
    </div>
  )
}