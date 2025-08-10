import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';

interface Municipality {
  id: string;
  name: string;
  code: string;
  province?: string;
  project_count: number;
  total_value: number;
  dashboard_url?: string;
}

interface MunicipalityProject {
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

interface Props {
  onSelectMunicipality?: (municipalityId: string) => void;
  onViewProject?: (projectId: string) => void;
}

export const MunicipalityManagement: React.FC<Props> = ({ 
  onSelectMunicipality,
  onViewProject 
}) => {
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [selectedMunicipality, setSelectedMunicipality] = useState<Municipality | null>(null);
  const [municipalityProjects, setMunicipalityProjects] = useState<MunicipalityProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    province: ''
  });

  const fetchMunicipalities = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.province) params.append('province', filters.province);

      const response = await fetch(`/api/v1/municipalities?${params}`);
      if (!response.ok) throw new Error('Failed to fetch municipalities');
      const data = await response.json();
      setMunicipalities(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchMunicipalityProjects = async (municipalityId: string) => {
    setProjectsLoading(true);
    try {
      const response = await fetch(`/api/v1/municipalities/${municipalityId}/projects`);
      if (!response.ok) throw new Error('Failed to fetch municipality projects');
      const data = await response.json();
      setMunicipalityProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setProjectsLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchMunicipalities();
      setLoading(false);
    };

    loadData();
  }, [filters]);

  const handleSelectMunicipality = async (municipality: Municipality) => {
    setSelectedMunicipality(municipality);
    await fetchMunicipalityProjects(municipality.id);
    if (onSelectMunicipality) onSelectMunicipality(municipality.id);
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1e9) {
      return `R${(amount / 1e9).toFixed(1)}B`;
    } else if (amount >= 1e6) {
      return `R${(amount / 1e6).toFixed(1)}M`;
    } else {
      return `R${amount.toLocaleString()}`;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'planned': return 'bg-yellow-100 text-yellow-800';
      case 'delayed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const provinces = [
    'Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 
    'Limpopo', 'Mpumalanga', 'Northern Cape', 'North West', 'Western Cape'
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="p-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <h2 className="text-xl font-semibold">Municipalities</h2>
            <div className="flex flex-wrap gap-3">
              <select
                value={filters.province}
                onChange={(e) => setFilters({...filters, province: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Provinces</option>
                {provinces.map(province => (
                  <option key={province} value={province}>{province}</option>
                ))}
              </select>
              {selectedMunicipality && (
                <Button
                  onClick={() => setSelectedMunicipality(null)}
                  variant="secondary"
                  size="sm"
                >
                  Back to List
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card>

      {selectedMunicipality ? (
        // Municipality Details View
        <div className="space-y-6">
          {/* Municipality Header */}
          <Card>
            <div className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-bold">{selectedMunicipality.name}</h3>
                  <div className="text-gray-600">
                    {selectedMunicipality.code} • {selectedMunicipality.province}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-medium">
                    {selectedMunicipality.project_count} Projects
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatCurrency(selectedMunicipality.total_value)} Total Value
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Municipality Projects */}
          <Card>
            <div className="p-6">
              <h4 className="text-lg font-semibold mb-4">Projects</h4>
              {projectsLoading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                </div>
              ) : municipalityProjects.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No projects found for this municipality.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Project
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Progress
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Budget
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {municipalityProjects.map((project) => (
                        <tr key={project.id}>
                          <td className="px-6 py-4">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {project.name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {project.location || project.address}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                              {project.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-1 mr-3">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full" 
                                    style={{ width: `${project.progress_percentage}%` }}
                                  ></div>
                                </div>
                              </div>
                              <div className="text-sm text-gray-600">
                                {project.progress_percentage}%
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {project.budget_allocated ? formatCurrency(project.budget_allocated) : 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <Button
                              onClick={() => onViewProject && onViewProject(project.id)}
                              variant="secondary"
                              size="sm"
                            >
                              View Details
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>
        </div>
      ) : (
        // Municipalities Grid View
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {municipalities.map((municipality) => (
            <Card key={municipality.id} className="cursor-pointer hover:shadow-lg transition-shadow">
              <div 
                className="p-6"
                onClick={() => handleSelectMunicipality(municipality)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{municipality.name}</h3>
                    <div className="text-sm text-gray-600">
                      {municipality.code}
                    </div>
                    {municipality.province && (
                      <div className="text-sm text-gray-500">
                        {municipality.province}
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {municipality.project_count}
                    </div>
                    <div className="text-sm text-gray-600">Projects</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-green-600">
                      {formatCurrency(municipality.total_value)}
                    </div>
                    <div className="text-sm text-gray-600">Total Value</div>
                  </div>
                </div>

                {municipality.dashboard_url && (
                  <div className="mt-4 pt-4 border-t">
                    <a 
                      href={municipality.dashboard_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800"
                      onClick={(e) => e.stopPropagation()}
                    >
                      View External Dashboard →
                    </a>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {municipalities.length === 0 && !loading && (
        <Card>
          <div className="p-12 text-center text-gray-500">
            <div className="text-lg mb-2">No municipalities found</div>
            <div className="text-sm">Try adjusting your filters</div>
          </div>
        </Card>
      )}
    </div>
  );
};
