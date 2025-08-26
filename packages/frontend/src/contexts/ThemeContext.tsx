import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  actualTheme: 'light' | 'dark'
  toggleTheme: () => void
  isTransitioning: boolean
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem('theme') as Theme
    return stored || 'system'
  })

  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('light')
  const [isTransitioning, setIsTransitioning] = useState(false)

  const updateTheme = useCallback(() => {
    setIsTransitioning(true)
    
    const root = window.document.documentElement
    let resolvedTheme: 'light' | 'dark'
    
    if (theme === 'system') {
      resolvedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    } else {
      resolvedTheme = theme
    }
    
    // Smooth transition effect
    setTimeout(() => {
      setActualTheme(resolvedTheme)
      root.classList.remove('light', 'dark')
      root.classList.add(resolvedTheme)
      
      // Allow transition animations to complete
      setTimeout(() => setIsTransitioning(false), 300)
    }, 50)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(prevTheme => {
      if (prevTheme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        return systemTheme === 'dark' ? 'light' : 'dark'
      }
      return prevTheme === 'dark' ? 'light' : 'dark'
    })
  }, [])

  useEffect(() => {
    updateTheme()

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', updateTheme)
      return () => mediaQuery.removeEventListener('change', updateTheme)
    }
  }, [theme, updateTheme])

  useEffect(() => {
    localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <ThemeContext.Provider value={{ 
      theme, 
      setTheme, 
      actualTheme, 
      toggleTheme, 
      isTransitioning 
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}