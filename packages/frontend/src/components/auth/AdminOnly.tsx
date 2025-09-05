import React from 'react';
import { useIsAdmin } from '@/hooks/useAuth';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Shield } from 'lucide-react';

interface AdminOnlyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  hideWhenNotAdmin?: boolean;
}

export const AdminOnly: React.FC<AdminOnlyProps> = ({ 
  children, 
  fallback, 
  hideWhenNotAdmin = false 
}) => {
  const isAdmin = useIsAdmin();

  if (!isAdmin) {
    if (hideWhenNotAdmin) {
      return null;
    }
    
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Alert className="border-orange-200 bg-orange-50 dark:bg-orange-900/20">
        <Shield className="h-4 w-4 text-orange-600" />
        <AlertDescription className="text-orange-800 dark:text-orange-200">
          This feature is only available to administrators. Please contact your admin for access.
        </AlertDescription>
      </Alert>
    );
  }

  return <>{children}</>;
};

interface AdminButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  fallbackText?: string;
}

export const AdminButton: React.FC<AdminButtonProps> = ({ 
  children, 
  fallbackText = "Admin Only", 
  disabled,
  ...props 
}) => {
  const isAdmin = useIsAdmin();

  return (
    <button
      {...props}
      disabled={disabled || !isAdmin}
      title={!isAdmin ? fallbackText : props.title}
    >
      {children}
    </button>
  );
};

export default AdminOnly;
