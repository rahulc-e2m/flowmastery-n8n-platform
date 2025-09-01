import { Variants } from 'framer-motion'

// Animation variants for consistent motion design
export const fadeInUp: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    y: -20,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const fadeInRight: Variants = {
  initial: { 
    opacity: 0, 
    x: 30 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    x: -30,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const fadeInLeft: Variants = {
  initial: { 
    opacity: 0, 
    x: -30 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    x: 30,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const scaleIn: Variants = {
  initial: { 
    opacity: 0, 
    scale: 0.95 
  },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const slideUpModal: Variants = {
  initial: { 
    opacity: 0, 
    y: 50,
    scale: 0.95 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    y: 50,
    scale: 0.95,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const cardHover: Variants = {
  rest: { 
    scale: 1,
    y: 0,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  hover: { 
    scale: 1.02,
    y: -4,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const buttonTap: Variants = {
  tap: { 
    scale: 0.95,
    transition: {
      duration: 0.1,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  }
}

export const staggerItem: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const pageTransition: Variants = {
  initial: { 
    opacity: 0, 
    x: 20 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: { 
    opacity: 0, 
    x: -20,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const navItemHover: Variants = {
  rest: { 
    x: 0,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  hover: { 
    x: 4,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1]
    }
  }
}

export const shimmer: Variants = {
  initial: { 
    backgroundPosition: '-1000px 0' 
  },
  animate: { 
    backgroundPosition: '1000px 0',
    transition: {
      duration: 2,
      ease: 'linear',
      repeat: Infinity
    }
  }
}

// Custom easing curves
export const easing = {
  easeInOut: [0.4, 0, 0.2, 1],
  easeOut: [0, 0, 0.2, 1],
  easeIn: [0.4, 0, 1, 1],
  bounce: [0.68, -0.55, 0.265, 1.55]
} as const

// Utility function for spring animations
export const spring = {
  type: 'spring',
  damping: 25,
  stiffness: 120
} as const

// Utility for creating custom delays
export const createDelayedAnimation = (delay: number, variants: Variants) => ({
  ...variants,
  animate: {
    ...(typeof variants.animate === 'object' ? variants.animate : {}),
    transition: {
      ...(typeof variants.animate === 'object' && variants.animate?.transition ? variants.animate.transition : {}),
      delay
    }
  }
})