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
    const totalBudget = projects.reduce((sum, p) => sum + p.budget, 0);
    const totalSpent = projects.reduce((sum, p) => sum + p.spent, 0);
    const avgProgress = projects.length > 0 ? projects.reduce((sum, p) => sum + p.progress, 0) / projects.length : 0;

    return {
      total,
      completed,
      inProgress,
      delayed,
      totalBudget,
      totalSpent,
      avgProgress,
      remaining: totalBudget - totalSpent,
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

  // Generate sample progress data for charts
  const progressData = useMemo(() => {
    if (projects.length === 0) return [];
    
    // Create sample historical data for the first project
    const sampleProject = projects[0];
    const startDate = new Date(sampleProject.startDate);
    const currentDate = new Date();
    const data = [];
    
    // Generate monthly progress data
    for (let d = new Date(startDate); d <= currentDate; d.setMonth(d.getMonth() + 1)) {
      const monthsFromStart = (d.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 30.44);
      const progress = Math.min(100, monthsFromStart * (sampleProject.progress / 12));
      
      data.push({
        date: d.toISOString(),
        progress: Math.round(progress),
        milestone: monthsFromStart % 3 === 0 ? `Milestone ${Math.floor(monthsFromStart / 3) + 1}` : undefined
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
            title="Sample Project Progress"
            projectName={projects.length > 0 ? projects[0].title : "No Projects"}
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

      {/* Project Status Distribution */}
      <div className="bg-gradient-to-br from-white to-ocean-50/60 p-6 rounded-lg shadow-lg border border-ocean-200/50 hover:shadow-xl transition-shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Status Distribution</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-water-blue-50 to-water-blue-100 rounded-lg border border-water-blue-200/30">
            <div className="text-2xl font-bold text-water-blue-700">
              {projects.filter(p => p.status === 'planned').length}
            </div>
            <div className="text-sm text-water-blue-800">Planned</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-ocean-50 to-ocean-100 rounded-lg border border-ocean-200/30">
            <div className="text-2xl font-bold text-ocean-700">{stats.inProgress}</div>
            <div className="text-sm text-ocean-800">In Progress</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-aqua-50 to-aqua-100 rounded-lg border border-aqua-200/30">
            <div className="text-2xl font-bold text-aqua-700">{stats.completed}</div>
            <div className="text-sm text-aqua-800">Completed</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200/30">
            <div className="text-2xl font-bold text-red-600">{stats.delayed}</div>
            <div className="text-sm text-red-700">Delayed</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200/30">
            <div className="text-2xl font-bold text-gray-700">
              {projects.filter(p => p.status === 'cancelled').length}
            </div>
            <div className="text-sm text-gray-700">Cancelled</div>
          </div>
        </div>
      </div>
    </div>
  );
};
