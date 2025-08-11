import React, { useEffect, useState } from 'react';
import { create } from 'zustand';
import { ProjectCard } from './components/ProjectCard';
import { ProjectDetails } from './components/ProjectDetails';
import { ProjectsView } from './components/ProjectsView';
import { WaterWave } from './components/WaterWave';
import { WaterBubbles } from './components/WaterBubbles';
import { WaterDroplet } from './components/WaterDroplet';
import { Dashboard } from './components/Dashboard';
import { CommunityReportForm } from './components/CommunityReportForm';
import { DataSyncDashboard } from './components/DataSyncDashboard';
import { ProjectCorrelationAnalysis } from './components/ProjectCorrelationAnalysis';
import { MunicipalInvestmentOverview } from './components/MunicipalInvestmentOverview';
import { useWebSocket } from './hooks/useWebSocket';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

// Types
type Notification = {
  type: string;
  timestamp: string;
  data?: any;
};

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

type AppState = {
  notifications: Notification[];
  projects: Project[];
  selectedProject: Project | null;
  addNotification: (n: Notification) => void;
  setProjects: (projects: Project[]) => void;
  setSelectedProject: (project: Project | null) => void;
};

const useAppStore = create<AppState>((set: (partial: Partial<AppState> | ((state: AppState) => Partial<AppState>)) => void) => ({
  notifications: [],
  projects: [],
  selectedProject: null,
  addNotification: (n: Notification) => set((s: AppState) => ({ 
    notifications: [n, ...s.notifications].slice(0, 50) 
  })),
  setProjects: (projects: Project[]) => set({ projects }),
  setSelectedProject: (project: Project | null) => set({ selectedProject: project }),
}));

// Mock data for demonstration
const mockProjects: Project[] = [
  {
    id: '1',
    title: 'Rustic Water Treatment Plant Upgrade',
    location: 'Rustic Valley, Western Cape',
    description: 'Upgrading the existing water treatment plant to increase capacity and improve water quality.',
    longDescription: 'This project involves the comprehensive upgrade of the Rustic Valley Water Treatment Plant to meet the growing demand for clean water in the region. The upgrade includes the installation of advanced filtration systems, expansion of storage capacity, and implementation of modern water treatment technologies to ensure compliance with national water quality standards.',
    progress: 65,
    budget: 24500000,
    spent: 15925000,
    startDate: '2023-03-15',
    endDate: '2024-08-30',
    status: 'in_progress',
    contractor: 'AquaTech Solutions',
    municipality: 'Rustic Valley Municipality',
    lastUpdated: new Date().toISOString(),
    milestones: [
      {
        id: 'm1',
        title: 'Design Phase Complete',
        description: 'Finalize all engineering designs and obtain necessary approvals.',
        status: 'completed',
        dueDate: '2023-05-30',
        completedDate: '2023-05-25',
      },
      {
        id: 'm2',
        title: 'Phase 1 Construction',
        description: 'Complete civil works and structural foundations.',
        status: 'completed',
        dueDate: '2023-09-15',
        completedDate: '2023-09-10',
      },
      {
        id: 'm3',
        title: 'Equipment Installation',
        description: 'Install new filtration and treatment equipment.',
        status: 'in_progress',
        dueDate: '2024-02-28',
      },
      {
        id: 'm4',
        title: 'Testing & Commissioning',
        description: 'Test all systems and commission the upgraded plant.',
        status: 'pending',
        dueDate: '2024-07-15',
      },
    ],
    documents: [
      {
        id: 'd1',
        title: 'Project Scope Document',
        type: 'report',
        url: '#',
        uploadedAt: '2023-03-10',
      },
      {
        id: 'd2',
        title: 'Environmental Impact Assessment',
        type: 'report',
        url: '#',
        uploadedAt: '2023-04-05',
      },
    ],
    updates: [
      {
        id: 'u1',
        title: 'Equipment Delivery Delayed',
        description: 'The delivery of the new filtration units has been delayed by two weeks due to shipping delays.',
        date: '2023-11-15T14:30:00',
        author: 'John Smith',
      },
      {
        id: 'u2',
        title: 'Phase 1 Construction Completed',
        description: 'Successfully completed all civil works ahead of schedule.',
        date: '2023-09-10T11:15:00',
        author: 'Sarah Johnson',
      },
    ],
  },
  // Add more mock projects as needed
];

export default function App() {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showNotifications, setShowNotifications] = useState<boolean>(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [currentView, setCurrentView] = useState<'projects' | 'dashboard' | 'data-sync' | 'correlation' | 'municipal-overview'>('projects');
  const [showReportForm, setShowReportForm] = useState(false);
  const [reportFormProject, setReportFormProject] = useState<{ id: string; name: string } | null>(null);
  const [selectedMunicipalityId, setSelectedMunicipalityId] = useState<string | null>(null);
  
  const {
    notifications,
    projects,
    selectedProject,
    addNotification,
    setProjects,
    setSelectedProject
  } = useAppStore();

  // Handle WebSocket messages
  const handleWebSocketMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      
      if (data.type === 'project_update') {
        setProjects(data.payload);
      } else if (data.type === 'notification') {
        addNotification({
          type: data.notification_type,
          timestamp: new Date().toISOString(),
          data: data.data
        });
      }
    } catch (error: unknown) {
      console.error('Error processing WebSocket message:', error);
    }
  };

  // Initialize WebSocket connection
  const { send } = useWebSocket(
    `ws://${window.location.hostname}:8000/ws/projects`,
    {
      onOpen: () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        send({ action: 'subscribe', entity_type: 'all' });
      },
      onMessage: handleWebSocketMessage,
      onClose: () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      }
    }
  );

// Load initial data from API
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await fetch(`http://${window.location.hostname}:8000/api/v1/projects`);
        if (response.ok) {
          const apiProjects = await response.json();
          // Transform API data to match frontend interface
          const transformedProjects = apiProjects.map((proj: any) => ({
            id: proj.id,
            title: proj.name,
            location: proj.address || 'Location not specified',
            description: proj.description || 'No description available',
            longDescription: proj.description || 'No detailed description available',
            progress: proj.progress_percentage || 0,
            budget: proj.budget_allocated || 0,
            spent: proj.budget_spent || 0,
            startDate: proj.start_date || new Date().toISOString().split('T')[0],
            endDate: proj.end_date || new Date().toISOString().split('T')[0],
            status: proj.status as 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled',
            contractor: proj.contractor || 'Not specified',
            municipality: proj.municipality_name || 'Unknown Municipality',
            lastUpdated: proj.updated_at || new Date().toISOString(),
            milestones: [],
            documents: [],
            updates: []
          }));
          setProjects(transformedProjects);
        } else {
          console.error('Failed to load projects from API, using mock data');
          setProjects(mockProjects);
        }
      } catch (error) {
        console.error('Error loading projects:', error);
        setProjects(mockProjects);
      }
    };
    
    loadProjects();
  }, [setProjects]);

  const handleViewDetails = (projectId: string) => {
    const project = projects.find((p: Project) => p.id === projectId) || null;
    setSelectedProject(project);
    window.scrollTo({ top: 0, behavior: 'smooth' as ScrollBehavior });
  };

  const handleBackToList = () => {
    setSelectedProject(null);
  };

  const handleProvideFeedback = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setReportFormProject({ id: project.id, name: project.title });
      setShowReportForm(true);
    }
  };

  const handleSubmitReport = async (reportData: any) => {
    try {
      const response = await fetch(`http://${window.location.hostname}:8000/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      });
      
      if (response.ok) {
        addNotification({
          type: 'Report Submitted',
          timestamp: new Date().toISOString(),
          data: { message: 'Your community report has been submitted successfully' }
        });
        setShowReportForm(false);
        setReportFormProject(null);
      } else {
        throw new Error('Failed to submit report');
      }
    } catch (error) {
      console.error('Error submitting report:', error);
      throw error;
    }
  };

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  if (selectedProject) {
    return (
      <ProjectDetails 
        project={selectedProject} 
        onBack={handleBackToList}
        onProvideFeedback={handleProvideFeedback}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-water-blue-50 via-aqua-50/30 to-white">
      {/* Header */}
      <header className="relative bg-gradient-to-br from-water-blue-600 via-ocean-600 to-water-blue-800 text-white overflow-hidden">
        {/* Animated Background Elements */}
        <div className="absolute inset-0">
          <WaterWave className="w-full h-full" color="#ffffff" opacity={0.15} speed="slow" variant="wave" />
          <WaterBubbles count={12} className="opacity-20" />
        </div>
        
        {/* Decorative Water Droplets */}
        <div className="absolute top-8 left-1/4 opacity-30">
          <WaterDroplet size="lg" delay={500} />
        </div>
        <div className="absolute top-16 right-1/3 opacity-25">
          <WaterDroplet size="md" delay={1000} />
        </div>
        <div className="absolute top-12 left-3/4 opacity-35">
          <WaterDroplet size="sm" delay={1500} />
        </div>
        
        <div className="relative z-10 container mx-auto px-4 py-16">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
            <div className="mb-8 md:mb-0">
              <div className="flex items-center mb-4">
                {/* Water Drop Logo */}
                <div className="w-12 h-14 mr-4 bg-gradient-to-b from-water-blue-200 to-water-blue-400 rounded-full relative animate-droplet" 
                  style={{ borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%' }}>
                  <div className="absolute top-2 left-2 w-3 h-3 bg-white/50 rounded-full blur-sm" />
                </div>
                <div>
                  <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-white to-water-blue-100 bg-clip-text text-transparent">
                    Buka Amanzi
                  </h1>
                  <div className="text-sm font-medium text-water-blue-200 tracking-wider">WATER WATCH</div>
                </div>
              </div>
              <p className="text-lg text-water-blue-100 max-w-lg leading-relaxed">
                Monitoring water infrastructure projects across South Africa with transparency and community engagement
              </p>
            </div>
            
            {/* Connection Status Card with animations */}
            <div className="bg-white/15 backdrop-blur-md rounded-xl p-6 border border-white/20 animate-float">
              <div className="text-sm text-water-blue-100 mb-3 font-medium">System Status</div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`h-3 w-3 rounded-full mr-3 animate-pulse ${
                    connectionStatus === 'connected' ? 'bg-emerald-400 animate-glow-pulse' : 
                    connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
                  }`} />
                  <div>
                    <span className="text-sm font-medium text-white block">
                      {connectionStatus === 'connected' ? 'Live Data' : 
                       connectionStatus === 'connecting' ? 'Connecting...' : 'Offline'}
                    </span>
                    <span className="text-xs text-water-blue-200">
                      {projects.length} active projects
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-water-blue-200">Last update</div>
                  <div className="text-sm font-medium text-white">Just now</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Enhanced Bottom Wave */}
        <div className="relative h-20 md:h-28 -mb-1">
          <WaterWave className="w-full h-full" color="#ffffff" opacity={0.4} speed="normal" variant="wave" />
          <div className="absolute inset-0">
            <WaterWave className="w-full h-full" color="#87eaff" opacity={0.2} speed="fast" variant="flow" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 -mt-12 relative z-10">
        <div className="bg-gradient-to-br from-white to-water-blue-50 rounded-xl shadow-lg overflow-hidden mb-8 border border-water-blue-100/50">
          <div className="p-6">
            {/* Tab Navigation */}
            <div className="flex flex-wrap gap-1 bg-gradient-to-r from-water-blue-100/80 to-aqua-100/80 backdrop-blur-sm rounded-lg p-1 mb-6 border border-water-blue-200/30">
              <button
                onClick={() => setCurrentView('projects')}
                className={`flex-1 min-w-fit py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'projects'
                    ? 'bg-gradient-to-r from-white to-water-blue-50 text-water-blue-800 shadow-md border border-water-blue-200/30'
                    : 'text-ocean-600 hover:text-ocean-800 hover:bg-white/60'
                }`}
              >
                Projects
              </button>
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`flex-1 min-w-fit py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'dashboard'
                    ? 'bg-gradient-to-r from-white to-water-blue-50 text-water-blue-800 shadow-md border border-water-blue-200/30'
                    : 'text-ocean-600 hover:text-ocean-800 hover:bg-white/60'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('data-sync')}
                className={`flex-1 min-w-fit py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'data-sync'
                    ? 'bg-gradient-to-r from-white to-water-blue-50 text-water-blue-800 shadow-md border border-water-blue-200/30'
                    : 'text-ocean-600 hover:text-ocean-800 hover:bg-white/60'
                }`}
              >
                Data Sync
              </button>
              <button
                onClick={() => setCurrentView('correlation')}
                className={`flex-1 min-w-fit py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'correlation'
                    ? 'bg-gradient-to-r from-white to-water-blue-50 text-water-blue-800 shadow-md border border-water-blue-200/30'
                    : 'text-ocean-600 hover:text-ocean-800 hover:bg-white/60'
                }`}
              >
                Analysis
              </button>
            </div>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {currentView === 'projects' && 'Active Projects'}
                  {currentView === 'dashboard' && 'Dashboard'}
                  {currentView === 'data-sync' && 'Data Synchronization'}
                  {currentView === 'correlation' && 'Correlation Analysis'}
                  {currentView === 'municipal-overview' && 'Municipal Overview'}
                </h2>
                <div className="flex items-center">
                  <span className={`h-3 w-3 rounded-full mr-2 ${
                    connectionStatus === 'connected' ? 'bg-green-500' : 
                    connectionStatus === 'connecting' ? 'bg-yellow-500' : 
                    'bg-red-500'
                  }`}></span>
                  <span className="text-sm text-gray-500">
                    {connectionStatus === 'connected' ? 'Connected' : 
                     connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search projects..."
                    className="px-4 py-2 pr-10 rounded-lg border border-water-blue-300/60 bg-gradient-to-r from-white to-water-blue-50/80 focus:outline-none focus:ring-2 focus:ring-water-blue-500 focus:border-water-blue-400 focus:bg-white transition-all"
                    value={searchQuery}
                    onChange={handleSearchInputChange}
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-2 rounded-full hover:bg-water-blue-100 text-water-blue-700 focus:outline-none focus:ring-2 focus:ring-water-blue-500"
                  aria-label="Notifications"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {notifications.length > 0 && (
                    <span className="absolute top-0 right-0 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.length}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {currentView === 'projects' && (
              <ProjectsView 
                projects={projects}
                searchQuery={searchQuery}
                onViewDetails={handleViewDetails}
                onProvideFeedback={handleProvideFeedback}
                onShowReportForm={() => setShowReportForm(true)}
                onClearSearch={() => setSearchQuery('')}
              />
            )}
            
            {currentView === 'dashboard' && (
              <Dashboard projects={projects} onViewProjectDetails={handleViewDetails} />
            )}
            
            {currentView === 'data-sync' && (
              <DataSyncDashboard />
            )}
            
            {currentView === 'correlation' && (
              <ProjectCorrelationAnalysis />
            )}
            
            {currentView === 'municipal-overview' && (
              <MunicipalInvestmentOverview />
            )}
          </div>
        </div>
      </main>

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed top-20 right-4 w-96 max-w-full z-50">
            <div className="bg-gradient-to-br from-white to-ocean-50 rounded-xl shadow-2xl overflow-hidden border border-water-blue-200/60 backdrop-blur-md">
              <div className="p-4 bg-gradient-to-r from-water-blue-50 to-aqua-50 border-b border-water-blue-200/50">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {notifications.length > 0 ? (
                notifications.map((notification: Notification, idx: number) => (
                  <div key={idx} className="border-b border-water-blue-100/60 p-4 hover:bg-water-blue-50/50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{notification.type}</p>
                        {notification.data && (
                          <p className="text-sm text-gray-600 mt-1">
                            {typeof notification.data === 'object' 
                              ? notification.data.message || JSON.stringify(notification.data, null, 2)
                              : notification.data}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                        {new Date(notification.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  <p className="mt-2">No notifications yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity Section */}
      <div className="container mx-auto px-4 pb-8">
        <div className="bg-gradient-to-br from-white to-ocean-50/60 rounded-xl shadow-lg overflow-hidden border border-water-blue-100/50">
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
              {notifications.length > 0 ? (
                notifications.map((notification: Notification, idx: number) => (
                  <div key={idx} className="border-l-4 border-gradient-to-b from-water-blue-500 to-ocean-500 pl-4 py-2 rounded-r-lg bg-gradient-to-r from-water-blue-50/30 to-transparent hover:from-water-blue-50/50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{notification.type}</p>
                        {notification.data && (
                          <p className="text-sm text-gray-600 mt-1">
                            {JSON.stringify(notification.data, null, 2)}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                        {new Date(notification.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  <p className="mt-2">No recent activity</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Community Report Form Modal */}
      {showReportForm && (
        <div className="fixed inset-0 bg-gradient-to-br from-water-blue-900/40 to-ocean-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-white to-water-blue-50/80 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-water-blue-200/50">
            <CommunityReportForm
              selectedProject={reportFormProject}
              onClose={() => {
                setShowReportForm(false);
                setReportFormProject(null);
              }}
              onSubmit={handleSubmitReport}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-gradient-to-r from-water-blue-900 via-ocean-900 to-water-blue-800 text-white py-8 mt-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h3 className="text-xl font-bold">Water Watch</h3>
              <p className="text-gray-400">Transparent water infrastructure monitoring</p>
            </div>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-300 hover:text-white">About</a>
              <a href="#" className="text-gray-300 hover:text-white">FAQ</a>
              <a href="#" className="text-gray-300 hover:text-white">Contact</a>
              <a href="#" className="text-gray-300 hover:text-white">API</a>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-6 pt-6 text-center md:text-left">
            <p className="text-gray-400 text-sm">
              &copy; {new Date().getFullYear()} Water Watch. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}