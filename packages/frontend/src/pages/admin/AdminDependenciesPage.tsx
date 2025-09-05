import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  BookOpen, 
  ExternalLink, 
  Loader2, 
  AlertCircle, 
  Save,
  X
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { DependencyCard } from '@/components/ui/DependencyCard';
import { GuidesApi, Guide as Dependency, GuideCreate as DependencyCreate, GuideUpdate as DependencyUpdate } from '@/services/guidesApi';

// Helper function to ensure all form fields are strings
const createEmptyFormData = (): DependencyFormData => ({
  title: '',
  platform_name: '',
  where_to_get: '',
  guide_link: '',
  documentation_link: '',
  description: ''
});

// Helper function to safely convert dependency to form data
const dependencyToFormData = (dependency: Dependency): DependencyFormData => ({
  title: dependency.title || '',
  platform_name: dependency.platform_name || '',
  where_to_get: dependency.where_to_get || '',
  guide_link: dependency.guide_link || '',
  documentation_link: dependency.documentation_link || '',
  description: dependency.description || ''
});

interface DependencyFormData {
  title: string;
  platform_name: string;
  where_to_get: string;
  guide_link: string;
  documentation_link: string;
  description: string;
}

export const AdminDependenciesPage: React.FC = () => {
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredDependencies, setFilteredDependencies] = useState<Dependency[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingDependency, setEditingDependency] = useState<Dependency | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState<DependencyFormData>(createEmptyFormData);

  useEffect(() => {
    fetchDependencies();
  }, []);

  useEffect(() => {
    const filtered = dependencies.filter(dep =>
      dep.platform_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (dep.description && dep.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    setFilteredDependencies(filtered);
  }, [searchTerm, dependencies]);

  const fetchDependencies = async () => {
    try {
      setLoading(true);
      const data = await GuidesApi.getAllGuides();
      setDependencies(data);
      setFilteredDependencies(data);
    } catch (err) {
      setError('Failed to load dependencies. Please try again later.');
      console.error('Error fetching dependencies:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData(createEmptyFormData());
    setEditingDependency(null);
    setShowForm(false);
  };

  const handleCreate = () => {
    resetForm();
    setShowForm(true);
  };

  const handleEdit = (dependency: Dependency) => {
    setFormData(dependencyToFormData(dependency));
    setEditingDependency(dependency);
    setShowForm(true);
  };

  const handleDelete = async (dependency: Dependency) => {
    if (!confirm(`Are you sure you want to delete "${dependency.platform_name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await GuidesApi.deleteGuide(dependency.id);
      await fetchDependencies();
    } catch (err) {
      setError('Failed to delete dependency. Please try again.');
      console.error('Error deleting dependency:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }
    
    if (!formData.platform_name.trim()) {
      setError('Platform name is required');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const submitData = {
        title: formData.title.trim(),
        platform_name: formData.platform_name.trim(),
        where_to_get: formData.where_to_get.trim() || undefined,
        guide_link: formData.guide_link.trim() || undefined,
        documentation_link: formData.documentation_link.trim() || undefined,
        description: formData.description.trim() || undefined
      };

      if (editingDependency) {
        // Update existing dependency
        await GuidesApi.updateGuide(editingDependency.id, submitData as DependencyUpdate);
      } else {
        // Create new dependency
        await GuidesApi.createGuide(submitData as DependencyCreate);
      }

      await fetchDependencies();
      resetForm();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
        `Failed to ${editingDependency ? 'update' : 'create'} dependency. Please try again.`;
      setError(errorMessage);
      console.error('Error submitting dependency:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof DependencyFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value || '' // Ensure we always have a string value
    }));
  };

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

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <BookOpen className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Manage Dependencies
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Add, edit, and manage platform setup guides for clients
              </p>
            </div>
          </div>
          <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            Add Platform
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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
                    With API Links
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {dependencies.filter(d => d.where_to_get).length}
                  </p>
                </div>
                <ExternalLink className="h-8 w-8 text-purple-600" />
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
                <Search className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search platforms..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800 dark:text-red-200">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Form Modal */}
      {showForm && (
        <Card className="mb-8 border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-blue-900 dark:text-blue-100">
                  {editingDependency ? 'Edit Platform' : 'Add New Platform'}
                </CardTitle>
                <CardDescription className="text-blue-700 dark:text-blue-300">
                  {editingDependency ? 'Update the platform information' : 'Add a new platform guide for clients'}
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={resetForm}
                className="text-blue-700 border-blue-300 hover:bg-blue-100"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="title" className="text-blue-900 dark:text-blue-100">
                    Title *
                  </Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="e.g., OpenAI API Setup Guide"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="platform_name" className="text-blue-900 dark:text-blue-100">
                    Platform Name *
                  </Label>
                  <Input
                    id="platform_name"
                    value={formData.platform_name}
                    onChange={(e) => handleInputChange('platform_name', e.target.value)}
                    placeholder="e.g., OpenAI, Google Sheets, Slack"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="where_to_get" className="text-blue-900 dark:text-blue-100">
                    API Keys URL
                  </Label>
                  <Input
                    id="where_to_get"
                    value={formData.where_to_get}
                    onChange={(e) => handleInputChange('where_to_get', e.target.value)}
                    placeholder="https://platform.openai.com/api-keys"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="guide_link" className="text-blue-900 dark:text-blue-100">
                    Step-by-Step Guide URL
                  </Label>
                  <Input
                    id="guide_link"
                    value={formData.guide_link}
                    onChange={(e) => handleInputChange('guide_link', e.target.value)}
                    placeholder="https://app.tango.us/app/workflow/..."
                  />
                </div>
                <div>
                  <Label htmlFor="documentation_link" className="text-blue-900 dark:text-blue-100">
                    Documentation URL
                  </Label>
                  <Input
                    id="documentation_link"
                    value={formData.documentation_link}
                    onChange={(e) => handleInputChange('documentation_link', e.target.value)}
                    placeholder="https://docs.platform.com/api"
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="description" className="text-blue-900 dark:text-blue-100">
                  Description
                </Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Brief description of what this platform is used for..."
                  rows={3}
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button
                  type="submit"
                  disabled={submitting}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {editingDependency ? 'Updating...' : 'Creating...'}
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      {editingDependency ? 'Update Platform' : 'Create Platform'}
                    </>
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Dependencies Grid */}
      {filteredDependencies.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {searchTerm ? 'No matching platforms found' : 'No dependencies yet'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchTerm 
                ? `No platforms match "${searchTerm}". Try a different search term.`
                : 'Get started by adding your first platform guide.'
              }
            </p>
            {searchTerm ? (
              <Button onClick={() => setSearchTerm('')} variant="outline">
                Clear Search
              </Button>
            ) : (
              <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Add First Platform
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
              onEdit={handleEdit}
              onDelete={handleDelete}
              showAdminActions={true}
            />
          ))}
        </div>
      )}
    </div>
  );
};