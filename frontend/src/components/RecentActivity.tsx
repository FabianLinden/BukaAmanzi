import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';

interface RecentChange {
  id: string;
  entity_type: string;
  entity_id: string;
  change_type: string;
  source: string;
  created_at: string;
  field_changes: string[];
}

interface ETLStatus {
  status: string;
  total_projects: number;
  total_municipalities: number;
  recent_changes: RecentChange[];
}

interface RecentActivityProps {
  className?: string;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ className = '' }) => {
  const [etlStatus, setEtlStatus] = useState<ETLStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecentActivity = async () => {
    try {
      const response = await fetch(`http://${window.location.hostname}:8000/api/v1/etl/status`);
      if (!response.ok) throw new Error('Failed to fetch recent activity');
      const data = await response.json();
      setEtlStatus(data);
    } catch (err) {
      console.error('Error fetching recent activity:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecentActivity();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchRecentActivity, 30000);
    return () => clearInterval(interval);
  }, []);

  const getChangeTypeColor = (changeType: string) => {
    switch (changeType.toLowerCase()) {
      case 'created': return 'border-green-500 bg-green-50';
      case 'updated': return 'border-blue-500 bg-blue-50';
      case 'deleted': return 'border-red-500 bg-red-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getEntityIcon = (entityType: string) => {
    switch (entityType.toLowerCase()) {
      case 'project':
        return (
          <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        );
      case 'municipality':
        return (
          <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l7-3 7 3z" />
          </svg>
        );
      case 'financial_data':
        return (
          <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <Card className={className}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-water-blue-600"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-8 text-red-500">
          <svg className="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="text-sm">Unable to load recent activity</p>
          <button 
            onClick={fetchRecentActivity}
            className="mt-2 text-water-blue-600 hover:text-water-blue-800 underline text-sm"
          >
            Try again
          </button>
        </div>
      </Card>
    );
  }

  const recentChanges = etlStatus?.recent_changes || [];

  return (
    <Card className={className}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-500">Live</span>
        </div>
      </div>
      
      {etlStatus && (
        <div className="text-sm text-gray-600 mb-4">
          {etlStatus.total_projects} projects across {etlStatus.total_municipalities} municipalities
        </div>
      )}

      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {recentChanges.length > 0 ? (
          recentChanges.map((change) => (
            <div 
              key={change.id} 
              className={`border-l-4 pl-4 py-3 rounded-r-lg transition-colors hover:bg-opacity-70 ${
                getChangeTypeColor(change.change_type)
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start space-x-3">
                  {getEntityIcon(change.entity_type)}
                  <div>
                    <div className="font-medium text-gray-900 capitalize">
                      {change.entity_type.replace('_', ' ')} {change.change_type}
                    </div>
                    <div className="text-sm text-gray-600">
                      Source: {change.source}
                    </div>
                    {change.field_changes.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {change.field_changes.slice(0, 3).map((field, index) => (
                          <span 
                            key={index} 
                            className="bg-water-blue-100 text-water-blue-800 px-2 py-1 rounded text-xs"
                          >
                            {field}
                          </span>
                        ))}
                        {change.field_changes.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{change.field_changes.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                  {formatTimeAgo(change.created_at)}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">No recent activity</p>
            <p className="text-xs text-gray-400 mt-1">Activity will appear here as data changes</p>
          </div>
        )}
      </div>

      {recentChanges.length > 5 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button className="text-sm text-water-blue-600 hover:text-water-blue-800 font-medium">
            View all activity →
          </button>
        </div>
      )}
    </Card>
  );
};
