import React, { useState, useEffect, useMemo } from 'react';
import { AdvancedProjectSearch } from './AdvancedProjectSearch';
import { ProjectCard } from './ProjectCard';
import { useProjectSearch } from '../hooks/useProjectSearch';
import { parseLocationFromProject } from '../utils/projectDataUtils';

interface SearchFilters {
  search?: string;
  status?: string;
  municipality_id?: string;
  project_type?: string;
  min_progress?: number;
  max_progress?: number;
  min_budget?: number;
  max_budget?: number;
  page?: number;
  limit?: number;
}

interface EnhancedProject {
  id: string;
  title: string;
  location: string;
  description: string;
  longDescription: string;
  progress: number;
  budget: number;
  spent: number;
  startDate: string;
  endDate: string;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  contractor?: string;
  municipality: string;
  lastUpdated: string;
  milestones: Array<{
    id: string;
    title: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'delayed';
    dueDate: string;
    completedDate?: string;
  }>;
  documents: Array<{
    id: string;
    title: string;
    type: 'report' | 'contract' | 'permit' | 'other';
    url: string;
    uploadedAt: string;
  }>;
  updates: Array<{
    id: string;
    title: string;
    description: string;
    date: string;
    author: string;
  }>;
  _originalData?: any;
}

interface EnhancedProjectsViewProps {
  onViewDetails: (projectId: string) => void;
  onProvideFeedback: (projectId: string) => void;
  onShowReportForm: () => void;
  className?: string;
}

export const EnhancedProjectsView: React.FC<EnhancedProjectsViewProps> = ({
  onViewDetails,
  onProvideFeedback,
  onShowReportForm,
  className = ''
}) => {
  const {
    projects: apiProjects,
    municipalities,
    isLoading,
    error,
    searchProjects,
    totalResults,
    currentPage,
    hasMoreResults
  } = useProjectSearch();

  const [currentFilters, setCurrentFilters] = useState<SearchFilters>({
    limit: 100,
    page: 1
  });

  // Transform API projects to frontend format
  const transformedProjects: EnhancedProject[] = useMemo(() => {
    return apiProjects.map(project => {
      const locationData = parseLocationFromProject(project);
      
      // Helper function to format dates properly
      const formatDate = (dateStr: string | null | undefined) => {
        if (!dateStr || dateStr.trim() === '') {
          return '2024-01-01'; // Default fallback date
        }
        try {
          return new Date(dateStr).toISOString().split('T')[0];
        } catch {
          return '2024-01-01';
        }
      };

      // Helper function to parse budget values
      const parseBudgetValue = (value: any): number => {
        if (typeof value === 'number') {
          return value;
        }
        if (typeof value === 'string') {
          const cleanValue = value.replace(/,/g, '.');
          const parsed = parseFloat(cleanValue);
          return isNaN(parsed) ? 0 : parsed;
        }
        return 0;
      };

      return {
        id: project.id,
        title: project.name,
        location: project.address || (locationData?.coordinates ? locationData.coordinates : 'Location not specified'),
        description: project.description || 'No description available',
        longDescription: project.description || 'No detailed description available',
        progress: project.progress_percentage || 0,
        budget: parseBudgetValue(project.budget_allocated),
        spent: parseBudgetValue(project.budget_spent),
        startDate: formatDate(project.start_date),
        endDate: formatDate(project.end_date),
        status: project.status as 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled',
        contractor: project.contractor || 'Not specified',
        municipality: project.municipality_name || 'Unknown Municipality',
        lastUpdated: project.updated_at || new Date().toISOString(),
        milestones: [],
        documents: [],
        updates: [],
        _originalData: project
      };
    });
  }, [apiProjects]);

  // Group projects by municipality for better organization
  const groupedProjects = useMemo(() => {
    const groups: Record<string, EnhancedProject[]> = {};
    transformedProjects.forEach(project => {
      const municipality = project.municipality || 'Unknown Municipality';
      if (!groups[municipality]) {
        groups[municipality] = [];
      }
      groups[municipality].push(project);
    });
    
    // Sort municipalities by number of projects (descending) and then alphabetically
    const sortedMunicipalities = Object.keys(groups).sort((a, b) => {
      const countDiff = groups[b].length - groups[a].length;
      if (countDiff !== 0) return countDiff;
      return a.localeCompare(b);
    });
    
    return sortedMunicipalities.map(municipality => ({
      municipality,
      projects: groups[municipality].sort((a, b) => {
        // Sort projects within municipality by title
        const aMatch = a.title.match(/Project\s+(\d+)/);
        const bMatch = b.title.match(/Project\s+(\d+)/);
        if (aMatch && bMatch) {
          return parseInt(aMatch[1]) - parseInt(bMatch[1]);
        }
        return a.title.localeCompare(b.title);
      })
    }));
  }, [transformedProjects]);

  // Handle filter changes
  const handleFiltersChange = (filters: SearchFilters) => {
    setCurrentFilters(filters);
  };

  // Handle search execution
  const handleSearch = async () => {
    await searchProjects(currentFilters);
  };

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      await searchProjects({ limit: 100, page: 1 });
    };
    loadInitialData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle pagination
  const handleLoadMore = async () => {
    if (!hasMoreResults || isLoading) return;
    
    const nextPage = currentPage + 1;
    const nextFilters = { ...currentFilters, page: nextPage };
    await searchProjects(nextFilters);
  };

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <svg className="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Projects</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={handleSearch}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Advanced Search Component */}
      <div className="mb-8">
        <AdvancedProjectSearch
          onFiltersChange={handleFiltersChange}
          onSearch={handleSearch}
          isLoading={isLoading}
          municipalityOptions={municipalities}
        />
      </div>

      {/* Search Results Summary */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Search Results
          </h3>
          <div className="text-sm text-gray-600">
            {isLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading...
              </div>
            ) : (
              `${transformedProjects.length} project${transformedProjects.length !== 1 ? 's' : ''} found`
            )}
          </div>
        </div>
        
        {transformedProjects.length > 0 && (
          <div className="text-sm text-gray-500">
            Page {currentPage} {hasMoreResults && `• More results available`}
          </div>
        )}
      </div>

      {/* Projects Display */}
      {transformedProjects.length > 0 ? (
        <>
          {/* Display projects grouped by municipality */}
          {groupedProjects.map(({ municipality, projects: municipalityProjects }) => (
            <div key={municipality} className="mb-8">
              {/* Municipality header */}
              <div className="mb-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="w-1 h-8 bg-gradient-to-b from-water-blue-500 to-water-blue-700 rounded-full"></div>
                    {municipality}
                    <span className="text-sm font-normal text-gray-500 bg-water-blue-50 px-2 py-1 rounded-full">
                      {municipalityProjects.length} project{municipalityProjects.length !== 1 ? 's' : ''}
                    </span>
                  </h2>
                </div>
                
                {/* Quick stats for this municipality */}
                <div className="mt-3 flex gap-4 text-sm text-gray-600">
                  <span>
                    Active: {municipalityProjects.filter(p => p.status === 'in_progress').length}
                  </span>
                  <span>
                    Completed: {municipalityProjects.filter(p => p.status === 'completed').length}
                  </span>
                  <span>
                    Budget: R{(municipalityProjects.reduce((sum, p) => sum + p.budget, 0) / 1000000).toFixed(1)}M
                  </span>
                </div>
              </div>
              
              {/* Projects grid for this municipality */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {municipalityProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    {...project}
                    onViewDetails={onViewDetails}
                    onProvideFeedback={onProvideFeedback}
                  />
                ))}
              </div>
            </div>
          ))}
          
          {/* Load More Button */}
          {hasMoreResults && (
            <div className="mt-8 text-center">
              <button
                onClick={handleLoadMore}
                disabled={isLoading}
                className={`px-6 py-3 bg-gradient-to-r from-water-blue-600 to-ocean-600 text-white rounded-lg hover:from-water-blue-700 hover:to-ocean-700 focus:outline-none focus:ring-2 focus:ring-water-blue-500 transition-all font-medium ${
                  isLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <div className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading More...
                  </div>
                ) : (
                  'Load More Projects'
                )}
              </button>
            </div>
          )}
          
          {/* Add Report Button */}
          <div className="mt-8 text-center">
            <div className="bg-gradient-to-r from-water-blue-50 to-ocean-50 p-6 rounded-xl border border-water-blue-200/50">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Submit a Community Report</h3>
              <p className="text-gray-600 mb-4">Report issues, provide updates, or share feedback about any water infrastructure project in your community.</p>
              <p className="text-sm text-gray-500 mb-4">Click on "Provide Feedback" button on any project card above, or the "Provide Feedback" button in the project details page.</p>
              <div className="flex items-center justify-center space-x-2 text-water-blue-600">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm font-medium">Select a project above to get started</span>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* No Results */
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p className="mt-2 text-lg font-medium">No projects found</p>
          <p className="text-gray-400">Try adjusting your search filters or search terms</p>
          <button 
            onClick={() => handleFiltersChange({ limit: 100, page: 1 })}
            className="mt-4 text-water-blue-600 hover:text-water-blue-800 underline"
          >
            Show all projects
          </button>
        </div>
      )}
    </div>
  );
};
