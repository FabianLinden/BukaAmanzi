from __future__ import annotations

import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote

from app.db.models import Project
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeocodingService:
    """Service for converting addresses to geographic coordinates"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_expiry = timedelta(days=30)  # Cache geocoding results for 30 days
        self.rate_limit_delay = 1.0  # Seconds between API requests
        self.last_request_time = 0
        
        # Multiple geocoding providers for redundancy
        self.providers = {
            'nominatim': {
                'base_url': 'https://nominatim.openstreetmap.org/search',
                'rate_limit': 1.0,  # 1 request per second
                'enabled': True
            },
            'photon': {
                'base_url': 'https://photon.komoot.io/api/',
                'rate_limit': 0.5,  # 2 requests per second
                'enabled': True
            }
        }
    
    async def geocode_address(self, address: str, municipality: Optional[str] = None) -> Dict[str, Any]:
        """Geocode a single address with fallback providers"""
        
        if not address or address.strip() == '':
            return {
                'success': False,
                'error': 'Empty address provided',
                'coordinates': None,
                'confidence': 'none'
            }
        
        # Clean and normalize address
        normalized_address = self._normalize_address(address, municipality)
        
        # Check cache first
        cache_key = f"{normalized_address}|{municipality or ''}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Using cached geocoding result for: {normalized_address}")
            return cached_result
        
        # Try each provider until successful
        for provider_name, provider_config in self.providers.items():
            if not provider_config['enabled']:
                continue
            
            try:
                logger.info(f"Attempting geocoding with {provider_name} for: {normalized_address}")
                result = await self._geocode_with_provider(provider_name, normalized_address, municipality)
                
                if result['success']:
                    # Cache successful result
                    self._cache_result(cache_key, result)
                    logger.info(f"Successfully geocoded '{normalized_address}' using {provider_name}")
                    return result
                
            except Exception as e:
                logger.warning(f"Geocoding failed with {provider_name}: {str(e)}")
                continue
        
        # All providers failed
        logger.error(f"All geocoding providers failed for address: {normalized_address}")
        return {
            'success': False,
            'error': 'All geocoding providers failed',
            'coordinates': None,
            'confidence': 'none',
            'address': normalized_address
        }
    
    async def _geocode_with_provider(self, provider: str, address: str, municipality: Optional[str] = None) -> Dict[str, Any]:
        """Geocode using a specific provider"""
        
        # Respect rate limiting
        await self._rate_limit_delay(provider)
        
        if provider == 'nominatim':
            return await self._geocode_nominatim(address, municipality)
        elif provider == 'photon':
            return await self._geocode_photon(address, municipality)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _geocode_nominatim(self, address: str, municipality: Optional[str] = None) -> Dict[str, Any]:
        """Geocode using OpenStreetMap Nominatim"""
        
        # Build search query
        query_parts = [address]
        if municipality:
            query_parts.append(municipality)
        query_parts.append("South Africa")
        
        query = ", ".join(query_parts)
        
        params = {
            'q': query,
            'format': 'json',
            'countrycodes': 'za',  # Limit to South Africa
            'limit': 5,
            'addressdetails': 1,
            'extratags': 1,
            'namedetails': 1
        }
        
        url = self.providers['nominatim']['base_url']
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'BukaAmanzi/1.0 (Water Infrastructure Monitoring)'
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                results = await response.json()
                
                if not results:
                    return {
                        'success': False,
                        'error': 'No results found',
                        'coordinates': None,
                        'confidence': 'none'
                    }
                
                # Use the best result
                best_result = results[0]
                lat, lng = float(best_result['lat']), float(best_result['lon'])
                
                # Validate coordinates are within South Africa
                if not self._is_within_south_africa(lat, lng):
                    return {
                        'success': False,
                        'error': 'Coordinates outside South Africa',
                        'coordinates': None,
                        'confidence': 'none'
                    }
                
                # Determine confidence based on result quality
                confidence = self._calculate_confidence_nominatim(best_result, address, municipality)
                
                return {
                    'success': True,
                    'coordinates': {'lat': lat, 'lng': lng},
                    'confidence': confidence,
                    'provider': 'nominatim',
                    'display_name': best_result.get('display_name', ''),
                    'address_components': best_result.get('address', {}),
                    'place_id': best_result.get('place_id'),
                    'osm_type': best_result.get('osm_type'),
                    'importance': best_result.get('importance', 0)
                }
    
    async def _geocode_photon(self, address: str, municipality: Optional[str] = None) -> Dict[str, Any]:
        """Geocode using Photon geocoder"""
        
        query_parts = [address]
        if municipality:
            query_parts.append(municipality)
        query = " ".join(query_parts)
        
        params = {
            'q': query,
            'limit': 5,
            'osm_tag': '!highway',  # Exclude highways
            'bbox': '16.3449768409,34.8191663551,32.830120477,22.0913127581'  # South Africa bounding box
        }
        
        url = self.providers['photon']['base_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
                results = data.get('features', [])
                
                if not results:
                    return {
                        'success': False,
                        'error': 'No results found',
                        'coordinates': None,
                        'confidence': 'none'
                    }
                
                # Use the best result
                best_result = results[0]
                coords = best_result['geometry']['coordinates']
                lng, lat = coords[0], coords[1]  # GeoJSON format: [lng, lat]
                
                # Validate coordinates
                if not self._is_within_south_africa(lat, lng):
                    return {
                        'success': False,
                        'error': 'Coordinates outside South Africa',
                        'coordinates': None,
                        'confidence': 'none'
                    }
                
                # Determine confidence
                confidence = self._calculate_confidence_photon(best_result, address, municipality)
                
                return {
                    'success': True,
                    'coordinates': {'lat': lat, 'lng': lng},
                    'confidence': confidence,
                    'provider': 'photon',
                    'display_name': best_result['properties'].get('name', ''),
                    'address_components': best_result['properties'],
                    'osm_id': best_result['properties'].get('osm_id'),
                    'osm_type': best_result['properties'].get('osm_type')
                }
    
    def _normalize_address(self, address: str, municipality: Optional[str] = None) -> str:
        """Normalize address for consistent geocoding"""
        
        if not address:
            return ""
        
        normalized = address.strip()
        
        # Remove common prefixes that might confuse geocoders
        prefixes_to_remove = [
            r'^project\s+site:?\s*',
            r'^location:?\s*',
            r'^address:?\s*',
            r'^at:?\s*'
        ]
        
        for prefix in prefixes_to_remove:
            normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE).strip()
        
        # Clean up common issues
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single space
        normalized = re.sub(r'[,;]+\s*$', '', normalized)  # Trailing punctuation
        
        return normalized
    
    def _is_within_south_africa(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within South Africa bounds"""
        # South Africa bounding box (approximate)
        return (
            -35.0 <= lat <= -22.0 and
            16.0 <= lng <= 33.0
        )
    
    def _calculate_confidence_nominatim(self, result: Dict[str, Any], original_address: str, municipality: Optional[str]) -> str:
        """Calculate confidence level for Nominatim results"""
        
        importance = result.get('importance', 0)
        osm_type = result.get('osm_type', '')
        place_class = result.get('class', '')
        
        # High confidence indicators
        if importance > 0.5 and osm_type in ['way', 'relation'] and place_class in ['place', 'amenity', 'building']:
            return 'high'
        
        # Medium confidence indicators
        if importance > 0.3 or osm_type in ['node', 'way']:
            return 'medium'
        
        # Default to low confidence
        return 'low'
    
    def _calculate_confidence_photon(self, result: Dict[str, Any], original_address: str, municipality: Optional[str]) -> str:
        """Calculate confidence level for Photon results"""
        
        properties = result.get('properties', {})
        osm_type = properties.get('osm_type', '')
        place_type = properties.get('type', '')
        
        # High confidence indicators
        if osm_type in ['way', 'relation'] and place_type in ['city', 'town', 'village', 'building']:
            return 'high'
        
        # Medium confidence indicators
        if osm_type in ['node', 'way'] or place_type in ['residential', 'commercial', 'industrial']:
            return 'medium'
        
        return 'low'
    
    async def _rate_limit_delay(self, provider: str):
        """Implement rate limiting for geocoding providers"""
        
        current_time = asyncio.get_event_loop().time()
        rate_limit = self.providers[provider]['rate_limit']
        
        if hasattr(self, f'_last_request_{provider}'):
            last_request = getattr(self, f'_last_request_{provider}')
            time_diff = current_time - last_request
            
            if time_diff < rate_limit:
                sleep_time = rate_limit - time_diff
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {provider}")
                await asyncio.sleep(sleep_time)
        
        setattr(self, f'_last_request_{provider}', current_time)
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached geocoding result if not expired"""
        
        if cache_key not in self.cache:
            return None
        
        cached_data = self.cache[cache_key]
        if datetime.utcnow() - cached_data['timestamp'] > self.cache_expiry:
            del self.cache[cache_key]
            return None
        
        result = cached_data['result'].copy()
        result['cached'] = True
        return result
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache geocoding result"""
        
        self.cache[cache_key] = {
            'result': result.copy(),
            'timestamp': datetime.utcnow()
        }
        
        # Clean up old cache entries periodically
        if len(self.cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, data in self.cache.items():
            if current_time - data['timestamp'] > self.cache_expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def geocode_project(self, project: Project) -> Dict[str, Any]:
        """Geocode a project using available address information"""
        
        # Check if project already has coordinates
        if project.location and project.location.startswith('POINT('):
            return {
                'success': True,
                'source': 'existing_coordinates',
                'coordinates': self._parse_point_string(project.location),
                'confidence': 'high',
                'message': 'Project already has precise coordinates'
            }
        
        # Try to geocode using address
        if project.address and project.address.strip():
            municipality_name = None
            if hasattr(project, 'municipality') and project.municipality:
                municipality_name = project.municipality.name if hasattr(project.municipality, 'name') else str(project.municipality)
            
            result = await self.geocode_address(project.address, municipality_name)
            
            if result['success']:
                # Format as POINT string for database storage
                coords = result['coordinates']
                point_string = f"POINT({coords['lng']} {coords['lat']})"
                
                return {
                    'success': True,
                    'source': 'geocoded_address',
                    'coordinates': coords,
                    'point_string': point_string,
                    'confidence': result['confidence'],
                    'provider': result.get('provider'),
                    'display_name': result.get('display_name'),
                    'original_address': project.address
                }
        
        return {
            'success': False,
            'error': 'No geocodable address available',
            'coordinates': None,
            'confidence': 'none'
        }
    
    def _parse_point_string(self, point_string: str) -> Optional[Dict[str, float]]:
        """Parse POINT(lng lat) string to coordinates"""
        
        match = re.match(r'POINT\(([^)]+)\)', point_string)
        if match:
            try:
                coords = match.group(1).split()
                if len(coords) == 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    return {'lat': lat, 'lng': lng}
            except (ValueError, IndexError):
                pass
        
        return None
    
    async def batch_geocode_projects(self, projects: List[Project], max_concurrent: int = 5) -> Dict[str, Any]:
        """Geocode multiple projects concurrently"""
        
        logger.info(f"Starting batch geocoding for {len(projects)} projects")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def geocode_single(project: Project) -> Tuple[str, Dict[str, Any]]:
            async with semaphore:
                result = await self.geocode_project(project)
                return project.id, result
        
        # Process all projects
        tasks = [geocode_single(project) for project in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        geocoded_results = {}
        successful = 0
        failed = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Geocoding task failed: {str(result)}")
                failed += 1
                continue
            
            project_id, geocoding_result = result
            geocoded_results[project_id] = geocoding_result
            
            if geocoding_result['success']:
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Batch geocoding completed: {successful} successful, {failed} failed")
        
        return {
            'total_projects': len(projects),
            'successful': successful,
            'failed': failed,
            'results': geocoded_results,
            'processed_at': datetime.utcnow().isoformat()
        }
