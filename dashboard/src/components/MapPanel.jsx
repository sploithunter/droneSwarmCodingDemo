import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useSwarmState } from '../context/WebSocketContext';
import { CALLSIGNS, BASE_STATION } from '../utils/constants';

const MODE_COLOR_MAP = {
  0: '#808080', 1: '#2196F3', 2: '#2196F3', 3: '#00BCD4',
  4: '#FF9800', 5: '#FF9800', 6: '#808080', 7: '#F44336',
};

export default function MapPanel() {
  const { state, dispatch } = useSwarmState();
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});
  const trailsRef = useRef({});
  const waypointLayersRef = useRef({});
  const geofenceRef = useRef(null);

  // Initialize map
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapRef.current).setView([BASE_STATION.lat, BASE_STATION.lon], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    // Base station marker
    L.marker([BASE_STATION.lat, BASE_STATION.lon], {
      icon: L.divIcon({
        className: 'base-station-marker',
        html: '<div style="background:#FFD700;width:16px;height:16px;border-radius:50%;border:3px solid #333;"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(map).bindPopup('Base Station');

    // Geofence boundary (2km x 2km)
    const halfLatDeg = 1000 / 111320;
    const halfLonDeg = 1000 / (111320 * Math.cos(BASE_STATION.lat * Math.PI / 180));
    const bounds = [
      [BASE_STATION.lat - halfLatDeg, BASE_STATION.lon - halfLonDeg],
      [BASE_STATION.lat - halfLatDeg, BASE_STATION.lon + halfLonDeg],
      [BASE_STATION.lat + halfLatDeg, BASE_STATION.lon + halfLonDeg],
      [BASE_STATION.lat + halfLatDeg, BASE_STATION.lon - halfLonDeg],
    ];
    geofenceRef.current = L.polygon(bounds, {
      color: '#F44336', weight: 2, dashArray: '10,10', fill: false,
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update drone markers
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    for (let id = 0; id < 8; id++) {
      const droneState = state.droneStates[id];
      if (!droneState || !droneState.position) continue;

      const { latitude, longitude } = droneState.position;
      const heading = droneState.heading_deg || 0;
      const mode = droneState.mode || 0;
      const color = MODE_COLOR_MAP[mode] || '#808080';
      const callsign = CALLSIGNS[id];
      const isSelected = state.selectedDroneId === id;

      const iconHtml = `<div style="
        width:24px;height:24px;
        transform:rotate(${heading}deg);
        border:2px solid ${color};
        background:${color}33;
        border-radius:50% 50% 50% 0;
        ${isSelected ? 'box-shadow:0 0 8px ' + color + ';' : ''}
        ${mode === 7 ? 'animation:pulse 1s infinite;' : ''}
      "><span style="font-size:8px;color:${color};position:absolute;top:-12px;left:0;white-space:nowrap;">${callsign}</span></div>`;

      if (markersRef.current[id]) {
        markersRef.current[id].setLatLng([latitude, longitude]);
        markersRef.current[id].setIcon(L.divIcon({
          className: 'drone-marker',
          html: iconHtml,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        }));
      } else {
        markersRef.current[id] = L.marker([latitude, longitude], {
          icon: L.divIcon({
            className: 'drone-marker',
            html: iconHtml,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
          }),
        }).addTo(map).on('click', () => {
          dispatch({ type: 'SELECT_DRONE', payload: id });
        });
      }

      // Update trails
      if (state.showTrails && state.droneTrails[id]) {
        const trailPoints = state.droneTrails[id].map(p => [p.lat, p.lon]);
        if (trailsRef.current[id]) {
          trailsRef.current[id].setLatLngs(trailPoints);
        } else {
          trailsRef.current[id] = L.polyline(trailPoints, {
            color: color, weight: 2, opacity: 0.5,
          }).addTo(map);
        }
      } else if (trailsRef.current[id]) {
        map.removeLayer(trailsRef.current[id]);
        delete trailsRef.current[id];
      }

      // Update waypoint paths
      const mission = state.missions[id];
      if (state.showWaypoints && mission && mission.waypoints) {
        const wpPoints = mission.waypoints.map(wp => [wp.latitude, wp.longitude]);
        if (waypointLayersRef.current[id]) {
          waypointLayersRef.current[id].setLatLngs(wpPoints);
        } else {
          waypointLayersRef.current[id] = L.polyline(wpPoints, {
            color: color, weight: 1, dashArray: '5,5', opacity: 0.7,
          }).addTo(map);
        }
      } else if (waypointLayersRef.current[id]) {
        map.removeLayer(waypointLayersRef.current[id]);
        delete waypointLayersRef.current[id];
      }
    }
  }, [state.droneStates, state.selectedDroneId, state.showTrails, state.showWaypoints, state.droneTrails, state.missions]);

  return (
    <div className="map-panel" data-testid="map-panel">
      <div ref={mapRef} className="map-container" style={{ height: '100%', minHeight: '400px' }} />
      <div className="map-controls" data-testid="map-controls">
        <button
          data-testid="toggle-trails"
          onClick={() => dispatch({ type: 'TOGGLE_TRAILS' })}
          className={state.showTrails ? 'active' : ''}
        >
          Trails
        </button>
        <button
          data-testid="toggle-waypoints"
          onClick={() => dispatch({ type: 'TOGGLE_WAYPOINTS' })}
          className={state.showWaypoints ? 'active' : ''}
        >
          Waypoints
        </button>
      </div>
    </div>
  );
}
