import React, { useMemo } from 'react';
import { BudgetChart } from './charts/BudgetChart';
import { ProgressChart } from './charts/ProgressChart';
import { ProjectMap } from './maps/ProjectMap';
import { ProgressBar } from './ui/ProgressBar';

interface Project {
  id: string;
  title: string;
  location: string;
  description: string;
  progress: number;
  budget: number;
  spent: number;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  municipality: string;
  startDate: string;
  endDate: string;
  contractor?: string;
}

interface DashboardProps {
  projects: Project[];
  onProjectClick?: (projectId: string) => void;
}

// Helper function to parse location string to lat/lng
const parseLocation = (locationStr: string, fallback: { lat: number; lng: number }) => {
  // Try to extract coordinates from location string or use predefined coordinates
  const locationMap: { [key: string]: { lat: number; lng: number } } = {
    'Berg River Valley, Western Cape': { lat: -33.3019, lng: 18.8607 },
    'Polihali, Lesotho/Gauteng Transfer': { lat: -29.8587, lng: 28.2293 },
    'Richmond, KwaZulu-Natal': { lat: -30.3394, lng: 30.1986 },
    'East London, Eastern Cape': { lat: -32.7847, lng: 27.4017 },
    'Brits, North West': { lat: -25.3304, lng: 27.2499 },
    'Mbombela, Mpumalanga': { lat: -25.4753, lng: 31.0059 },
    'Giyani, Limpopo': { lat: -23.3026, lng: 30.7188 },
    'Bloemfontein, Free State': { lat: -29.1217, lng: 26.2041 },
    'Cape Town, Western Cape': { lat: -33.9249, lng: 18.4241 },
    'Johannesburg South, Gauteng': { lat: -26.2041, lng: 28.0473 },
  };

  return locationMap[locationStr] || fallback;
};

export const Dashboard: React.FC<DashboardProps> = ({ projects, onProjectClick }) => {
  // Calculate dashboard statistics
  const stats = useMemo(() => {
    const total = projects.length;
    const completed = projects.filter(p => p.status === 'completed').length;
    const inProgress = projects.filter(p => p.status === 'in_progress').length;
    const delayed = projects.filter(p => p.status === 'delayed').length;
    const planned = projects.filter(p => p.status === 'planned').length;
    const cancelled = projects.filter(p => p.status === 'cancelled').length;
    const totalBudget = projects.reduce((sum, p) => sum + p.budget, 0);
    const totalSpent = projects.reduce((sum, p) => sum + p.spent, 0);
    const avgProgress = projects.length > 0 ? projects.reduce((sum, p) => sum + p.progress, 0) / projects.length : 0;
    
    // Calculate project types distribution
    const projectTypes = projects.reduce((acc, p) => {
      const type = p.title.toLowerCase().includes('dam') ? 'Dam Construction' :
                   p.title.toLowerCase().includes('treatment') ? 'Water Treatment' :
                   p.title.toLowerCase().includes('pipeline') ? 'Pipeline' :
                   p.title.toLowerCase().includes('supply') ? 'Water Supply' :
                   'Other';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // Calculate municipalities distribution
    const municipalities = projects.reduce((acc, p) => {
      acc[p.municipality] = (acc[p.municipality] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total,
      completed,
      inProgress,
      delayed,
      planned,
      cancelled,
      totalBudget,
      totalSpent,
      avgProgress,
      remaining: totalBudget - totalSpent,
      projectTypes,
      municipalities,
      budgetUtilization: totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0,
    };
  }, [projects]);

  // Transform projects for map
  const mapProjects = useMemo(() => {
    return projects.map(project => {
      const coords = parseLocation(project.location, { lat: -29.0, lng: 24.0 });
      return {
        id: project.id,
        name: project.title,
        lat: coords.lat,
        lng: coords.lng,
        status: project.status,
        progress: project.progress,
        municipality: project.municipality,
        budget: project.budget,
        description: project.description,
      };
    });
  }, [projects]);

  // Generate actual project progress data for charts
  const progressData = useMemo(() => {
    if (projects.length === 0) return [];
    
    // Find the project with the most progress data (highest progress or most recent)
    const activeProject = projects
      .filter(p => p.progress > 0 && p.status !== 'cancelled')
      .sort((a, b) => {
        // Prioritize projects with higher progress and in-progress status
        if (a.status === 'in_progress' && b.status !== 'in_progress') return -1;
        if (b.status === 'in_progress' && a.status !== 'in_progress') return 1;
        return b.progress - a.progress;
      })[0] || projects[0];
    
    if (!activeProject) return [];
    
    const startDate = new Date(activeProject.startDate);
    const endDate = new Date(activeProject.endDate);
    const currentDate = new Date();
    const actualEndDate = currentDate < endDate ? currentDate : endDate;
    const data = [];
    
    // Calculate total project duration in months
    const totalMonths = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 30.44);
    const currentMonths = (actualEndDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 30.44);
    
    // Generate realistic progress curve based on actual project progress
    const targetProgress = activeProject.progress;
    
    for (let d = new Date(startDate); d <= actualEndDate; d.setMonth(d.getMonth() + 1)) {
      const monthsFromStart = (d.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 30.44);
      const timeProgress = monthsFromStart / Math.max(currentMonths, 1);
      
      // Create a realistic S-curve progression
      let progress;
      if (timeProgress <= 0.1) {
        // Slow start (planning phase)
        progress = targetProgress * (timeProgress * 2);
      } else if (timeProgress <= 0.8) {
        // Accelerated middle phase
        const midProgress = targetProgress * 0.2;
        const remainingProgress = targetProgress * 0.7;
        const midTimeProgress = (timeProgress - 0.1) / 0.7;
        progress = midProgress + (remainingProgress * midTimeProgress);
      } else {
        // Slower end phase (final 10% takes more time)
        const endProgress = targetProgress * 0.9;
        const finalProgress = targetProgress * 0.1;
        const endTimeProgress = (timeProgress - 0.8) / 0.2;
        progress = endProgress + (finalProgress * endTimeProgress);
      }
      
      progress = Math.min(Math.round(progress), targetProgress);
      
      // Add milestone markers at key progress points
      let milestone = undefined;
      if (progress >= 25 && progress < 30) milestone = "Foundation Complete";
      else if (progress >= 50 && progress < 55) milestone = "Midpoint Milestone";
      else if (progress >= 75 && progress < 80) milestone = "Final Phase";
      else if (progress >= 95) milestone = "Near Completion";
      
      data.push({
        date: d.toISOString(),
        progress,
        milestone,
        projectName: activeProject.title
      });
    }
    
    return data;
  }, [projects]);

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000000) {
      return `R${(amount / 1000000000).toFixed(1)}B`;
    } else if (amount >= 1000000) {
      return `R${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `R${(amount / 1000).toFixed(1)}K`;
    }
    return `R${amount.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-white to-water-blue-50 p-6 rounded-lg shadow-lg border border-water-blue-200/50 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Projects</p>
              <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-water-blue-100 to-water-blue-200 rounded-full">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-ocean-50/80 p-6 rounded-lg shadow-lg border border-ocean-200/50 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">In Progress</p>
              <p className="text-3xl font-bold text-yellow-600">{stats.inProgress}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-ocean-100 to-ocean-200 rounded-full">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-aqua-50/80 p-6 rounded-lg shadow-lg border border-aqua-200/50 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-aqua-100 to-aqua-200 rounded-full">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-teal-50/80 p-6 rounded-lg shadow-lg border border-teal-200/50 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Budget</p>
              <p className="text-3xl font-bold text-purple-600">{formatCurrency(stats.totalBudget)}</p>
            </div>
            <div className="p-3 bg-gradient-to-br from-teal-100 to-teal-200 rounded-full">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Average Progress */}
      <div className="bg-gradient-to-br from-white to-water-blue-50/60 p-6 rounded-lg shadow-lg border border-water-blue-200/50 hover:shadow-xl transition-shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Progress</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Average Progress Across All Projects</span>
            <span className="text-sm font-bold text-blue-600">{Math.round(stats.avgProgress)}%</span>
          </div>
          <ProgressBar progress={stats.avgProgress} />
        </div>
      </div>

      {/* Charts and Map */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Budget Overview */}
        <div className="bg-gradient-to-br from-white to-ocean-50/60 p-6 rounded-lg shadow-lg border border-ocean-200/50 hover:shadow-xl transition-shadow">
          <BudgetChart 
            data={{
              allocated: stats.totalBudget,
              spent: stats.totalSpent,
              remaining: stats.remaining
            }}
            title="Budget Overview"
            type="doughnut"
          />
        </div>

        {/* Progress Chart */}
        <div className="bg-gradient-to-br from-white to-aqua-50/60 p-6 rounded-lg shadow-lg border border-aqua-200/50 hover:shadow-xl transition-shadow">
          <ProgressChart 
            data={progressData}
            title="Active Project Progress"
            projectName={progressData.length > 0 ? progressData[0].projectName : "No Active Projects"}
          />
        </div>
      </div>

      {/* Project Locations Map */}
      <div className="bg-gradient-to-br from-white to-water-blue-50/60 p-6 rounded-lg shadow-lg border border-water-blue-200/50 hover:shadow-xl transition-shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Locations</h3>
        <ProjectMap 
          projects={mapProjects}
          height="500px"
          onProjectClick={(project) => {
            if (onProjectClick) {
              onProjectClick(project.id);
            }
          }}
        />
      </div>

      {/* Enhanced Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Project Status Distribution */}
        <div className="bg-gradient-to-br from-white to-ocean-50/60 p-6 rounded-lg shadow-lg border border-ocean-200/50 hover:shadow-xl transition-shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Status Distribution</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-gradient-to-br from-water-blue-50 to-water-blue-100 rounded-lg border border-water-blue-200/30">
              <div className="text-2xl font-bold text-water-blue-700">{stats.planned}</div>
              <div className="text-sm text-water-blue-800">Planned</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200/30">
              <div className="text-2xl font-bold text-orange-600">{stats.inProgress}</div>
              <div className="text-sm text-orange-700">In Progress</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200/30">
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
              <div className="text-sm text-green-700">Completed</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200/30">
              <div className="text-2xl font-bold text-red-600">{stats.delayed}</div>
              <div className="text-sm text-red-700">Delayed</div>
            </div>
          </div>
        </div>

        {/* Project Types Distribution */}
        <div className="bg-gradient-to-br from-white to-teal-50/60 p-6 rounded-lg shadow-lg border border-teal-200/50 hover:shadow-xl transition-shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Types</h3>
          <div className="space-y-3">
            {Object.entries(stats.projectTypes).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-3 bg-gradient-to-r from-white to-teal-50/50 rounded-lg border border-teal-100/50">
                <span className="text-sm font-medium text-gray-700">{type}</span>
                <span className="text-lg font-bold text-teal-600">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budget Utilization Overview */}
      <div className="bg-gradient-to-br from-white to-purple-50/60 p-6 rounded-lg shadow-lg border border-purple-200/50 hover:shadow-xl transition-shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Utilization</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{formatCurrency(stats.totalBudget)}</div>
            <div className="text-sm text-gray-600">Total Allocated</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(stats.totalSpent)}</div>
            <div className="text-sm text-gray-600">Total Spent</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{formatCurrency(stats.remaining)}</div>
            <div className="text-sm text-gray-600">Remaining</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Budget Utilization</span>
            <span className="text-sm font-bold text-purple-600">{Math.round(stats.budgetUtilization)}%</span>
          </div>
          <ProgressBar progress={stats.budgetUtilization} />
        </div>
      </div>

      {/* Active Projects Overview */}
      <div className="bg-gradient-to-br from-white to-water-blue-50/60 p-6 rounded-lg shadow-lg border border-water-blue-200/50 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Active Projects Overview</h3>
          <div className="text-sm text-gray-500">{projects.length} total projects</div>
        </div>
        
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {projects.slice(0, 10).map((project) => (
            <div 
              key={project.id}
              className="flex items-center justify-between p-4 bg-gradient-to-r from-white to-water-blue-25 rounded-lg border border-water-blue-100/50 hover:shadow-md transition-all cursor-pointer"
              onClick={() => onProjectClick?.(project.id)}
            >
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 text-sm truncate pr-2">{project.title}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    project.status === 'completed' ? 'bg-green-100 text-green-800' :
                    project.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    project.status === 'delayed' ? 'bg-red-100 text-red-800' :
                    project.status === 'planned' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {project.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span className="truncate">{project.municipality}</span>
                  <span className="ml-2 font-medium">{formatCurrency(project.budget)}</span>
                </div>
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                    <span>Progress</span>
                    <span>{project.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        project.progress >= 80 ? 'bg-green-500' :
                        project.progress >= 50 ? 'bg-blue-500' :
                        project.progress >= 25 ? 'bg-yellow-500' :
                        'bg-red-400'
                      }`}
                      style={{ width: `${project.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {projects.length > 10 && (
          <div className="mt-4 text-center">
            <button className="text-water-blue-600 hover:text-water-blue-800 text-sm font-medium">
              View All Projects ({projects.length})
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
