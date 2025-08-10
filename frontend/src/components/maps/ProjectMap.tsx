import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface ProjectLocation {
  id: string;
  name: string;
  lat: number;
  lng: number;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  progress: number;
  municipality: string;
  budget: number;
  description: string;
}

interface ProjectMapProps {
  projects: ProjectLocation[];
  center?: [number, number];
  zoom?: number;
  height?: string;
  onProjectClick?: (project: ProjectLocation) => void;
}

// Custom icons for different project statuses
const createStatusIcon = (status: string, progress: number) => {
  let color = '#3B82F6'; // Default blue
  
  switch (status) {
    case 'completed':
      color = '#10B981'; // Green
      break;
    case 'in_progress':
      color = '#F59E0B'; // Yellow
      break;
    case 'delayed':
      color = '#EF4444'; // Red
      break;
    case 'cancelled':
      color = '#6B7280'; // Gray
      break;
    case 'planned':
      color = '#8B5CF6'; // Purple
      break;
  }

  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        border: 3px solid white;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        position: relative;
      ">
        <div style="
          background-color: white;
          border-radius: 50%;
          width: 12px;
          height: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 8px;
          font-weight: bold;
          color: ${color};
        ">
          ${progress}%
        </div>
      </div>
    `,
    className: 'custom-div-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

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

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'text-green-600 bg-green-100';
    case 'in_progress': return 'text-yellow-600 bg-yellow-100';
    case 'delayed': return 'text-red-600 bg-red-100';
    case 'cancelled': return 'text-gray-600 bg-gray-100';
    case 'planned': return 'text-purple-600 bg-purple-100';
    default: return 'text-blue-600 bg-blue-100';
  }
};

const FitBounds: React.FC<{ projects: ProjectLocation[] }> = ({ projects }) => {
  const map = useMap();
  
  useEffect(() => {
    if (projects.length > 0) {
      const bounds = L.latLngBounds(projects.map(p => [p.lat, p.lng]));
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [map, projects]);
  
  return null;
};

export const ProjectMap: React.FC<ProjectMapProps> = ({
  projects,
  center = [-29.0, 24.0], // Center of South Africa
  zoom = 6,
  height = '400px',
  onProjectClick
}) => {
  return (
    <div className="w-full border border-gray-300 rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height, width: '100%' }}
        className="z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {projects.length > 0 && <FitBounds projects={projects} />}
        
        {projects.map((project) => (
          <Marker
            key={project.id}
            position={[project.lat, project.lng]}
            icon={createStatusIcon(project.status, project.progress)}
            eventHandlers={{
              click: () => {
                if (onProjectClick) {
                  onProjectClick(project);
                }
              }
            }}
          >
            <Popup className="project-popup" maxWidth={300}>
              <div className="p-2">
                <h3 className="font-bold text-lg text-gray-900 mb-2 leading-tight">
                  {project.name}
                </h3>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {project.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Progress:</span>
                    <span className="text-sm font-medium text-blue-600">{project.progress}%</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Budget:</span>
                    <span className="text-sm font-medium text-green-600">{formatCurrency(project.budget)}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Municipality:</span>
                    <span className="text-sm text-gray-800 truncate max-w-32" title={project.municipality}>
                      {project.municipality}
                    </span>
                  </div>
                </div>
                
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {project.description.length > 100 
                      ? `${project.description.substring(0, 100)}...` 
                      : project.description
                    }
                  </p>
                </div>
                
                {onProjectClick && (
                  <button
                    onClick={() => onProjectClick(project)}
                    className="mt-3 w-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded transition-colors"
                  >
                    View Details
                  </button>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {/* Legend */}
      <div className="bg-white px-4 py-3 border-t border-gray-200">
        <div className="flex flex-wrap items-center justify-between text-xs">
          <div className="font-medium text-gray-700 mb-2 w-full sm:w-auto sm:mb-0">Project Status:</div>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-purple-500 rounded-full mr-1"></div>
              <span className="text-gray-600">Planned</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-1"></div>
              <span className="text-gray-600">In Progress</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
              <span className="text-gray-600">Completed</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-1"></div>
              <span className="text-gray-600">Delayed</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-500 rounded-full mr-1"></div>
              <span className="text-gray-600">Cancelled</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
