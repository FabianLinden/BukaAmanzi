import React, { useState, useEffect, useMemo } from 'react';

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

interface AdvancedProjectSearchProps {
  onFiltersChange: (filters: SearchFilters) => void;
  onSearch: () => void;
  isLoading?: boolean;
  municipalityOptions?: Municipality[];
  className?: string;
}

export const AdvancedProjectSearch: React.FC<AdvancedProjectSearchProps> = ({
  onFiltersChange,
  onSearch,
  isLoading = false,
  municipalityOptions = [],
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    status: '',
    municipality_id: '',
    project_type: '',
    min_progress: undefined,
    max_progress: undefined,
    min_budget: undefined,
    max_budget: undefined,
    page: 1,
    limit: 100
  });

  // Derived state for displaying filter summary
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.status) count++;
    if (filters.municipality_id) count++;
    if (filters.project_type) count++;
    if (filters.min_progress !== undefined) count++;
    if (filters.max_progress !== undefined) count++;
    if (filters.min_budget !== undefined) count++;
    if (filters.max_budget !== undefined) count++;
    return count;
  }, [filters]);

  // Status options
  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'planned', label: 'Planned' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'delayed', label: 'Delayed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  // Project type options (derived from common project names)
  const projectTypeOptions = [
    { value: '', label: 'All Project Types' },
    { value: 'Water Treatment', label: 'Water Treatment' },
    { value: 'Pipeline', label: 'Pipeline' },
    { value: 'Dam Construction', label: 'Dam Construction' },
    { value: 'Water Supply', label: 'Water Supply' },
    { value: 'Infrastructure', label: 'Infrastructure' },
    { value: 'Other', label: 'Other' }
  ];

  // Update filters and notify parent
  const updateFilters = (newFilters: Partial<SearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFiltersChange(updatedFilters);
  };

  // Handle form submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  // Clear all filters
  const clearFilters = () => {
    const emptyFilters: SearchFilters = {
      search: '',
      status: '',
      municipality_id: '',
      project_type: '',
      min_progress: undefined,
      max_progress: undefined,
      min_budget: undefined,
      max_budget: undefined,
      page: 1,
      limit: 100
    };
    setFilters(emptyFilters);
    onFiltersChange(emptyFilters);
    onSearch();
  };

  // Format currency for budget inputs
  const formatBudgetValue = (value: string): number | undefined => {
    if (!value || value.trim() === '') return undefined;
    const numValue = parseFloat(value.replace(/[^\d.]/g, ''));
    return isNaN(numValue) ? undefined : numValue;
  };

  const formatBudgetDisplay = (value: number | undefined): string => {
    if (value === undefined) return '';
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toString();
  };

  return (
    <div className={`bg-gradient-to-r from-white to-water-blue-50/80 rounded-lg border border-water-blue-200/60 shadow-sm ${className}`}>
      <form onSubmit={handleSearch}>
        {/* Basic Search Bar */}
        <div className="p-4">
          <div className="flex items-center space-x-3">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search projects by name, description, or contractor..."
                className="w-full px-4 py-2 pr-10 rounded-lg border border-water-blue-300/60 bg-white focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 transition-all"
                value={filters.search || ''}
                onChange={(e) => updateFilters({ search: e.target.value })}
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Search Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`px-6 py-2 bg-gradient-to-r from-water-blue-600 to-ocean-600 text-white rounded-lg hover:from-water-blue-700 hover:to-ocean-700 focus:outline-none focus:ring-2 focus:ring-water-blue-500 transition-all font-medium ${
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {isLoading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Searching...
                </div>
              ) : (
                'Search'
              )}
            </button>

            {/* Advanced Filters Toggle */}
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-4 py-2 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-lg hover:from-gray-200 hover:to-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all font-medium"
            >
              <div className="flex items-center space-x-2">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                </svg>
                <span>Filters</span>
                {activeFilterCount > 0 && (
                  <span className="bg-water-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                    {activeFilterCount}
                  </span>
                )}
                <svg
                  className={`h-4 w-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>
          </div>
        </div>

        {/* Advanced Filters Panel */}
        {isExpanded && (
          <div className="border-t border-water-blue-200/40 bg-gradient-to-r from-water-blue-25 to-ocean-25 p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Status
                </label>
                <select
                  value={filters.status || ''}
                  onChange={(e) => updateFilters({ status: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Municipality Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Municipality
                </label>
                <select
                  value={filters.municipality_id || ''}
                  onChange={(e) => updateFilters({ municipality_id: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                >
                  <option value="">All Municipalities</option>
                  {municipalityOptions.map((municipality) => (
                    <option key={municipality.id} value={municipality.id}>
                      {municipality.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Project Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Type
                </label>
                <select
                  value={filters.project_type || ''}
                  onChange={(e) => updateFilters({ project_type: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                >
                  {projectTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Results Per Page */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Results Per Page
                </label>
                <select
                  value={filters.limit || 100}
                  onChange={(e) => updateFilters({ limit: parseInt(e.target.value), page: 1 })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                >
                  <option value={25}>25 results</option>
                  <option value={50}>50 results</option>
                  <option value={100}>100 results</option>
                  <option value={200}>200 results</option>
                </select>
              </div>
            </div>

            {/* Progress Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Progress (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="e.g. 25"
                  value={filters.min_progress || ''}
                  onChange={(e) => updateFilters({ 
                    min_progress: e.target.value ? parseInt(e.target.value) : undefined 
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Progress (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="e.g. 75"
                  value={filters.max_progress || ''}
                  onChange={(e) => updateFilters({ 
                    max_progress: e.target.value ? parseInt(e.target.value) : undefined 
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                />
              </div>
            </div>

            {/* Budget Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Budget (R)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 1000000 or 1M"
                  value={filters.min_budget ? formatBudgetDisplay(filters.min_budget) : ''}
                  onChange={(e) => updateFilters({ 
                    min_budget: formatBudgetValue(e.target.value)
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Budget (R)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 50000000 or 50M"
                  value={filters.max_budget ? formatBudgetDisplay(filters.max_budget) : ''}
                  onChange={(e) => updateFilters({ 
                    max_budget: formatBudgetValue(e.target.value)
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 text-sm"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-water-blue-200/40">
              <div className="text-sm text-gray-600">
                {activeFilterCount > 0 && `${activeFilterCount} filter${activeFilterCount !== 1 ? 's' : ''} applied`}
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={clearFilters}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all text-sm"
                >
                  Clear All
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className={`px-6 py-2 bg-gradient-to-r from-water-blue-600 to-ocean-600 text-white rounded-lg hover:from-water-blue-700 hover:to-ocean-700 focus:outline-none focus:ring-2 focus:ring-water-blue-500 transition-all font-medium text-sm ${
                    isLoading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
