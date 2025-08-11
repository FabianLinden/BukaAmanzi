import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { ProgressBar } from './ui/ProgressBar';

interface MunicipalOverview {
  municipality: {
    id: string;
    name: string;
    code: string;
    province: string;
  };
  projects_summary: {
    total_projects: number;
    total_allocated: number;
    total_spent: number;
    average_progress: number;
    status_breakdown: {
      [status: string]: number;
    };
  };
  financial_summary: {
    latest_year: number;
    total_budget: number;
    water_related_capex: number;
    infrastructure_budget: number;
    surplus_deficit: number;
    years_available: number;
  };
  investment_efficiency: {
    project_to_capex_ratio: number;
    assessment: 'low' | 'balanced' | 'high';
  };
  recommendations: Array<{
    type: string;
    priority: 'low' | 'medium' | 'high';
    message: string;
  }>;
}

interface Props {
  municipalityId?: string;
}

export const MunicipalInvestmentOverview: React.FC<Props> = ({ municipalityId }) => {
  const [overview, setOverview] = useState<MunicipalOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverview = async () => {
      if (!municipalityId) {
        // If no municipality ID provided, show a selection interface or fetch a default one
        setLoading(false);
        setError('Please select a municipality to view investment overview');
        return;
      }
      
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`http://${window.location.hostname}:8000/api/v1/data/correlation/municipalities/${municipalityId}`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Municipality not found');
          }
          throw new Error('Failed to fetch municipal overview');
        }
        const data = await response.json();
        setOverview(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, [municipalityId]);

  const formatCurrency = (amount: number) => {
    if (amount >= 1e9) {
      return `R${(amount / 1e9).toFixed(1)}B`;
    } else if (amount >= 1e6) {
      return `R${(amount / 1e6).toFixed(1)}M`;
    } else if (amount >= 1e3) {
      return `R${(amount / 1e3).toFixed(1)}K`;
    } else {
      return `R${amount.toLocaleString()}`;
    }
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'planning': return 'bg-yellow-100 text-yellow-800';
      case 'delayed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: 'low' | 'medium' | 'high') => {
    switch (priority) {
      case 'high': return 'border-red-200 bg-red-50 text-red-800';
      case 'medium': return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'low': return 'border-blue-200 bg-blue-50 text-blue-800';
      default: return 'border-gray-200 bg-gray-50 text-gray-800';
    }
  };

  const getEfficiencyColor = (assessment: 'low' | 'balanced' | 'high') => {
    switch (assessment) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'balanced': return 'text-blue-600 bg-blue-100';
      case 'low': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-6 text-center">
          <div className="text-red-600 mb-2">Error loading municipal overview</div>
          <div className="text-sm text-gray-600">{error}</div>
        </div>
      </Card>
    );
  }

  if (!overview) {
    return (
      <Card>
        <div className="p-6 text-center">
          <div className="text-gray-600">No data available for this municipality</div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Municipality Header */}
      <Card>
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold">{overview.municipality.name}</h1>
              <div className="text-sm text-gray-600">
                {overview.municipality.code} • {overview.municipality.province}
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-medium">
                {overview.projects_summary.total_projects} Projects
              </div>
              <div className="text-sm text-gray-600">
                {formatCurrency(overview.projects_summary.total_allocated)} Total Value
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="p-6">
            <div className="text-sm text-gray-600 mb-2">Project Portfolio</div>
            <div className="text-2xl font-bold text-blue-600">
              {overview.projects_summary.total_projects}
            </div>
            <div className="text-sm text-gray-600">
              Avg Progress: {formatPercentage(overview.projects_summary.average_progress)}
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm text-gray-600 mb-2">Budget Utilization</div>
            <div className="text-2xl font-bold text-green-600">
              {overview.projects_summary.total_allocated > 0 
                ? formatPercentage((overview.projects_summary.total_spent / overview.projects_summary.total_allocated) * 100)
                : '0%'
              }
            </div>
            <div className="text-sm text-gray-600">
              {formatCurrency(overview.projects_summary.total_spent)} spent
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm text-gray-600 mb-2">Municipal Budget ({overview.financial_summary.latest_year})</div>
            <div className="text-2xl font-bold text-purple-600">
              {formatCurrency(overview.financial_summary.total_budget)}
            </div>
            <div className={`text-sm ${overview.financial_summary.surplus_deficit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {overview.financial_summary.surplus_deficit >= 0 ? 'Surplus' : 'Deficit'}: {formatCurrency(Math.abs(overview.financial_summary.surplus_deficit))}
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm text-gray-600 mb-2">Investment Efficiency</div>
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEfficiencyColor(overview.investment_efficiency.assessment)}`}>
              {overview.investment_efficiency.assessment.toUpperCase()}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Ratio: {overview.investment_efficiency.project_to_capex_ratio}x
            </div>
          </div>
        </Card>
      </div>

      {/* Project Status Breakdown */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Project Status Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Object.entries(overview.projects_summary.status_breakdown).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                  {status.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-lg font-bold mt-2">{count}</div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Financial Overview */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Financial Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600 mb-2">Total Municipal Budget</div>
              <div className="text-xl font-bold">{formatCurrency(overview.financial_summary.total_budget)}</div>
              <div className="text-xs text-gray-500 mt-1">Financial Year {overview.financial_summary.latest_year}</div>
            </div>

            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600 mb-2">Infrastructure Budget</div>
              <div className="text-xl font-bold">{formatCurrency(overview.financial_summary.infrastructure_budget)}</div>
              <div className="text-xs text-gray-500 mt-1">
                {overview.financial_summary.total_budget > 0 
                  ? formatPercentage((overview.financial_summary.infrastructure_budget / overview.financial_summary.total_budget) * 100)
                  : '0%'
                } of total budget
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600 mb-2">Water-Related Capex</div>
              <div className="text-xl font-bold">{formatCurrency(overview.financial_summary.water_related_capex)}</div>
              <div className="text-xs text-gray-500 mt-1">
                {overview.financial_summary.infrastructure_budget > 0 
                  ? formatPercentage((overview.financial_summary.water_related_capex / overview.financial_summary.infrastructure_budget) * 100)
                  : '0%'
                } of infrastructure budget
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Budget vs Projects Comparison */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Budget vs Project Investment</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Project Allocation vs Water Capex</span>
                <span>
                  {overview.financial_summary.water_related_capex > 0 
                    ? formatPercentage((overview.projects_summary.total_allocated / overview.financial_summary.water_related_capex) * 100)
                    : '0%'
                  }
                </span>
              </div>
              <ProgressBar 
                progress={overview.financial_summary.water_related_capex > 0 
                  ? Math.min(100, (overview.projects_summary.total_allocated / overview.financial_summary.water_related_capex) * 100)
                  : 0
                }
                className="h-2"
              />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Project Allocation vs Infrastructure Budget</span>
                <span>
                  {overview.financial_summary.infrastructure_budget > 0 
                    ? formatPercentage((overview.projects_summary.total_allocated / overview.financial_summary.infrastructure_budget) * 100)
                    : '0%'
                  }
                </span>
              </div>
              <ProgressBar 
                progress={overview.financial_summary.infrastructure_budget > 0 
                  ? Math.min(100, (overview.projects_summary.total_allocated / overview.financial_summary.infrastructure_budget) * 100)
                  : 0
                }
                className="h-2"
              />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Budget Utilization (Projects)</span>
                <span>
                  {overview.projects_summary.total_allocated > 0 
                    ? formatPercentage((overview.projects_summary.total_spent / overview.projects_summary.total_allocated) * 100)
                    : '0%'
                  }
                </span>
              </div>
              <ProgressBar 
                progress={overview.projects_summary.total_allocated > 0 
                  ? (overview.projects_summary.total_spent / overview.projects_summary.total_allocated) * 100
                  : 0
                }
                className="h-2"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Recommendations */}
      {overview.recommendations.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Investment Recommendations</h3>
            <div className="space-y-3">
              {overview.recommendations.map((rec, index) => (
                <div key={index} className={`border p-4 rounded ${getPriorityColor(rec.priority)}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-medium capitalize">
                      {rec.type.replace('_', ' ')}
                    </div>
                    <div className="text-xs uppercase tracking-wide font-medium">
                      {rec.priority} Priority
                    </div>
                  </div>
                  <div className="text-sm">{rec.message}</div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Data Source Info */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Data Sources</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <div className="font-medium text-sm mb-1">Project Data</div>
              <div className="text-xs text-gray-600">
                Source: DWS Project Monitoring Dashboard
              </div>
              <div className="text-xs text-gray-600">
                Projects: {overview.projects_summary.total_projects}
              </div>
            </div>

            <div className="bg-gray-50 p-3 rounded">
              <div className="font-medium text-sm mb-1">Financial Data</div>
              <div className="text-xs text-gray-600">
                Source: National Treasury Municipal Data
              </div>
              <div className="text-xs text-gray-600">
                Data Available: {overview.financial_summary.years_available} years
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
