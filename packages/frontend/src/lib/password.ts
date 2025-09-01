/**
 * Password strength validation utilities
 */

export interface PasswordStrength {
  score: number // 0-5 (0 = very weak, 5 = very strong)
  feedback: string[]
  isValid: boolean
  requirements: {
    minLength: boolean
    hasUppercase: boolean
    hasLowercase: boolean
    hasDigit: boolean
    hasSpecialChar: boolean
  }
}

export const PASSWORD_REQUIREMENTS = {
  minLength: 12,
  uppercaseRegex: /[A-Z]/,
  lowercaseRegex: /[a-z]/,
  digitRegex: /\d/,
  specialCharRegex: /[!@#$%^&*(),.?":{}|<>]/
}

/**
 * Validates password strength and returns detailed feedback
 */
export function validatePasswordStrength(password: string): PasswordStrength {
  const requirements = {
    minLength: password.length >= PASSWORD_REQUIREMENTS.minLength,
    hasUppercase: PASSWORD_REQUIREMENTS.uppercaseRegex.test(password),
    hasLowercase: PASSWORD_REQUIREMENTS.lowercaseRegex.test(password),
    hasDigit: PASSWORD_REQUIREMENTS.digitRegex.test(password),
    hasSpecialChar: PASSWORD_REQUIREMENTS.specialCharRegex.test(password)
  }

  const feedback: string[] = []
  let score = 0

  // Check each requirement
  if (!requirements.minLength) {
    feedback.push(`At least ${PASSWORD_REQUIREMENTS.minLength} characters`)
  } else {
    score += 1
  }

  if (!requirements.hasUppercase) {
    feedback.push('At least one uppercase letter (A-Z)')
  } else {
    score += 1
  }

  if (!requirements.hasLowercase) {
    feedback.push('At least one lowercase letter (a-z)')
  } else {
    score += 1
  }

  if (!requirements.hasDigit) {
    feedback.push('At least one digit (0-9)')
  } else {
    score += 1
  }

  if (!requirements.hasSpecialChar) {
    feedback.push('At least one special character (!@#$%^&*(),.?":{}|<>)')
  } else {
    score += 1
  }

  // Bonus points for extra security
  if (password.length >= 16) {
    score += 0.5
  }
  if (password.length >= 20) {
    score += 0.5
  }

  const isValid = Object.values(requirements).every(req => req)

  return {
    score: Math.min(5, score),
    feedback,
    isValid,
    requirements
  }
}

/**
 * Gets password strength label based on score
 */
export function getPasswordStrengthLabel(score: number): string {
  if (score < 2) return 'Very Weak'
  if (score < 3) return 'Weak'
  if (score < 4) return 'Fair'
  if (score < 5) return 'Good'
  return 'Very Strong'
}

/**
 * Gets password strength color based on score
 */
export function getPasswordStrengthColor(score: number): string {
  if (score < 2) return 'text-red-500'
  if (score < 3) return 'text-orange-500'
  if (score < 4) return 'text-yellow-500'
  if (score < 5) return 'text-blue-500'
  return 'text-green-500'
}

/**
 * Gets password strength progress bar color based on score
 */
export function getPasswordStrengthBarColor(score: number): string {
  if (score < 2) return 'bg-red-500'
  if (score < 3) return 'bg-orange-500'
  if (score < 4) return 'bg-yellow-500'
  if (score < 5) return 'bg-blue-500'
  return 'bg-green-500'
}