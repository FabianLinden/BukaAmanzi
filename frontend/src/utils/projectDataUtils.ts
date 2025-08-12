// Utility functions for handling project data quality and filtering

export interface ProjectValidationResult {
  isComplete: boolean;
  completeness: number;
  missingFields: string[];
  dataQuality: 'high' | 'medium' | 'low';
}

export const validateProjectData = (project: any): ProjectValidationResult => {
  const requiredFields = [
    { field: 'name', weight: 1 },
    { field: 'description', weight: 0.8 },
    { field: 'start_date', weight: 1 },
    { field: 'end_date', weight: 1 },
    { field: 'address', weight: 0.9 },
    { field: 'location', weight: 0.9 },
    { field: 'budget_allocated', weight: 0.7 },
    { field: 'municipality_name', weight: 1 }
  ];

  const missingFields: string[] = [];
  let totalWeight = 0;
  let presentWeight = 0;

  requiredFields.forEach(({ field, weight }) => {
    totalWeight += weight;
    const value = project[field];
    
    if (isValidField(value)) {
      presentWeight += weight;
    } else {
      missingFields.push(field);
    }
  });

  const completeness = (presentWeight / totalWeight) * 100;
  const isComplete = completeness >= 80; // 80% threshold for complete projects

  let dataQuality: 'high' | 'medium' | 'low';
  if (completeness >= 90) {
    dataQuality = 'high';
  } else if (completeness >= 70) {
    dataQuality = 'medium';
  } else {
    dataQuality = 'low';
  }

  return {
    isComplete,
    completeness,
    missingFields,
    dataQuality
  };
};

const isValidField = (value: any): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string' && (value.trim() === '' || value.trim() === 'null' || value.trim() === 'undefined')) return false;
  if (typeof value === 'number' && (isNaN(value) || value === 0)) return false;
  return true;
};

export const filterCompleteProjects = (projects: any[]): any[] => {
  return projects.filter(project => {
    const validation = validateProjectData(project);
    return validation.isComplete;
  });
};

export const filterIncompleteProjects = (projects: any[]): any[] => {
  return projects.filter(project => {
    const validation = validateProjectData(project);
    return !validation.isComplete;
  });
};

export const categorizeProjects = (projects: any[]) => {
  const complete: any[] = [];
  const incomplete: any[] = [];
  const validationResults: Map<string, ProjectValidationResult> = new Map();

  projects.forEach(project => {
    const validation = validateProjectData(project);
    validationResults.set(project.id, validation);
    
    if (validation.isComplete) {
      complete.push(project);
    } else {
      incomplete.push(project);
    }
  });

  return {
    complete,
    incomplete,
    validationResults,
    statistics: {
      total: projects.length,
      completeCount: complete.length,
      incompleteCount: incomplete.length,
      completePercentage: projects.length > 0 ? (complete.length / projects.length) * 100 : 0
    }
  };
};

export const getProjectQualityStats = (projects: any[]) => {
  const stats = {
    high: 0,
    medium: 0,
    low: 0,
    total: projects.length
  };

  projects.forEach(project => {
    const validation = validateProjectData(project);
    stats[validation.dataQuality]++;
  });

  return stats;
};

export const hasValidLocation = (project: any): boolean => {
  // Check for POINT format coordinates
  if (project.location && typeof project.location === 'string' && project.location.startsWith('POINT(')) {
    return true;
  }
  
  // Check for valid address
  if (project.address && typeof project.address === 'string' && project.address.trim() !== '') {
    return true;
  }
  
  return false;
};

export const parseLocationFromProject = (project: any) => {
  // Try to extract coordinates from POINT format
  if (project.location && project.location.startsWith('POINT(')) {
    const coords = project.location.match(/POINT\(([^)]+)\)/);
    if (coords && coords[1]) {
      const [lng, lat] = coords[1].split(' ').map(parseFloat);
      if (!isNaN(lat) && !isNaN(lng)) {
        return { 
          lat, 
          lng, 
          coordinates: `${lat}, ${lng}`,
          source: 'coordinates',
          confidence: 'high'
        };
      }
    }
  }
  
  // Fallback to address if available
  if (project.address && project.address.trim() !== '') {
    return {
      address: project.address,
      source: 'address',
      confidence: 'medium'
    };
  }
  
  return null;
};

// Enhanced municipality-based location mapping
const municipalityLocationMap: { [key: string]: { lat: number; lng: number; zoom?: number } } = {
  // Major municipalities with precise coordinates
  'City of Cape Town': { lat: -33.9249, lng: 18.4241, zoom: 10 },
  'City of Johannesburg': { lat: -26.2041, lng: 28.0473, zoom: 10 },
  'eThekwini Municipality': { lat: -29.8587, lng: 31.0218, zoom: 10 },
  'City of Tshwane': { lat: -25.7479, lng: 28.2293, zoom: 10 },
  'Nelson Mandela Bay Municipality': { lat: -33.9608, lng: 25.6022, zoom: 10 },
  'Buffalo City Municipality': { lat: -32.9783, lng: 27.8546, zoom: 11 },
  'Mangaung Metropolitan Municipality': { lat: -29.1217, lng: 26.2041, zoom: 11 },
  'Ekurhuleni Metropolitan Municipality': { lat: -26.1367, lng: 28.2400, zoom: 10 },
  
  // Western Cape municipalities
  'Drakenstein Municipality': { lat: -33.8067, lng: 19.0116, zoom: 12 },
  'Stellenbosch Municipality': { lat: -33.9321, lng: 18.8602, zoom: 12 },
  'Swartland Municipality': { lat: -33.3019, lng: 18.8607, zoom: 12 },
  'Witzenberg Municipality': { lat: -33.2167, lng: 19.1333, zoom: 12 },
  'Breede Valley Municipality': { lat: -33.6394, lng: 19.4484, zoom: 12 },
  'Langeberg Municipality': { lat: -33.8833, lng: 20.4500, zoom: 12 },
  'Overberg District Municipality': { lat: -34.4208, lng: 19.2375, zoom: 11 },
  'West Coast District Municipality': { lat: -32.2968, lng: 18.4900, zoom: 11 },
  
  // Eastern Cape municipalities  
  'Kouga Municipality': { lat: -33.7808, lng: 24.9122, zoom: 12 },
  'Ndlambe Municipality': { lat: -33.6081, lng: 26.8909, zoom: 12 },
  'Sundays River Valley Municipality': { lat: -33.4500, lng: 25.5833, zoom: 12 },
  'Blue Crane Route Municipality': { lat: -32.8208, lng: 26.0447, zoom: 12 },
  'Dr Beyers Naude Municipality': { lat: -33.2167, lng: 23.6167, zone: 12 },
  
  // KwaZulu-Natal municipalities
  'uMhlathuze Municipality': { lat: -28.7856, lng: 32.0467, zoom: 12 },
  'Newcastle Municipality': { lat: -27.7574, lng: 29.9319, zoom: 12 },
  'Msunduzi Municipality': { lat: -29.6000, lng: 30.3783, zoom: 12 },
  'Ray Nkonyeni Municipality': { lat: -30.7394, lng: 30.1986, zoom: 12 },
  'Umgeni Municipality': { lat: -29.5167, lng: 30.2667, zoom: 12 },
  
  // Gauteng municipalities
  'Mogale City': { lat: -26.0167, lng: 27.7833, zoom: 12 },
  'Rand West City Municipality': { lat: -26.1833, lng: 27.7667, zoom: 12 },
  'Merafong City Municipality': { lat: -26.3667, lng: 27.4667, zoom: 12 },
  'Midvaal Municipality': { lat: -26.5667, lng: 28.1167, zoom: 12 },
  'Emfuleni Municipality': { lat: -26.5333, lng: 27.8667, zoom: 12 },
  'Lesedi Municipality': { lat: -26.4167, lng: 28.3500, zoom: 12 },
  
  // Mpumalanga municipalities
  'City of Mbombela': { lat: -25.4753, lng: 31.0059, zoom: 11 },
  'Emalahleni Municipality': { lat: -25.8647, lng: 29.2364, zoom: 12 },
  'Steve Tshwete Municipality': { lat: -25.3833, lng: 29.8167, zoom: 12 },
  'Govan Mbeki Municipality': { lat: -26.2167, lng: 29.1833, zoom: 12 },
  
  // Limpopo municipalities
  'Polokwane Municipality': { lat: -23.9045, lng: 29.4689, zoom: 11 },
  'Greater Giyani Municipality': { lat: -23.3026, lng: 30.7188, zoom: 12 },
  'Greater Tzaneen Municipality': { lat: -23.8333, lng: 30.1667, zoom: 12 },
  'Makhado Municipality': { lat: -23.0667, lng: 29.9000, zoom: 12 },
  
  // North West municipalities
  'Madibeng Municipality': { lat: -25.3304, lng: 27.2499, zoom: 12 },
  'Rustenburg Municipality': { lat: -25.6672, lng: 27.2424, zoom: 12 },
  'Moretele Municipality': { lat: -25.4333, lng: 28.0333, zoom: 12 },
  'Moses Kotane Municipality': { lat: -25.6000, lng: 26.9833, zoom: 12 },
  
  // Northern Cape municipalities
  'Sol Plaatje Municipality': { lat: -28.7282, lng: 24.7499, zoom: 12 },
  'Dikgatlong Municipality': { lat: -28.0833, lng: 24.8167, zoom: 12 },
  'Phokwane Municipality': { lat: -27.9167, lng: 25.5833, zoom: 12 },
  
  // Free State municipalities
  'Mangaung Municipality': { lat: -29.1217, lng: 26.2041, zoom: 11 },
  'Matjhabeng Municipality': { lat: -27.4833, lng: 26.7333, zoom: 12 },
  'Fezile Dabi District Municipality': { lat: -27.8500, lng: 26.8833, zoom: 11 },
  'Lejweleputswa District Municipality': { lat: -28.7500, lng: 26.0000, zoom: 11 },
  
  // Generic fallbacks
  'Unknown Municipality': { lat: -29.0, lng: 24.0, zoom: 6 },
  'Not specified': { lat: -29.0, lng: 24.0, zoom: 6 },
};

export const getMunicipalityLocation = (municipalityName: string) => {
  if (!municipalityName) return null;
  
  // Direct match
  if (municipalityLocationMap[municipalityName]) {
    return { 
      ...municipalityLocationMap[municipalityName], 
      source: 'municipality_mapping',
      confidence: 'medium'
    };
  }
  
  // Fuzzy match - look for partial matches
  const normalized = municipalityName.toLowerCase().trim();
  for (const [key, value] of Object.entries(municipalityLocationMap)) {
    if (key.toLowerCase().includes(normalized) || normalized.includes(key.toLowerCase())) {
      return { 
        ...value, 
        source: 'municipality_fuzzy',
        confidence: 'low'
      };
    }
  }
  
  return null;
};

export const getProjectLocation = (project: any) => {
  // Try precise coordinates first
  const locationData = parseLocationFromProject(project);
  if (locationData && locationData.lat && locationData.lng) {
    return {
      lat: locationData.lat,
      lng: locationData.lng,
      source: locationData.source,
      confidence: locationData.confidence,
      hasCoordinates: true
    };
  }
  
  // Try municipality-based location
  const municipalityName = project.municipality_name || project.municipality;
  if (municipalityName) {
    const municipalityLocation = getMunicipalityLocation(municipalityName);
    if (municipalityLocation) {
      return {
        lat: municipalityLocation.lat,
        lng: municipalityLocation.lng,
        source: municipalityLocation.source,
        confidence: municipalityLocation.confidence,
        hasCoordinates: false,
        isMunicipalityCenter: true,
        municipalityName: municipalityName
      };
    }
  }
  
  // Final fallback - center of South Africa
  return {
    lat: -29.0,
    lng: 24.0,
    source: 'fallback',
    confidence: 'none',
    hasCoordinates: false,
    isFallback: true
  };
};

export const isGenericProjectName = (name: string): boolean => {
  if (!name || typeof name !== 'string') return true;
  
  const genericPatterns = [
    /^District\s+Municipaly?Project$/i,
    /^Project\s*\d*$/i,
    /^Test\s+Project/i,
    /^Sample\s+Project/i,
    /^Placeholder/i,
    /^Default\s+Project/i,
    /^Unnamed\s+Project/i,
    /^\s*$/ // Empty or whitespace only
  ];
  
  return genericPatterns.some(pattern => pattern.test(name.trim()));
};

export const enhanceProjectData = (project: any) => {
  const validation = validateProjectData(project);
  const locationData = parseLocationFromProject(project);
  const hasGenericName = isGenericProjectName(project.name);
  
  return {
    ...project,
    _validation: validation,
    _locationData: locationData,
    _hasGenericName: hasGenericName,
    _hasValidLocation: hasValidLocation(project)
  };
};

// API integration functions
export const fetchDataQualityReport = async () => {
  try {
    const response = await fetch('/api/v1/data-quality/assessment');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching data quality report:', error);
    throw error;
  }
};

export const fetchFilteredProjects = async (filters = {}) => {
  const {
    minQualityScore = 60,
    excludeTemplate = true,
    qualityTiers = null,
    includeAssessment = false
  } = filters;
  
  const params = new URLSearchParams({
    min_quality_score: minQualityScore.toString(),
    exclude_template: excludeTemplate.toString(),
    include_assessment: includeAssessment.toString()
  });
  
  if (qualityTiers && qualityTiers.length > 0) {
    params.append('quality_tiers', qualityTiers.join(','));
  }
  
  try {
    const response = await fetch(`/api/v1/data-quality/filtered-projects?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching filtered projects:', error);
    throw error;
  }
};

export const geocodeAddress = async (address, municipality = null) => {
  try {
    const response = await fetch('/api/v1/data-quality/geocode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        address,
        municipality
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error geocoding address:', error);
    throw error;
  }
};

export const improveProjectData = async (projectId, options = {}) => {
  const { geocodeAddress = true } = options;
  
  try {
    const response = await fetch(`/api/v1/data-quality/improve-project/${projectId}?geocode_address=${geocodeAddress}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error improving project data:', error);
    throw error;
  }
};

// Data quality assessment functions
export const calculateDataQualityScore = (project: any): number => {
  const validation = validateProjectData(project);
  const locationData = parseLocationFromProject(project);
  const hasGenericName = isGenericProjectName(project.name);
  
  let score = 0;
  const maxScore = 100;
  
  // Name quality (20 points)
  if (!hasGenericName && project.name && project.name.trim().length > 10) {
    score += 20;
  } else if (!hasGenericName && project.name) {
    score += 10;
  }
  
  // Location quality (25 points)
  if (locationData && locationData.lat && locationData.lng) {
    score += 25;
  } else if (project.address && project.address.trim()) {
    score += 10;
  }
  
  // Financial data (20 points)
  if (project.budget_allocated && project.budget_allocated > 0) {
    score += 12;
    if (project.budget_spent !== undefined && project.budget_spent >= 0) {
      score += 8;
    }
  }
  
  // Temporal data (15 points)
  if (project.start_date && project.end_date) {
    score += 15;
  } else if (project.start_date || project.end_date) {
    score += 8;
  }
  
  // Descriptive data (10 points)
  if (project.description && project.description.trim() && project.description.length > 20) {
    score += 6;
  }
  if (project.contractor && project.contractor.trim()) {
    score += 4;
  }
  
  // Status consistency (10 points)
  if (project.status && ['planned', 'in_progress', 'completed', 'delayed', 'cancelled'].includes(project.status)) {
    score += 10;
  }
  
  return Math.min(score, maxScore);
};

export const getQualityTier = (score: number): string => {
  if (score >= 90) return 'excellent';
  if (score >= 80) return 'good';
  if (score >= 60) return 'fair';
  if (score >= 40) return 'poor';
  return 'very_poor';
};

export const getQualityColor = (tier: string): string => {
  switch (tier) {
    case 'excellent': return 'text-green-700 bg-green-100';
    case 'good': return 'text-blue-700 bg-blue-100';
    case 'fair': return 'text-yellow-700 bg-yellow-100';
    case 'poor': return 'text-orange-700 bg-orange-100';
    case 'very_poor': return 'text-red-700 bg-red-100';
    default: return 'text-gray-700 bg-gray-100';
  }
};
