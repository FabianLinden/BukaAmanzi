import React from 'react';
import { ProjectCard } from './ProjectCard';

type Project = {
  id: string;
  title: string;
  location: string;
  description: string;
  longDescription: string;
  progress: number;
  budget: number;
  spent: number;
  startDate: string;
  endDate: string;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  contractor?: string;
  municipality: string;
  lastUpdated: string;
  milestones: Array<{
    id: string;
    title: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'delayed';
    dueDate: string;
    completedDate?: string;
  }>;
  documents: Array<{
    id: string;
    title: string;
    type: 'report' | 'contract' | 'permit' | 'other';
    url: string;
    uploadedAt: string;
  }>;
  updates: Array<{
    id: string;
    title: string;
    description: string;
    date: string;
    author: string;
  }>;
};

type ProjectsViewProps = {
  projects: Project[];
  searchQuery: string;
  onViewDetails: (projectId: string) => void;
  onProvideFeedback: (projectId: string) => void;
  onShowReportForm: () => void;
  onClearSearch: () => void;
};

export const ProjectsView: React.FC<ProjectsViewProps> = ({
  projects,
  searchQuery,
  onViewDetails,
  onProvideFeedback,
  onShowReportForm,
  onClearSearch
}) => {
  // Filter projects based on search query
  const filteredProjects = projects.filter(project =>
    searchQuery === '' ||
    project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.municipality.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.contractor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (filteredProjects.length > 0) {
    return (
      <div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              {...project}
              onViewDetails={onViewDetails}
              onProvideFeedback={onProvideFeedback}
            />
          ))}
        </div>
        
        {/* Add Report Button */}
        <div className="mt-8 text-center">
          <div className="bg-gradient-to-r from-water-blue-50 to-ocean-50 p-6 rounded-xl border border-water-blue-200/50">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Submit a Community Report</h3>
            <p className="text-gray-600 mb-4">Report issues, provide updates, or share feedback about any water infrastructure project in your community.</p>
            <p className="text-sm text-gray-500 mb-4">Click on "Provide Feedback" button on any project card above, or the "Provide Feedback" button in the project details page.</p>
            <div className="flex items-center justify-center space-x-2 text-water-blue-600">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium">Select a project above to get started</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="text-center py-8 text-gray-500">
      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p className="mt-2">{searchQuery ? `No projects found matching "${searchQuery}"` : 'No projects found'}</p>
      {searchQuery && (
        <button 
          onClick={onClearSearch}
          className="mt-2 text-water-blue-600 hover:text-water-blue-800 underline"
        >
          Clear search
        </button>
      )}
    </div>
  );
};
