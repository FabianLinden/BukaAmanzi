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
          <button
            onClick={onShowReportForm}
            className="inline-flex items-center px-6 py-3 bg-water-blue-600 text-white rounded-lg hover:bg-water-blue-700 transition-colors"
          >
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Submit Community Report
          </button>
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
