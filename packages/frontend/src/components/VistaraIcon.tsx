import React from 'react'
import VistaraLogoSvg from '../../assests/footer-logo.svg'

interface VistaraIconProps {
  className?: string
  isLogoOnly?: boolean
  width?: number
  height?: number
}

// Custom Vistara Icon component to handle SVG sizing
export const VistaraIcon = ({ 
  className, 
  isLogoOnly = false, 
  width, 
  height 
}: VistaraIconProps) => (
  <img 
    src={VistaraLogoSvg} 
    alt="Vistara" 
    className={className} 
    style={{ 
      width: width ? `${width}px` : (isLogoOnly ? '120px' : '16px'), 
      height: height ? `${height}px` : (isLogoOnly ? 'auto' : '16px'),
      maxHeight: isLogoOnly ? '32px' : '16px'
    }} 
  />
)
