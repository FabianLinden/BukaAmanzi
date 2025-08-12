import { useState, useCallback, useEffect } from 'react';

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

interface Municipality {
  id: string;
  name: string;
}

interface Project {
  id: string;
  external_id?: string;
  source: string;
  municipality_id?: string;
  municipality_name?: string;
  name: string;
  description?: string;
  project_type?: string;
  status: string;
  start_date?: string;
  end_date?: string;
  location?: string;
  address?: string;
  budget_allocated?: number;
  budget_spent?: number;
  progress_percentage: number;
  contractor?: string;
  created_at: string;
  updated_at: string;
}

interface UseProjectSearchResult {
  projects: Project[];
  municipalities: Municipality[];
  isLoading: boolean;
  error: string | null;
  searchProjects: (filters: SearchFilters) => Promise<void>;
  loadMunicipalities: () => Promise<void>;
  totalResults: number;
  currentPage: number;
  hasMoreResults: boolean;
}

export const useProjectSearch = (): UseProjectSearchResult => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreResults, setHasMoreResults] = useState(false);

  // Build query string from filters
  const buildQueryString = useCallback((filters: SearchFilters): string => {
    const params = new URLSearchParams();
    
    if (filters.search && filters.search.trim()) {
      params.append('search', filters.search.trim());
    }
    if (filters.status) {
      params.append('status', filters.status);
    }
    if (filters.municipality_id) {
      params.append('municipality_id', filters.municipality_id);
    }
    if (filters.project_type) {
      params.append('project_type', filters.project_type);
    }
    if (filters.min_progress !== undefined && filters.min_progress >= 0) {
      params.append('min_progress', filters.min_progress.toString());
    }
    if (filters.max_progress !== undefined && filters.max_progress <= 100) {
      params.append('max_progress', filters.max_progress.toString());
    }
    if (filters.page && filters.page > 0) {
      params.append('page', filters.page.toString());
    }
    if (filters.limit && filters.limit > 0) {
      params.append('limit', filters.limit.toString());
    }

    return params.toString();
  }, []);

  // Search projects with filters
  const searchProjects = useCallback(async (filters: SearchFilters) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const queryString = buildQueryString(filters);
      const url = `/api/v1/projects/${queryString ? `?${queryString}` : ''}`;
      
      console.log('Searching projects with URL:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Handle both array response and paginated response
      if (Array.isArray(data)) {
        setProjects(data);
        setTotalResults(data.length);
        setCurrentPage(filters.page || 1);
        setHasMoreResults(data.length === (filters.limit || 100));
      } else {
        // If the API returns paginated data in the future
        setProjects(data.projects || data.items || []);
        setTotalResults(data.total || data.count || 0);
        setCurrentPage(data.page || filters.page || 1);
        setHasMoreResults(data.has_more || false);
      }

      console.log('Search results:', {
        count: Array.isArray(data) ? data.length : (data.projects || data.items || []).length,
        filters,
        url
      });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      console.error('Error searching projects:', err);
      setError(errorMessage);
      setProjects([]);
      setTotalResults(0);
      setHasMoreResults(false);
    } finally {
      setIsLoading(false);
    }
  }, [buildQueryString]);

  // Load municipalities for filter dropdown
  const loadMunicipalities = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/municipalities/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMunicipalities(Array.isArray(data) ? data : []);
      } else {
        // If municipalities endpoint doesn't exist, extract from projects
        console.warn('Municipalities endpoint not available, extracting from projects');
        
        // Try to get unique municipalities from all projects
        const projectsResponse = await fetch('/api/v1/projects/?limit=1000', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (projectsResponse.ok) {
          const projectsData = await projectsResponse.json();
          const uniqueMunicipalities = new Map<string, Municipality>();
          
          projectsData.forEach((project: Project) => {
            if (project.municipality_id && project.municipality_name) {
              uniqueMunicipalities.set(project.municipality_id, {
                id: project.municipality_id,
                name: project.municipality_name
              });
            }
          });
          
          setMunicipalities(Array.from(uniqueMunicipalities.values()).sort((a, b) => a.name.localeCompare(b.name)));
        }
      }
    } catch (err) {
      console.error('Error loading municipalities:', err);
      setMunicipalities([]);
    }
  }, []);

  // Load municipalities on hook initialization
  useEffect(() => {
    loadMunicipalities();
  }, [loadMunicipalities]);

  return {
    projects,
    municipalities,
    isLoading,
    error,
    searchProjects,
    loadMunicipalities,
    totalResults,
    currentPage,
    hasMoreResults,
  };
};
