import React, { useMemo } from 'react';
import { 
  categorizeProjects, 
  getProjectQualityStats, 
  enhanceProjectData,
  ProjectValidationResult
} from '../utils/projectDataUtils';

interface DataQualityDashboardProps {
  projects: any[];
}

interface QualityIssue {
  id: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  count: number;
  projects: any[];
}

export const DataQualityDashboard: React.FC<DataQualityDashboardProps> = ({ projects }) => {
  const analysis = useMemo(() => {
    const enhanced = projects.map(enhanceProjectData);
    const categorized = categorizeProjects(projects);
    const qualityStats = getProjectQualityStats(projects);
    
    // Identify specific data quality issues
    const issues: QualityIssue[] = [];
    
    // Generic names issue
    const genericNameProjects = enhanced.filter(p => p._hasGenericName);
    if (genericNameProjects.length > 0) {
      issues.push({
        id: 'generic_names',
        title: 'Generic or Placeholder Project Names',
        description: 'Projects with generic names like "District MunicipalityProject" that appear to be test data',
        severity: 'high',
        count: genericNameProjects.length,
        projects: genericNameProjects
      });
    }
    
    // Missing locations issue
    const noLocationProjects = enhanced.filter(p => !p._hasValidLocation);
    if (noLocationProjects.length > 0) {
      issues.push({
        id: 'missing_locations',
        title: 'Missing Location Data',
        description: 'Projects without valid address or coordinate information',
        severity: 'high',
        count: noLocationProjects.length,
        projects: noLocationProjects
      });
    }
    
    // Missing dates issue
    const noDateProjects = enhanced.filter(p => !p.start_date || !p.end_date);
    if (noDateProjects.length > 0) {
      issues.push({
        id: 'missing_dates',
        title: 'Missing Project Dates',
        description: 'Projects without proper start or end dates',
        severity: 'medium',
        count: noDateProjects.length,
        projects: noDateProjects
      });
    }
    
    // Missing budget information
    const noBudgetProjects = enhanced.filter(p => !p.budget_allocated || p.budget_allocated === 0);
    if (noBudgetProjects.length > 0) {
      issues.push({
        id: 'missing_budget',
        title: 'Missing Budget Information',
        description: 'Projects without budget allocation data',
        severity: 'medium',
        count: noBudgetProjects.length,
        projects: noBudgetProjects
      });
    }
    
    // Missing descriptions
    const noDescriptionProjects = enhanced.filter(p => !p.description || p.description.trim() === '');
    if (noDescriptionProjects.length > 0) {
      issues.push({
        id: 'missing_descriptions',
        title: 'Missing Project Descriptions',
        description: 'Projects without proper descriptions',
        severity: 'low',
        count: noDescriptionProjects.length,
        projects: noDescriptionProjects
      });
    }
    
    return {
      enhanced,
      categorized,
      qualityStats,
      issues: issues.sort((a, b) => {
        const severityWeight = { high: 3, medium: 2, low: 1 };
        return severityWeight[b.severity] - severityWeight[a.severity] || b.count - a.count;
      })
    };
  }, [projects]);

  const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getSeverityIcon = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': 
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'medium':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case 'low':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-white to-green-50 p-6 rounded-lg shadow-lg border border-green-200/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Complete Projects</p>
              <p className="text-3xl font-bold text-green-600">{analysis.categorized.complete.length}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-green-100 to-green-200 rounded-full">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-red-50 p-6 rounded-lg shadow-lg border border-red-200/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Incomplete Projects</p>
              <p className="text-3xl font-bold text-red-600">{analysis.categorized.incomplete.length}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-red-100 to-red-200 rounded-full">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-blue-50 p-6 rounded-lg shadow-lg border border-blue-200/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Data Completeness</p>
              <p className="text-3xl font-bold text-blue-600">
                {Math.round(analysis.categorized.statistics.completePercentage)}%
              </p>
            </div>
            <div className="p-3 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-purple-50 p-6 rounded-lg shadow-lg border border-purple-200/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Data Issues Found</p>
              <p className="text-3xl font-bold text-purple-600">{analysis.issues.length}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-purple-100 to-purple-200 rounded-full">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality Distribution */}
      <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Quality Distribution</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200/30">
            <div className="text-2xl font-bold text-green-600">{analysis.qualityStats.high}</div>
            <div className="text-sm text-green-700">High Quality</div>
            <div className="text-xs text-gray-500 mt-1">≥90% complete</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg border border-yellow-200/30">
            <div className="text-2xl font-bold text-yellow-600">{analysis.qualityStats.medium}</div>
            <div className="text-sm text-yellow-700">Medium Quality</div>
            <div className="text-xs text-gray-500 mt-1">70-89% complete</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200/30">
            <div className="text-2xl font-bold text-red-600">{analysis.qualityStats.low}</div>
            <div className="text-sm text-red-700">Low Quality</div>
            <div className="text-xs text-gray-500 mt-1">&lt;70% complete</div>
          </div>
        </div>
      </div>

      {/* Data Quality Issues */}
      <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Quality Issues</h3>
        {analysis.issues.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="mt-2">No data quality issues found!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {analysis.issues.map((issue) => (
              <div
                key={issue.id}
                className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      {getSeverityIcon(issue.severity)}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{issue.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{issue.description}</p>
                      <p className="text-sm font-medium mt-2">
                        Affects {issue.count} project{issue.count !== 1 ? 's' : ''} 
                        ({Math.round((issue.count / projects.length) * 100)}% of total)
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                      issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {issue.severity} priority
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommendations */}
      {analysis.issues.length > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Recommendations
          </h3>
          <div className="space-y-3 text-sm text-gray-700">
            <p>• <strong>Data ETL Process:</strong> Review the data extraction and loading process to filter out test/placeholder data</p>
            <p>• <strong>Data Validation:</strong> Implement validation rules to ensure data completeness before ingestion</p>
            <p>• <strong>User Experience:</strong> Consider showing only complete projects by default in the main interface</p>
            <p>• <strong>Data Cleanup:</strong> Consider removing or flagging the {analysis.categorized.incomplete.length} incomplete projects to improve user experience</p>
          </div>
        </div>
      )}
    </div>
  );
};
