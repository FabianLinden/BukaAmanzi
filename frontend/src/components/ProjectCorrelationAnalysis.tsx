import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { ProgressBar } from './ui/ProgressBar';

interface ProjectCorrelation {
  project_id: string;
  project_name: string;
  municipality_name?: string;
  municipality_code?: string;
  province?: string;
  project_budget: {
    allocated: number;
    spent: number;
    progress_percentage: number;
  };
  municipal_context: {
    latest_year: number;
    total_budget: number;
    total_actual: number;
    water_related_capex: number;
    infrastructure_budget: number;
    surplus_deficit: number;
    budget_variance: number;
  };
  correlations: {
    project_vs_infrastructure_budget?: {
      percentage: number;
      significance: 'low' | 'medium' | 'high';
    };
    project_vs_water_capex?: {
      percentage: number;
      significance: 'low' | 'medium' | 'high';
    };
    project_vs_total_budget?: {
      percentage: number;
      significance: 'low' | 'medium' | 'high';
    };
    financial_health?: {
      budget_variance_trend?: {
        current: number;
        previous: number;
        change: number;
        improving: boolean;
      };
      infrastructure_trend?: {
        growth_rate: number;
        growing: boolean;
      };
      water_investment_trend?: {
        growth_rate: number;
        growing: boolean;
      };
    };
  };
  insights: string[];
  risk_indicators: Array<{
    type: string;
    severity: 'low' | 'medium' | 'high';
    message: string;
  }>;
}

interface CorrelationSummary {
  total_projects: number;
  projects_with_financial_data: number;
  high_risk_projects: number;
  major_investments: number;
  total_project_value: number;
  provinces: {
    [key: string]: {
      projects: number;
      total_value: number;
      high_risk: number;
    };
  };
  correlation_timestamp: string;
}

interface Props {
  projectId?: string;
  showSummary?: boolean;
}

export const ProjectCorrelationAnalysis: React.FC<Props> = ({ 
  projectId, 
  showSummary = true 
}) => {
  const [correlation, setCorrelation] = useState<ProjectCorrelation | null>(null);
  const [correlationSummary, setCorrelationSummary] = useState<CorrelationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (projectId) {
          // Fetch specific project correlation
          const response = await fetch(`http://${window.location.hostname}:8000/api/v1/data/correlation/projects/${projectId}`);
          if (!response.ok) throw new Error('Failed to fetch project correlation');
          const data = await response.json();
          setCorrelation(data);
        }

        if (showSummary) {
          // Fetch overall correlation summary
          const response = await fetch(`http://${window.location.hostname}:8000/api/v1/data/correlation/projects`);
          if (!response.ok) throw new Error('Failed to fetch correlation summary');
          const data = await response.json();
          setCorrelationSummary(data.summary);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, showSummary]);

  const formatCurrency = (amount: number) => {
    if (amount >= 1e9) {
      return `R${(amount / 1e9).toFixed(1)}B`;
    } else if (amount >= 1e6) {
      return `R${(amount / 1e6).toFixed(1)}M`;
    } else {
      return `R${amount.toLocaleString()}`;
    }
  };

  const getSignificanceColor = (significance: 'low' | 'medium' | 'high') => {
    switch (significance) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'high': return 'border-red-200 bg-red-50 text-red-800';
      case 'medium': return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'low': return 'border-blue-200 bg-blue-50 text-blue-800';
      default: return 'border-gray-200 bg-gray-50 text-gray-800';
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
          <div className="text-red-600 mb-2">Error loading correlation data</div>
          <div className="text-sm text-gray-600">{error}</div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      {showSummary && correlationSummary && (
        <Card>
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Correlation Analysis Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {correlationSummary.total_projects}
                </div>
                <div className="text-sm text-blue-600">Total Projects</div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {correlationSummary.projects_with_financial_data}
                </div>
                <div className="text-sm text-green-600">With Financial Data</div>
              </div>
              
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {correlationSummary.high_risk_projects}
                </div>
                <div className="text-sm text-red-600">High Risk Projects</div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {formatCurrency(correlationSummary.total_project_value)}
                </div>
                <div className="text-sm text-purple-600">Total Value</div>
              </div>
            </div>

            {/* Provincial Breakdown */}
            <div className="mb-4">
              <h3 className="text-lg font-medium mb-3">Provincial Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(correlationSummary.provinces).map(([province, data]) => (
                  <div key={province} className="bg-gray-50 p-3 rounded">
                    <div className="font-medium text-sm">{province}</div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <div>{data.projects} projects • {formatCurrency(data.total_value)}</div>
                      {data.high_risk > 0 && (
                        <div className="text-red-600">{data.high_risk} high risk</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Individual Project Correlation */}
      {correlation && (
        <Card>
          <div className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-semibold">{correlation.project_name}</h2>
                <div className="text-sm text-gray-600">
                  {correlation.municipality_name} • {correlation.province}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-medium">
                  {formatCurrency(correlation.project_budget.allocated)}
                </div>
                <div className="text-sm text-gray-600">Allocated Budget</div>
              </div>
            </div>

            {/* Project Budget Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600 mb-1">Budget Progress</div>
                <ProgressBar 
                  progress={correlation.project_budget.progress_percentage}
                  className="mb-2"
                />
                <div className="text-sm">
                  {formatCurrency(correlation.project_budget.spent)} of {formatCurrency(correlation.project_budget.allocated)}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600 mb-1">Municipal Budget ({correlation.municipal_context.latest_year})</div>
                <div className="font-medium">{formatCurrency(correlation.municipal_context.total_budget)}</div>
                <div className="text-xs text-gray-500">
                  Water Capex: {formatCurrency(correlation.municipal_context.water_related_capex)}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600 mb-1">Municipal Health</div>
                <div className={`font-medium ${correlation.municipal_context.surplus_deficit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {correlation.municipal_context.surplus_deficit >= 0 ? 'Surplus' : 'Deficit'}
                </div>
                <div className="text-xs text-gray-500">
                  Variance: {correlation.municipal_context.budget_variance.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Correlation Analysis */}
            {Object.keys(correlation.correlations).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-3">Financial Correlations</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {correlation.correlations.project_vs_infrastructure_budget && (
                    <div className="border p-4 rounded">
                      <div className="text-sm text-gray-600 mb-2">vs Infrastructure Budget</div>
                      <div className="flex justify-between items-center">
                        <div className="font-medium">
                          {correlation.correlations.project_vs_infrastructure_budget.percentage.toFixed(1)}%
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSignificanceColor(correlation.correlations.project_vs_infrastructure_budget.significance)}`}>
                          {correlation.correlations.project_vs_infrastructure_budget.significance}
                        </div>
                      </div>
                    </div>
                  )}

                  {correlation.correlations.project_vs_water_capex && (
                    <div className="border p-4 rounded">
                      <div className="text-sm text-gray-600 mb-2">vs Water Capex</div>
                      <div className="flex justify-between items-center">
                        <div className="font-medium">
                          {correlation.correlations.project_vs_water_capex.percentage.toFixed(1)}%
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSignificanceColor(correlation.correlations.project_vs_water_capex.significance)}`}>
                          {correlation.correlations.project_vs_water_capex.significance}
                        </div>
                      </div>
                    </div>
                  )}

                  {correlation.correlations.project_vs_total_budget && (
                    <div className="border p-4 rounded">
                      <div className="text-sm text-gray-600 mb-2">vs Total Budget</div>
                      <div className="flex justify-between items-center">
                        <div className="font-medium">
                          {correlation.correlations.project_vs_total_budget.percentage.toFixed(1)}%
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSignificanceColor(correlation.correlations.project_vs_total_budget.significance)}`}>
                          {correlation.correlations.project_vs_total_budget.significance}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Financial Health Trends */}
            {correlation.correlations.financial_health && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-3">Financial Health Trends</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {correlation.correlations.financial_health.infrastructure_trend && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Infrastructure Investment</div>
                      <div className={`font-medium ${correlation.correlations.financial_health.infrastructure_trend.growing ? 'text-green-600' : 'text-red-600'}`}>
                        {correlation.correlations.financial_health.infrastructure_trend.growth_rate > 0 ? '+' : ''}
                        {correlation.correlations.financial_health.infrastructure_trend.growth_rate.toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {correlation.correlations.financial_health.water_investment_trend && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Water Investment</div>
                      <div className={`font-medium ${correlation.correlations.financial_health.water_investment_trend.growing ? 'text-green-600' : 'text-red-600'}`}>
                        {correlation.correlations.financial_health.water_investment_trend.growth_rate > 0 ? '+' : ''}
                        {correlation.correlations.financial_health.water_investment_trend.growth_rate.toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {correlation.correlations.financial_health.budget_variance_trend && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Budget Variance Trend</div>
                      <div className={`font-medium ${correlation.correlations.financial_health.budget_variance_trend.improving ? 'text-green-600' : 'text-red-600'}`}>
                        {correlation.correlations.financial_health.budget_variance_trend.change > 0 ? '+' : ''}
                        {correlation.correlations.financial_health.budget_variance_trend.change.toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {correlation.insights.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-3">Key Insights</h3>
                <div className="space-y-2">
                  {correlation.insights.map((insight, index) => (
                    <div key={index} className="bg-blue-50 border border-blue-200 p-3 rounded text-sm">
                      💡 {insight}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Indicators */}
            {correlation.risk_indicators.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-3">Risk Indicators</h3>
                <div className="space-y-2">
                  {correlation.risk_indicators.map((risk, index) => (
                    <div key={index} className={`border p-3 rounded text-sm ${getRiskColor(risk.severity)}`}>
                      <div className="flex justify-between items-start">
                        <div className="font-medium capitalize">
                          {risk.type.replace('_', ' ')}
                        </div>
                        <div className="text-xs uppercase tracking-wide font-medium">
                          {risk.severity}
                        </div>
                      </div>
                      <div className="mt-1">{risk.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
