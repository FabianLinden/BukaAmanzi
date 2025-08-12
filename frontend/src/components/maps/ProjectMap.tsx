import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';
import { calculateDataQualityScore, getQualityTier, getQualityColor } from '../../utils/projectDataUtils';

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
  
  // Enhanced location metadata
  locationSource?: string;
  locationConfidence?: string;
  hasCoordinates?: boolean;
  isMunicipalityCenter?: boolean;
  municipalityName?: string;
  isFallback?: boolean;
  
  // Styling information
  markerType?: string;
  opacity?: number;
  markerSize?: string;
  isComplete?: boolean;
  
  // Additional project info
  originalProject?: any;
}

interface ProjectMapProps {
  projects: ProjectLocation[];
  center?: [number, number];
  zoom?: number;
  height?: string;
  onProjectClick?: (project: ProjectLocation) => void;
}

// Enhanced icons for different project statuses and data quality
const createStatusIcon = (project: ProjectLocation) => {
  const { status, progress, isComplete = true, locationConfidence = 'high', isMunicipalityCenter = false, hasCoordinates = true } = project;
  let color = '#3B82F6'; // Default blue
  let size = 24;
  let opacity = 1.0;
  let borderStyle = '3px solid white';
  
  // Determine base color from status
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
  
  // Adjust styling based on data quality and location confidence
  if (!isComplete) {
    opacity = 0.7;
    borderStyle = '2px dashed white';
  }
  
  if (isMunicipalityCenter) {
    color = '#F97316'; // Orange for municipality centers
    borderStyle = '2px dotted white';
    opacity = 0.8;
  }
  
  if (locationConfidence === 'low') {
    opacity *= 0.8;
    size = 20;
  } else if (locationConfidence === 'medium') {
    opacity *= 0.9;
    size = 22;
  }
  
  // Create location confidence indicator
  let confidenceIndicator = '';
  if (!hasCoordinates || locationConfidence !== 'high') {
    const indicatorColor = hasCoordinates ? '#F97316' : '#EF4444';
    confidenceIndicator = `
      <div style="
        position: absolute;
        top: -2px;
        right: -2px;
        width: 8px;
        height: 8px;
        background-color: ${indicatorColor};
        border: 1px solid white;
        border-radius: 50%;
        z-index: 1000;
      "></div>
    `;
  }

  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        border: ${borderStyle};
        border-radius: 50%;
        width: ${size}px;
        height: ${size}px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        position: relative;
        opacity: ${opacity};
      ">
        <div style="
          background-color: white;
          border-radius: 50%;
          width: ${size - 12}px;
          height: ${size - 12}px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: ${size > 22 ? 8 : 7}px;
          font-weight: bold;
          color: ${color};
        ">
          ${progress}%
        </div>
        ${confidenceIndicator}
      </div>
    `,
    className: 'custom-div-icon',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
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

// Custom clustering component
const ClusteredMarkers: React.FC<{ projects: ProjectLocation[], onProjectClick?: (project: ProjectLocation) => void }> = ({ projects, onProjectClick }) => {
  const map = useMap();

  useEffect(() => {
    // Create marker cluster group
    const markerClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 60,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        let size = 'small';
        let className = 'marker-cluster-small';

        if (count >= 100) {
          size = 'large';
          className = 'marker-cluster-large';
        } else if (count >= 10) {
          size = 'medium';
          className = 'marker-cluster-medium';
        }

        return L.divIcon({
          html: `<div><span>${count}</span></div>`,
          className: className,
          iconSize: L.point(40, 40)
        });
      }
    });

    // Add markers to cluster group
    projects.forEach(project => {
      const marker = L.marker([project.lat, project.lng], {
        icon: createStatusIcon(project)
      });

      // Add popup to marker
      const popupContent = `
        <div class="p-2">
          <h3 class="font-bold text-lg text-gray-900 mb-2 leading-tight">
            ${project.name}
          </h3>
          
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Status:</span>
              <span class="px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}">
                ${project.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Progress:</span>
              <span class="text-sm font-medium text-blue-600">${project.progress}%</span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Budget:</span>
              <span class="text-sm font-medium text-green-600">${formatCurrency(project.budget)}</span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Municipality:</span>
              <span class="text-sm text-gray-800 truncate max-w-32" title="${project.municipality}">
                ${project.municipality}
              </span>
            </div>
            
            ${project.locationConfidence ? `
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Location:</span>
                <span class="text-xs px-2 py-1 rounded-full ${
                  project.hasCoordinates && project.locationConfidence === 'high' ? 'bg-green-100 text-green-700' :
                  project.isMunicipalityCenter ? 'bg-orange-100 text-orange-700' :
                  'bg-yellow-100 text-yellow-700'
                }">
                  ${project.hasCoordinates && project.locationConfidence === 'high' ? 'Exact' :
                   project.isMunicipalityCenter ? 'Municipality Center' :
                   'Approximate'}
                </span>
              </div>
            ` : ''}
            
            ${project.isComplete !== undefined ? `
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Data Quality:</span>
                <span class="text-xs px-2 py-1 rounded-full ${
                  project.isComplete ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }">
                  ${project.isComplete ? 'Complete' : 'Incomplete'}
                </span>
              </div>
            ` : ''}
          </div>
          
          <div class="mt-3 pt-2 border-t border-gray-200">
            <p class="text-sm text-gray-600 leading-relaxed">
              ${project.description.length > 100 
                ? project.description.substring(0, 100) + '...' 
                : project.description
              }
            </p>
          </div>
          
          ${onProjectClick ? `
            <button
              onclick="window.handleProjectClick('${project.id}')"
              class="mt-3 w-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded transition-colors"
            >
              View Details
            </button>
          ` : ''}
        </div>
      `;

      marker.bindPopup(popupContent, { maxWidth: 300, className: 'project-popup' });
      markerClusterGroup.addLayer(marker);
    });

    // Add cluster group to map
    map.addLayer(markerClusterGroup);

    // Setup global click handler for project details
    if (onProjectClick) {
      (window as any).handleProjectClick = (projectId: string) => {
        const project = projects.find(p => p.id === projectId);
        if (project) {
          onProjectClick(project);
        }
      };
    }

    // Cleanup on unmount
    return () => {
      map.removeLayer(markerClusterGroup);
      if ((window as any).handleProjectClick) {
        delete (window as any).handleProjectClick;
      }
    };
  }, [map, projects, onProjectClick]);

  return null;
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
        
        <ClusteredMarkers projects={projects} onProjectClick={onProjectClick} />
      </MapContainer>
      
      {/* Enhanced Legend */}
      <div className="bg-white px-4 py-3 border-t border-gray-200">
        <div className="space-y-3 text-xs">
          {/* Status Legend */}
          <div className="flex flex-wrap items-center justify-between">
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
          
          {/* Location Confidence Legend */}
          <div className="flex flex-wrap items-center justify-between border-t pt-3">
            <div className="font-medium text-gray-700 mb-2 w-full sm:w-auto sm:mb-0">Location Confidence:</div>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-1 border-2 border-white"></div>
                <span className="text-gray-600">Exact Coordinates</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-orange-500 rounded-full mr-1 border border-white border-dotted"></div>
                <span className="text-gray-600">Municipality Center</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-1 border border-white border-dashed opacity-70"></div>
                <span className="text-gray-600">Incomplete Data</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
