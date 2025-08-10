import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { ProgressBar } from './ui/ProgressBar';

interface SchedulerStatus {
  running: boolean;
  health_status: {
    dws_status: 'stopped' | 'running' | 'healthy' | 'error' | 'stale';
    treasury_status: 'stopped' | 'running' | 'healthy' | 'error' | 'stale';
    correlation_status: 'stopped' | 'running' | 'healthy' | 'error' | 'stale';
    last_successful_sync: string | null;
    total_errors: number;
    uptime_seconds?: number;
  };
  last_run_times: {
    [key: string]: string | null;
  };
  error_counts: {
    [key: string]: number;
  };
  next_runs: {
    [key: string]: string;
  };
}

interface DataSourceHealth {
  timestamp: string;
  overall_status: 'healthy' | 'warning' | 'error';
  data_sources: {
    dws_api: {
      status: 'healthy' | 'warning' | 'error';
      last_successful_fetch: string;
      response_time_ms: number;
      error_count_24h: number;
    };
    treasury_api: {
      status: 'healthy' | 'warning' | 'error';
      last_successful_fetch: string;
      response_time_ms: number;
      error_count_24h: number;
    };
    database: {
      status: 'healthy' | 'warning' | 'error';
      connection_pool_used: number;
      connection_pool_size: number;
      query_avg_time_ms: number;
    };
  };
  data_freshness: {
    dws_projects: string;
    financial_data: string;
    correlation_analysis: string;
  };
}

interface SyncResponse {
  status: 'success' | 'error';
  results: any;
  trigger_time: string;
  error?: string;
}

export const DataSyncDashboard: React.FC = () => {
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [dataSourceHealth, setDataSourceHealth] = useState<DataSourceHealth | null>(null);
  const [syncLoading, setSyncLoading] = useState<string | null>(null);
  const [lastSyncResults, setLastSyncResults] = useState<SyncResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch('/api/v1/data/scheduler/status');
      if (!response.ok) throw new Error('Failed to fetch scheduler status');
      const data = await response.json();
      setSchedulerStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchDataSourceHealth = async () => {
    try {
      const response = await fetch('/api/v1/data/health/data-sources');
      if (!response.ok) throw new Error('Failed to fetch data source health');
      const data = await response.json();
      setDataSourceHealth(data);
    } catch (err) {
      console.error('Error fetching data source health:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchSchedulerStatus(), fetchDataSourceHealth()]);
      setLoading(false);
    };

    loadData();
    const interval = setInterval(() => {
      fetchSchedulerStatus();
      fetchDataSourceHealth();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleStartScheduler = async () => {
    try {
      setSyncLoading('start');
      const response = await fetch('/api/v1/data/scheduler/start', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to start scheduler');
      await fetchSchedulerStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSyncLoading(null);
    }
  };

  const handleStopScheduler = async () => {
    try {
      setSyncLoading('stop');
      const response = await fetch('/api/v1/data/scheduler/stop', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to stop scheduler');
      await fetchSchedulerStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSyncLoading(null);
    }
  };

  const handleTriggerSync = async (source: 'all' | 'dws' | 'treasury' | 'correlation') => {
    try {
      setSyncLoading(source);
      const response = await fetch('/api/v1/data/sync/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source }),
      });
      if (!response.ok) throw new Error('Failed to trigger sync');
      const result = await response.json();
      setLastSyncResults(result);
      await fetchSchedulerStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSyncLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'stale': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
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

      {/* Scheduler Controls */}
      <Card>
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Data Scheduler</h2>
            <div className="flex space-x-2">
              <Button
                onClick={handleStartScheduler}
                disabled={syncLoading === 'start' || schedulerStatus?.running}
                variant={schedulerStatus?.running ? 'secondary' : 'primary'}
              >
                {syncLoading === 'start' ? 'Starting...' : schedulerStatus?.running ? 'Running' : 'Start'}
              </Button>
              <Button
                onClick={handleStopScheduler}
                disabled={syncLoading === 'stop' || !schedulerStatus?.running}
                variant="secondary"
              >
                {syncLoading === 'stop' ? 'Stopping...' : 'Stop'}
              </Button>
            </div>
          </div>

          {schedulerStatus && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">DWS Status</div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(schedulerStatus.health_status.dws_status)}`}>
                  {schedulerStatus.health_status.dws_status}
                </div>
                {schedulerStatus.error_counts.dws > 0 && (
                  <div className="text-xs text-red-600 mt-1">
                    {schedulerStatus.error_counts.dws} errors
                  </div>
                )}
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Treasury Status</div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(schedulerStatus.health_status.treasury_status)}`}>
                  {schedulerStatus.health_status.treasury_status}
                </div>
                {schedulerStatus.error_counts.treasury > 0 && (
                  <div className="text-xs text-red-600 mt-1">
                    {schedulerStatus.error_counts.treasury} errors
                  </div>
                )}
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Correlation Status</div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(schedulerStatus.health_status.correlation_status)}`}>
                  {schedulerStatus.health_status.correlation_status}
                </div>
                {schedulerStatus.error_counts.correlation > 0 && (
                  <div className="text-xs text-red-600 mt-1">
                    {schedulerStatus.error_counts.correlation} errors
                  </div>
                )}
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Uptime</div>
                <div className="font-medium">
                  {schedulerStatus.health_status.uptime_seconds 
                    ? formatUptime(schedulerStatus.health_status.uptime_seconds)
                    : 'N/A'
                  }
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Total Errors: {schedulerStatus.health_status.total_errors}
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Manual Sync Controls */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Manual Data Synchronization</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button
              onClick={() => handleTriggerSync('all')}
              disabled={!!syncLoading}
              variant="primary"
              className="w-full"
            >
              {syncLoading === 'all' ? 'Syncing All...' : 'Sync All'}
            </Button>
            <Button
              onClick={() => handleTriggerSync('dws')}
              disabled={!!syncLoading}
              variant="secondary"
              className="w-full"
            >
              {syncLoading === 'dws' ? 'Syncing DWS...' : 'Sync DWS'}
            </Button>
            <Button
              onClick={() => handleTriggerSync('treasury')}
              disabled={!!syncLoading}
              variant="secondary"
              className="w-full"
            >
              {syncLoading === 'treasury' ? 'Syncing Treasury...' : 'Sync Treasury'}
            </Button>
            <Button
              onClick={() => handleTriggerSync('correlation')}
              disabled={!!syncLoading}
              variant="secondary"
              className="w-full"
            >
              {syncLoading === 'correlation' ? 'Correlating...' : 'Run Correlation'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Data Source Health */}
      {dataSourceHealth && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Data Source Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">DWS API</h4>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(dataSourceHealth.data_sources.dws_api.status)}`}>
                    {dataSourceHealth.data_sources.dws_api.status}
                  </div>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Response: {dataSourceHealth.data_sources.dws_api.response_time_ms}ms</div>
                  <div>Errors (24h): {dataSourceHealth.data_sources.dws_api.error_count_24h}</div>
                  <div>Last Fetch: {new Date(dataSourceHealth.data_sources.dws_api.last_successful_fetch).toLocaleTimeString()}</div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Treasury API</h4>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(dataSourceHealth.data_sources.treasury_api.status)}`}>
                    {dataSourceHealth.data_sources.treasury_api.status}
                  </div>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Response: {dataSourceHealth.data_sources.treasury_api.response_time_ms}ms</div>
                  <div>Errors (24h): {dataSourceHealth.data_sources.treasury_api.error_count_24h}</div>
                  <div>Last Fetch: {new Date(dataSourceHealth.data_sources.treasury_api.last_successful_fetch).toLocaleTimeString()}</div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Database</h4>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(dataSourceHealth.data_sources.database.status)}`}>
                    {dataSourceHealth.data_sources.database.status}
                  </div>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Pool: {dataSourceHealth.data_sources.database.connection_pool_used}/{dataSourceHealth.data_sources.database.connection_pool_size}</div>
                  <div>Query Time: {dataSourceHealth.data_sources.database.query_avg_time_ms}ms</div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Last Sync Results */}
      {lastSyncResults && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Last Sync Results</h3>
            <div className={`p-4 rounded-lg ${lastSyncResults.status === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex justify-between items-center mb-2">
                <span className={`font-medium ${lastSyncResults.status === 'success' ? 'text-green-800' : 'text-red-800'}`}>
                  {lastSyncResults.status === 'success' ? 'Success' : 'Error'}
                </span>
                <span className="text-sm text-gray-600">
                  {new Date(lastSyncResults.trigger_time).toLocaleString()}
                </span>
              </div>
              {lastSyncResults.error && (
                <div className="text-red-600 text-sm">{lastSyncResults.error}</div>
              )}
              {lastSyncResults.results && (
                <pre className="text-xs bg-white p-2 rounded border mt-2 overflow-auto max-h-32">
                  {JSON.stringify(lastSyncResults.results, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
