import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { ProgressBar } from './ui/ProgressBar';

interface ETLStatus {
  status: 'active' | 'inactive' | 'error';
  total_projects: number;
  total_municipalities: number;
  recent_changes: Array<{
    id: string;
    entity_type: string;
    entity_id: string;
    change_type: string;
    source: string;
    created_at: string;
    field_changes: string[];
  }>;
}

interface DataQualityStats {
  overview: {
    total_projects: number;
    total_municipalities: number;
    total_financial_records: number;
  };
  completeness: {
    projects_with_complete_data: number;
    completeness_rate: number;
  };
  data_sources: {
    dws_projects: number;
    treasury_financial_data: number;
  };
  quality_indicators: {
    projects_with_budgets: number;
    municipalities_with_financial_data: number;
    orphaned_projects: number;
  };
}

export const ETLMonitoring: React.FC = () => {
  const [etlStatus, setEtlStatus] = useState<ETLStatus | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggerLoading, setTriggerLoading] = useState<string | null>(null);

  const fetchETLStatus = async () => {
    try {
      const response = await fetch(`/api/v1/etl/status`);
      if (!response.ok) throw new Error('Failed to fetch ETL status');
      const data = await response.json();
      setEtlStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchDataQuality = async () => {
    try {
      const response = await fetch(`/api/v1/data/stats/data-quality`);
      if (!response.ok) throw new Error('Failed to fetch data quality stats');
      const data = await response.json();
      setDataQuality(data);
    } catch (err) {
      console.error('Error fetching data quality stats:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchETLStatus(), fetchDataQuality()]);
      setLoading(false);
    };

    loadData();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchETLStatus();
      fetchDataQuality();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleTriggerETL = async (type: 'demo' | 'dws') => {
    setTriggerLoading(type);
    try {
      const endpoint = type === 'demo' ? `/api/v1/etl/trigger` : `/api/v1/etl/dws-sync`;
      const response = await fetch(endpoint, { method: 'POST' });
      if (!response.ok) throw new Error(`Failed to trigger ${type} ETL`);
      
      // Refresh data after triggering
      setTimeout(() => {
        fetchETLStatus();
        fetchDataQuality();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ETL trigger failed');
    } finally {
      setTriggerLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'inactive': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getChangeTypeColor = (changeType: string) => {
    switch (changeType) {
      case 'created': return 'text-green-600 bg-green-100';
      case 'updated': return 'text-blue-600 bg-blue-100';
      case 'deleted': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

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

      {/* ETL Pipeline Status */}
      <Card>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">ETL Pipeline Status</h2>
            <div className="flex gap-3">
              <Button
                onClick={() => handleTriggerETL('demo')}
                disabled={!!triggerLoading}
                variant="secondary"
                size="sm"
              >
                {triggerLoading === 'demo' ? 'Triggering...' : 'Trigger Demo ETL'}
              </Button>
              <Button
                onClick={() => handleTriggerETL('dws')}
                disabled={!!triggerLoading}
                variant="primary"
                size="sm"
              >
                {triggerLoading === 'dws' ? 'Syncing...' : 'Sync DWS Data'}
              </Button>
            </div>
          </div>

          {etlStatus && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Pipeline Status</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(etlStatus.status)}`}>
                    {etlStatus.status}
                  </span>
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {etlStatus.status === 'active' ? 'Running' : 'Inactive'}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Total Projects</div>
                <div className="text-2xl font-bold text-green-600">
                  {etlStatus.total_projects}
                </div>
                <div className="text-xs text-gray-500">
                  Across {etlStatus.total_municipalities} municipalities
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Recent Changes</div>
                <div className="text-2xl font-bold text-purple-600">
                  {etlStatus.recent_changes.length}
                </div>
                <div className="text-xs text-gray-500">
                  In last 24 hours
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Data Quality Overview */}
      {dataQuality && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Data Quality Overview</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {dataQuality.overview.total_projects}
                </div>
                <div className="text-sm text-blue-600">Total Projects</div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {dataQuality.overview.total_municipalities}
                </div>
                <div className="text-sm text-green-600">Municipalities</div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {dataQuality.overview.total_financial_records}
                </div>
                <div className="text-sm text-purple-600">Financial Records</div>
              </div>

              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {dataQuality.completeness.completeness_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-orange-600">Data Completeness</div>
              </div>
            </div>

            {/* Data Completeness Progress */}
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-2">
                <span>Data Completeness</span>
                <span>{dataQuality.completeness.completeness_rate.toFixed(1)}%</span>
              </div>
              <ProgressBar 
                progress={dataQuality.completeness.completeness_rate} 
                className="h-3 mb-2" 
              />
              <div className="text-sm text-gray-600">
                {dataQuality.completeness.projects_with_complete_data} of {dataQuality.overview.total_projects} projects have complete data
              </div>
            </div>

            {/* Data Sources */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Data Sources</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                    <span className="text-sm">DWS Projects</span>
                    <span className="font-medium">{dataQuality.data_sources.dws_projects}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                    <span className="text-sm">Treasury Financial Data</span>
                    <span className="font-medium">{dataQuality.data_sources.treasury_financial_data}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Quality Indicators</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                    <span className="text-sm">Projects with Budgets</span>
                    <span className="font-medium text-green-600">{dataQuality.quality_indicators.projects_with_budgets}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                    <span className="text-sm">Financial Data Available</span>
                    <span className="font-medium text-blue-600">{dataQuality.quality_indicators.municipalities_with_financial_data}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                    <span className="text-sm">Orphaned Projects</span>
                    <span className={`font-medium ${dataQuality.quality_indicators.orphaned_projects > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {dataQuality.quality_indicators.orphaned_projects}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Recent Changes */}
      {etlStatus && etlStatus.recent_changes.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Data Changes</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Change Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fields Changed
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {etlStatus.recent_changes.map((change) => (
                    <tr key={change.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {change.entity_type}
                        </div>
                        <div className="text-sm text-gray-500">
                          {change.entity_id.substring(0, 8)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getChangeTypeColor(change.change_type)}`}>
                          {change.change_type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {change.field_changes.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {change.field_changes.slice(0, 3).map((field, index) => (
                                <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                  {field}
                                </span>
                              ))}
                              {change.field_changes.length > 3 && (
                                <span className="text-xs text-gray-500">
                                  +{change.field_changes.length - 3} more
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-500">No specific fields</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {change.source}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(change.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}

      {etlStatus && etlStatus.recent_changes.length === 0 && (
        <Card>
          <div className="p-12 text-center text-gray-500">
            <div className="text-lg mb-2">No recent data changes</div>
            <div className="text-sm">Changes will appear here when data is updated</div>
          </div>
        </Card>
      )}
    </div>
  );
};
