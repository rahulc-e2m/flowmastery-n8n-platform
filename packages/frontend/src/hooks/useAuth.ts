import { useContext } from 'react';
import { AuthContext } from '@/contexts/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useIsAdmin = (): boolean => {
  const { user } = useAuth();
  return user?.role === 'admin';
};

export const useCanManageGuides = (): boolean => {
  return useIsAdmin(); // Only admins can manage guides based on backend changes
};

export const useCanManageClients = (): boolean => {
  return useIsAdmin(); // Only admins can manage clients
};

export const useCanViewAdminMetrics = (): boolean => {
  return useIsAdmin(); // Only admins can view admin metrics
};

export default useAuth;
