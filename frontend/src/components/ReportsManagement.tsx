import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';

interface Report {
  id: string;
  project_id: string;
  title: string;
  description: string;
  location?: string;
  address?: string;
  report_type: 'progress_update' | 'issue' | 'completion' | 'quality_concern';
  status: 'published' | 'under_review' | 'resolved';
  upvotes: number;
  downvotes: number;
  photos?: string[];
  contributor_name?: string;
  created_at: string;
}

interface Props {
  projectId?: string;
}

export const ReportsManagement: React.FC<Props> = ({ projectId }) => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: '',
    report_type: ''
  });

  const fetchReports = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId);
      if (filters.status) params.append('status', filters.status);
      if (filters.report_type) params.append('report_type', filters.report_type);

      const response = await fetch(`http://${window.location.hostname}:8000/api/v1/reports?${params}`);
      if (!response.ok) throw new Error('Failed to fetch reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [projectId, filters]);

  const handleVote = async (reportId: string, voteType: 'up' | 'down') => {
    try {
      const response = await fetch(`http://${window.location.hostname}:8000/api/v1/reports/${reportId}/vote?vote_type=${voteType}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to submit vote');
      
      // Refresh the reports to show the new vote count
      fetchReports(); 
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Vote submission failed');
    }
  };

  const getReportTypeColor = (type: string) => {
    switch (type) {
      case 'progress_update': return 'bg-blue-100 text-blue-800';
      case 'issue': return 'bg-yellow-100 text-yellow-800';
      case 'completion': return 'bg-green-100 text-green-800';
      case 'quality_concern': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800';
      case 'under_review': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
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
      <Card>
        <div className="p-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <h2 className="text-xl font-semibold">Community Reports</h2>
              <div className="flex flex-wrap gap-3">
                <select 
                  value={filters.report_type} 
                  onChange={e => setFilters({...filters, report_type: e.target.value})}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                    <option value="">All Types</option>
                    <option value="progress_update">Progress Update</option>
                    <option value="issue">Issue</option>
                    <option value="completion">Completion</option>
                    <option value="quality_concern">Quality Concern</option>
                </select>
                <select 
                  value={filters.status} 
                  onChange={e => setFilters({...filters, status: e.target.value})}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">All Statuses</option>
                    <option value="published">Published</option>
                    <option value="under_review">Under Review</option>
                    <option value="resolved">Resolved</option>
                </select>
              </div>
          </div>
        </div>
      </Card>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {reports.length === 0 ? (
        <Card>
          <div className="p-12 text-center text-gray-500">
            No community reports found.
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map(report => (
            <Card key={report.id} className="flex flex-col">
              <div className="p-6 flex-grow">
                <div className="flex justify-between items-start mb-3">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getReportTypeColor(report.report_type)}`}>
                    {report.report_type.replace('_', ' ')}
                  </span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                    {report.status.replace('_', ' ')}
                  </span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{report.title}</h3>
                <p className="text-sm text-gray-600 mb-4">{report.description}</p>
                
                {report.photos && report.photos.length > 0 && (
                    <div className="mb-4">
                        <img src={report.photos[0]} alt={report.title} className="rounded-lg w-full h-40 object-cover" />
                    </div>
                )}
              </div>
              <div className="p-6 bg-gray-50 border-t">
                  <div className="flex justify-between items-center text-sm text-gray-600">
                      <div>
                        <span>By: {report.contributor_name || 'Anonymous'}</span>
                        <div className="text-xs">{new Date(report.created_at).toLocaleDateString()}</div>
                      </div>
                      <div className="flex items-center gap-3">
                          <Button size="sm" variant="secondary" onClick={() => handleVote(report.id, 'up')}>
                            👍 {report.upvotes}
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => handleVote(report.id, 'down')}>
                            👎 {report.downvotes}
                          </Button>
                      </div>
                  </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
