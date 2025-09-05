import React, { useState, useEffect } from 'react';
import { Search, BookOpen, ExternalLink, Loader2, AlertCircle, Plus } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DependencyCard } from '@/components/ui/DependencyCard';
import { dependencyApi, Dependency } from '@/services/guidesApi';
import { useCanManageGuides } from '@/hooks/useAuth';
import { AdminOnly } from '@/components/auth/AdminOnly';

export const DependenciesPage: React.FC = () => {
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredDependencies, setFilteredDependencies] = useState<Dependency[]>([]);
  const canManageGuides = useCanManageGuides();

  // Handler functions for admin actions
  const handleEditGuide = (guide: Dependency) => {
    console.log('Edit guide:', guide);
    // TODO: Implement edit guide modal/form
    alert('Edit guide functionality will be implemented soon!');
  };

  const handleDeleteGuide = async (guide: Dependency) => {
    if (window.confirm(`Are you sure you want to delete the guide for ${guide.platform_name}?`)) {
      try {
        await dependencyApi.deleteDependency(guide.id);
        // Refresh the list
        const data = await dependencyApi.getAllDependencies();
        setDependencies(data);
        alert('Guide deleted successfully!');
      } catch (error) {
        console.error('Error deleting guide:', error);
        alert('Failed to delete guide. Please try again.');
      }
    }
  };

  useEffect(() => {
    const fetchDependencies = async () => {
      try {
        setLoading(true);
        const data = await dependencyApi.getAllDependencies();
        setDependencies(data);
        setFilteredDependencies(data);
      } catch (err) {
        setError('Failed to load dependencies. Please try again later.');
        console.error('Error fetching dependencies:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDependencies();
  }, []);

  useEffect(() => {
    const filtered = dependencies.filter(dep =>
      dep.platform_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (dep.description && dep.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    setFilteredDependencies(filtered);
  }, [searchTerm, dependencies]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading dependencies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <BookOpen className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Platform Dependencies
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Step-by-step guides for setting up API keys and credentials for various platforms
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Platforms
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {dependencies.length}
                  </p>
                </div>
                <BookOpen className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    With Guides
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {dependencies.filter(d => d.guide_link).length}
                  </p>
                </div>
                <ExternalLink className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Filtered Results
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {filteredDependencies.length}
                  </p>
                </div>
                <Search className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Admin Actions */}
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search platforms (e.g., Google, OpenAI, Slack...)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <AdminOnly hideWhenNotAdmin>
            <Button className="flex-shrink-0">
              <Plus className="h-4 w-4 mr-2" />
              Add Guide
            </Button>
          </AdminOnly>
        </div>
      </div>

      {/* Dependencies Grid */}
      {filteredDependencies.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {searchTerm ? 'No matching platforms found' : 'No dependencies available'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchTerm 
                ? `No platforms match "${searchTerm}". Try a different search term.`
                : 'No platform guides have been added yet. Check back later or contact your administrator.'
              }
            </p>
            {searchTerm && (
              <Button onClick={() => setSearchTerm('')} variant="outline">
                Clear Search
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDependencies.map((dependency) => (
            <DependencyCard
              key={dependency.id}
              dependency={dependency}
              showAdminActions={canManageGuides}
              onEdit={canManageGuides ? handleEditGuide : undefined}
              onDelete={canManageGuides ? handleDeleteGuide : undefined}
            />
          ))}
        </div>
      )}

      {/* Help Text */}
      <Card className="mt-8 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="text-blue-900 dark:text-blue-100 flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            How to Use This Page
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-blue-800 dark:text-blue-200 space-y-2">
            <p>• <strong>Search:</strong> Use the search bar to quickly find specific platforms</p>
            <p>• <strong>Get API Keys:</strong> Click the blue "Get API Keys" button to visit the official platform</p>
            <p>• <strong>Step-by-Step Guide:</strong> Click the green "View Tutorial" button for detailed setup instructions</p>
            <p>• <strong>Documentation:</strong> Click the purple "Read Docs" button for official documentation</p>
            <p>• Need help? Contact your administrator if you can't find what you're looking for.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};