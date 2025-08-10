import { useEffect, useState } from 'react';
import { ProgressBar } from './ui/ProgressBar';
import { Button } from './ui/Button';
import { WaterWave } from './WaterWave';

interface ProjectDetailsProps {
  project: {
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
  onBack: () => void;
  onProvideFeedback: (projectId: string) => void;
}

const statusColors = {
  planned: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-green-100 text-green-800',
  completed: 'bg-purple-100 text-purple-800',
  delayed: 'bg-yellow-100 text-yellow-800',
  cancelled: 'bg-red-100 text-red-800',
};

const statusLabels = {
  planned: 'Planned',
  in_progress: 'In Progress',
  completed: 'Completed',
  delayed: 'Delayed',
  cancelled: 'Cancelled',
};

export const ProjectDetails = ({ project, onBack, onProvideFeedback }: ProjectDetailsProps) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [waveHeight, setWaveHeight] = useState(0);
  
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const maxScroll = 200;
      const height = Math.min(scrollPosition / 5, 40);
      setWaveHeight(height);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-ZA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };
  
  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-ZA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const getTimeRemaining = (endDate: string) => {
    const now = new Date();
    const end = new Date(endDate);
    const diffTime = end.getTime() - now.getTime();
    
    if (diffTime <= 0) return { value: 0, unit: 'days', isOverdue: true };
    
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 30) {
      const months = Math.ceil(diffDays / 30);
      return { value: months, unit: months === 1 ? 'month' : 'months', isOverdue: false };
    } else if (diffDays > 0) {
      return { value: diffDays, unit: diffDays === 1 ? 'day' : 'days', isOverdue: false };
    } else {
      return { value: 0, unit: 'days', isOverdue: true };
    }
  };
  
  const timeRemaining = getTimeRemaining(project.endDate);
  
  return (
    <div className="relative min-h-screen bg-gray-50">
      {/* Header with Wave */}
      <div className="relative bg-gradient-to-r from-water-blue-600 to-water-blue-800 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <WaterWave className="w-full h-full" color="#ffffff" speed="normal" />
        </div>
        <div className="relative z-10 container mx-auto px-4 py-12">
          <div className="flex items-center mb-6">
            <button
              onClick={onBack}
              className="flex items-center text-white hover:text-water-blue-100 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Projects
            </button>
          </div>
          
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">{project.title}</h1>
              <div className="flex items-center text-water-blue-100">
                <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{project.location}</span>
              </div>
            </div>
            
            <div className="mt-4 md:mt-0 bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="text-sm text-water-blue-100 mb-2">Project Status</div>
              <div className="flex items-center">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  statusColors[project.status] || 'bg-gray-100 text-gray-800'
                }`}>
                  {statusLabels[project.status] || project.status}
                </span>
                <div className="ml-4">
                  <div className="text-sm text-water-blue-100">
                    {timeRemaining.isOverdue ? (
                      <span className="text-red-200">Overdue by {Math.abs(timeRemaining.value)} {timeRemaining.unit}</span>
                    ) : (
                      <span>{timeRemaining.value} {timeRemaining.unit} remaining</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Animated wave at the bottom of the header */}
        <div className="relative h-16 md:h-24 -mb-1" style={{ transform: `translateY(${waveHeight}px)` }}>
          <WaterWave className="w-full h-full" color="#ffffff" opacity={0.3} speed="normal" />
        </div>
      </div>
      
      {/* Main Content */}
      <div className="container mx-auto px-4 -mt-12 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
              <div className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Project Overview</h2>
                <p className="text-gray-700 mb-6">{project.longDescription || project.description}</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Start Date</h3>
                    <p className="text-gray-900">{formatDate(project.startDate)}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Estimated Completion</h3>
                    <p className="text-gray-900">{formatDate(project.endDate)}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Contractor</h3>
                    <p className="text-gray-900">{project.contractor || 'To be announced'}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Municipality</h3>
                    <p className="text-gray-900">{project.municipality}</p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-gray-700">Project Progress</span>
                    <span className="font-medium text-water-blue-700">{Math.round(project.progress)}%</span>
                  </div>
                  <ProgressBar value={project.progress} className="h-3" />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Budget</h3>
                    <div className="text-2xl font-bold text-gray-900">{formatCurrency(project.budget)}</div>
                    <div className="text-sm text-gray-500 mt-1">Total allocated budget</div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Amount Spent</h3>
                    <div className="text-2xl font-bold text-gray-900">{formatCurrency(project.spent)}</div>
                    <div className="text-sm text-gray-500 mt-1">{(project.spent / project.budget * 100).toFixed(1)}% of budget</div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Tabs */}
            <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('updates')}
                    className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                      activeTab === 'updates'
                        ? 'border-water-blue-500 text-water-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Updates
                  </button>
                  <button
                    onClick={() => setActiveTab('milestones')}
                    className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                      activeTab === 'milestones'
                        ? 'border-water-blue-500 text-water-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Milestones
                  </button>
                  <button
                    onClick={() => setActiveTab('documents')}
                    className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                      activeTab === 'documents'
                        ? 'border-water-blue-500 text-water-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Documents
                  </button>
                </nav>
              </div>
              
              <div className="p-6">
                {activeTab === 'updates' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Project Updates</h3>
                    {project.updates.length > 0 ? (
                      <div className="space-y-6">
                        {project.updates.map((update) => (
                          <div key={update.id} className="border-l-4 border-water-blue-500 pl-4 py-1">
                            <div className="flex justify-between items-start">
                              <h4 className="font-medium text-gray-900">{update.title}</h4>
                              <span className="text-sm text-gray-500">{formatDateTime(update.date)}</span>
                            </div>
                            <p className="mt-1 text-gray-600">{update.description}</p>
                            <div className="mt-1 text-sm text-gray-500">Posted by {update.author}</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No updates available for this project yet.</p>
                    )}
                  </div>
                )}
                
                {activeTab === 'milestones' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Project Milestones</h3>
                    {project.milestones.length > 0 ? (
                      <div className="space-y-4">
                        {project.milestones.map((milestone) => (
                          <div key={milestone.id} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-medium text-gray-900">{milestone.title}</h4>
                                <p className="mt-1 text-sm text-gray-600">{milestone.description}</p>
                              </div>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                milestone.status === 'completed' 
                                  ? 'bg-green-100 text-green-800' 
                                  : milestone.status === 'in_progress'
                                    ? 'bg-blue-100 text-blue-800'
                                    : milestone.status === 'delayed'
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : 'bg-gray-100 text-gray-800'
                              }`}>
                                {milestone.status.replace('_', ' ')}
                              </span>
                            </div>
                            <div className="mt-2 text-sm text-gray-500">
                              Due: {formatDate(milestone.dueDate)}
                              {milestone.completedDate && (
                                <span className="ml-2">• Completed: {formatDate(milestone.completedDate)}</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No milestones defined for this project yet.</p>
                    )}
                  </div>
                )}
                
                {activeTab === 'documents' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Project Documents</h3>
                    {project.documents.length > 0 ? (
                      <div className="space-y-3">
                        {project.documents.map((doc) => (
                          <a
                            key={doc.id}
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex-shrink-0 w-10 h-10 bg-water-blue-50 rounded-lg flex items-center justify-center text-water-blue-600">
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div className="ml-4 flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
                              <p className="text-sm text-gray-500">
                                {doc.type.charAt(0).toUpperCase() + doc.type.slice(1)} • {formatDate(doc.uploadedAt)}
                              </p>
                            </div>
                            <div className="ml-4">
                              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No documents available for this project yet.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Right Column */}
          <div>
            <div className="bg-white rounded-xl shadow-md overflow-hidden mb-6">
              <div className="p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Project Actions</h2>
                <div className="space-y-3">
                  <Button 
                    variant="primary" 
                    className="w-full justify-center"
                    onClick={() => onProvideFeedback(project.id)}
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    Provide Feedback
                  </Button>
                  
                  <Button variant="outline" className="w-full justify-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    Get Updates
                  </Button>
                  
                  <Button variant="outline" className="w-full justify-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Download Report
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-md overflow-hidden">
              <div className="p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Project Team</h2>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-water-blue-100 flex items-center justify-center text-water-blue-800 font-medium">
                      PM
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Project Manager</p>
                      <p className="text-sm text-gray-500">municipality@example.com</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-green-100 flex items-center justify-center text-green-800 font-medium">
                      CE
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Civil Engineer</p>
                      <p className="text-sm text-gray-500">engineer@contractor.com</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-800 font-medium">
                      CO
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Contractor</p>
                      <p className="text-sm text-gray-500">{project.contractor || 'To be assigned'}</p>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Last Updated</h3>
                  <p className="text-sm text-gray-900">{formatDateTime(project.lastUpdated)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Floating Action Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => onProvideFeedback(project.id)}
          className="flex items-center justify-center h-14 w-14 rounded-full bg-water-blue-600 text-white shadow-lg hover:bg-water-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-water-blue-500"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </button>
      </div>
    </div>
  );
};
