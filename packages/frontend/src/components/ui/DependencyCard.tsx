import React from 'react';
import { ExternalLink, FileText, Book, Key, Edit, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Dependency } from '../../services/dependencyApi';

interface DependencyCardProps {
  dependency: Dependency;
  onEdit?: (dependency: Dependency) => void;
  onDelete?: (dependency: Dependency) => void;
  showAdminActions?: boolean;
}

export const DependencyCard: React.FC<DependencyCardProps> = ({
  dependency,
  onEdit,
  onDelete,
  showAdminActions = false
}) => {
  const handleLinkClick = (url: string | undefined) => {
    if (url) {
      // Check if the URL is valid
      try {
        new URL(url);
        window.open(url, '_blank', 'noopener,noreferrer');
      } catch (error) {
        // If URL is invalid, show an alert or handle gracefully
        console.error('Invalid URL:', url);
        alert('Invalid documentation link. Please contact your administrator.');
      }
    }
  };

  const hasLinks = dependency.where_to_get || dependency.guide_link || dependency.documentation_link;

  return (
    <Card className="h-full flex flex-col hover:shadow-md transition-shadow duration-200">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {dependency.platform_name}
            </CardTitle>
            {dependency.description && (
              <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
                {dependency.description}
              </CardDescription>
            )}
          </div>
          {showAdminActions && (
            <div className="flex gap-2 ml-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit?.(dependency)}
                className="h-8 w-8 p-0"
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete?.(dependency)}
                className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-grow flex flex-col">
        {hasLinks ? (
          <div className="space-y-3 flex-grow">
            {dependency.where_to_get && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Key className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Get API Keys
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleLinkClick(dependency.where_to_get)}
                  className="w-full justify-start text-left h-auto p-3 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/30"
                >
                  <ExternalLink className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span className="text-xs text-blue-700 dark:text-blue-300 truncate">
                    {dependency.where_to_get}
                  </span>
                </Button>
              </div>
            )}

            {dependency.guide_link && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Step-by-Step Guide
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleLinkClick(dependency.guide_link)}
                  className="w-full justify-start text-left h-auto p-3 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:hover:bg-green-900/30"
                >
                  <ExternalLink className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span className="text-xs text-green-700 dark:text-green-300 truncate">
                    View Tutorial
                  </span>
                </Button>
              </div>
            )}

            {dependency.documentation_link && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Book className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Documentation
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleLinkClick(dependency.documentation_link)}
                  className="w-full justify-start text-left h-auto p-3 bg-purple-50 hover:bg-purple-100 dark:bg-purple-900/20 dark:hover:bg-purple-900/30"
                >
                  <ExternalLink className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span className="text-xs text-purple-700 dark:text-purple-300 truncate">
                    Read Docs
                  </span>
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-grow flex items-center justify-center">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No links available</p>
            </div>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Badge variant="secondary" className="text-xs">
            {dependency.platform_name}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};