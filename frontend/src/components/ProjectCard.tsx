import { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardFooter } from './ui/Card';
import { ProgressBar } from './ui/ProgressBar';
import { Button } from './ui/Button';
import { WaterWave } from './WaterWave';
import { WaterDroplet } from './WaterDroplet';
import { WaterBubbles } from './WaterBubbles';

interface ProjectCardProps {
  id: string;
  title: string;
  location: string;
  description: string;
  progress: number;
  budget: number;
  spent: number;
  startDate: string;
  endDate: string;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  onViewDetails: (id: string) => void;
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

export const ProjectCard = ({
  id,
  title,
  location,
  description,
  progress,
  budget,
  spent,
  startDate,
  endDate,
  status,
  onViewDetails,
}: ProjectCardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const [waveOpacity, setWaveOpacity] = useState(0);
  
  useEffect(() => {
    if (isHovered) {
      setWaveOpacity(0.3);
    } else {
      setWaveOpacity(0.1);
    }
  }, [isHovered]);
  
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
      month: 'short',
      day: 'numeric',
    });
  };

  // Enhanced project title parsing and display
  const parseProjectInfo = (title: string) => {
    // Extract project phase/number from titles like "Water Infrastructure Project 1 - Municipality"
    const phaseMatch = title.match(/Project\s+(\d+|[IVX]+)\s*-\s*(.+)$/);
    if (phaseMatch) {
      const phase = phaseMatch[1];
      const municipality = phaseMatch[2];
      return {
        displayTitle: `${municipality} - Phase ${phase}`,
        subtitle: 'Water Infrastructure Development',
        phase: phase,
        municipality: municipality
      };
    }
    
    // Handle other title patterns
    const municipalityMatch = title.match(/(.+)\s+-\s+(.+)$/);
    if (municipalityMatch) {
      return {
        displayTitle: title,
        subtitle: '',
        phase: null,
        municipality: municipalityMatch[2]
      };
    }
    
    return {
      displayTitle: title,
      subtitle: '',
      phase: null,
      municipality: location
    };
  };

  const projectInfo = parseProjectInfo(title);

  // Generate a unique color based on project ID for visual distinction
  const getProjectAccentColor = (id: string) => {
    const colors = [
      'border-blue-300 bg-blue-50',
      'border-green-300 bg-green-50', 
      'border-purple-300 bg-purple-50',
      'border-orange-300 bg-orange-50',
      'border-teal-300 bg-teal-50',
      'border-pink-300 bg-pink-50',
      'border-indigo-300 bg-indigo-50',
      'border-cyan-300 bg-cyan-50'
    ];
    const index = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
  };

  const accentColor = getProjectAccentColor(id);

  return (
    <div 
      className={`relative overflow-hidden rounded-xl bg-gradient-to-br from-white to-water-blue-50/20 
        shadow-lg transition-all duration-500 hover:shadow-xl group
        ${isHovered ? 'animate-card-float' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Water Droplets - Top Corner Decorations */}
      <div className="absolute top-4 right-4 flex space-x-1 opacity-60">
        <WaterDroplet size="sm" delay={0} />
        <WaterDroplet size="sm" delay={200} />
      </div>
      
      {/* Progress-based Water Level Indicator */}
      <div 
        className="absolute left-0 top-0 w-1 bg-gradient-to-b from-water-blue-400 to-water-blue-600 transition-all duration-1000"
        style={{ height: `${progress}%` }}
      />
      
      <div className="relative z-10 p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            {/* Enhanced title with phase information */}
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-xl font-bold text-gray-900 group-hover:text-water-blue-800 transition-colors">
                {projectInfo.displayTitle}
              </h3>
              {projectInfo.phase && (
                <span className={`px-2 py-1 rounded-lg text-xs font-semibold border-2 ${accentColor}`}>
                  Phase {projectInfo.phase}
                </span>
              )}
            </div>
            
            {/* Subtitle for project type */}
            {projectInfo.subtitle && (
              <div className="text-sm font-medium text-gray-600 mb-1">
                {projectInfo.subtitle}
              </div>
            )}
            
            {/* Location information */}
            <div className="flex items-center text-sm text-gray-500 mb-2">
              <svg 
                className="w-4 h-4 mr-1 text-water-blue-500" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" 
                />
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" 
                />
              </svg>
              {location || 'Location not specified'}
            </div>
          </div>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium 
            backdrop-blur-sm border border-white/20 ${
            statusColors[status] || 'bg-gray-100 text-gray-800'
          }`}>
            {statusLabels[status] || status}
          </span>
        </div>
        
        <p className="text-gray-600 mb-4 line-clamp-2">{description}</p>
        
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="font-medium text-gray-700">Progress</span>
            <span className="font-medium text-water-blue-700">{Math.round(progress)}%</span>
          </div>
          <ProgressBar value={progress} className="h-2.5" />
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">Budget</div>
            <div className="font-medium">{formatCurrency(budget)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500 mb-1">Spent</div>
            <div className="font-medium">{formatCurrency(spent)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500 mb-1">Start Date</div>
            <div className="font-medium">{formatDate(startDate)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500 mb-1">End Date</div>
            <div className="font-medium">{formatDate(endDate)}</div>
          </div>
        </div>
        
        <Button 
          variant="outline" 
          className="w-full mt-2"
          onClick={() => onViewDetails(id)}
        >
          View Project Details
        </Button>
      </div>
      
      <div 
        className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-water-blue-50 to-transparent"
        style={{ opacity: waveOpacity, transition: 'opacity 0.3s ease' }}
      >
        <WaterWave className="w-full h-full" opacity={0.3} speed="slow" />
      </div>
      
      {isHovered && (
        <div className="absolute inset-0 bg-gradient-to-br from-water-blue-50/30 to-transparent pointer-events-none" />
      )}
    </div>
  );
};