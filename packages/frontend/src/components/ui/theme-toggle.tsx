import React from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTheme } from '@/contexts/ThemeContext'
import { buttonTap, scaleIn } from '@/lib/animations'

export function ThemeToggle() {
  const { theme, setTheme, actualTheme, toggleTheme, isTransitioning } = useTheme()

  const iconVariants = {
    initial: { scale: 0, rotate: -90, opacity: 0 },
    animate: { 
      scale: 1, 
      rotate: 0, 
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 200,
        damping: 15
      }
    },
    exit: { 
      scale: 0, 
      rotate: 90, 
      opacity: 0,
      transition: {
        duration: 0.2
      }
    }
  }

  const getCurrentIcon = () => {
    if (theme === 'system') return Monitor
    return actualTheme === 'dark' ? Moon : Sun
  }

  const CurrentIcon = getCurrentIcon()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <motion.div
          variants={buttonTap}
          whileTap="tap"
        >
          <Button 
            variant="ghost" 
            size="sm" 
            className={`
              w-10 h-10 p-0 rounded-lg 
              hover:bg-accent/50 
              transition-all duration-200 
              ${isTransitioning ? 'pointer-events-none' : ''}
            `}
            onClick={toggleTheme}
          >
            <div className="relative w-5 h-5 flex items-center justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${theme}-${actualTheme}`}
                  variants={iconVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  className="absolute"
                >
                  <CurrentIcon className="w-5 h-5" />
                </motion.div>
              </AnimatePresence>
            </div>
            <span className="sr-only">Toggle theme</span>
          </Button>
        </motion.div>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <motion.div
          variants={scaleIn}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <DropdownMenuItem 
            onClick={() => setTheme('light')}
            className={`
              flex items-center gap-3 px-3 py-2 cursor-pointer
              ${theme === 'light' ? 'bg-accent text-accent-foreground' : ''}
            `}
          >
            <Sun className="w-4 h-4" />
            <span>Light</span>
            {theme === 'light' && (
              <motion.div
                layoutId="theme-indicator"
                className="ml-auto w-2 h-2 bg-primary rounded-full"
              />
            )}
          </DropdownMenuItem>
          <DropdownMenuItem 
            onClick={() => setTheme('dark')}
            className={`
              flex items-center gap-3 px-3 py-2 cursor-pointer
              ${theme === 'dark' ? 'bg-accent text-accent-foreground' : ''}
            `}
          >
            <Moon className="w-4 h-4" />
            <span>Dark</span>
            {theme === 'dark' && (
              <motion.div
                layoutId="theme-indicator"
                className="ml-auto w-2 h-2 bg-primary rounded-full"
              />
            )}
          </DropdownMenuItem>
          <DropdownMenuItem 
            onClick={() => setTheme('system')}
            className={`
              flex items-center gap-3 px-3 py-2 cursor-pointer
              ${theme === 'system' ? 'bg-accent text-accent-foreground' : ''}
            `}
          >
            <Monitor className="w-4 h-4" />
            <span>System</span>
            {theme === 'system' && (
              <motion.div
                layoutId="theme-indicator"
                className="ml-auto w-2 h-2 bg-primary rounded-full"
              />
            )}
          </DropdownMenuItem>
        </motion.div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}