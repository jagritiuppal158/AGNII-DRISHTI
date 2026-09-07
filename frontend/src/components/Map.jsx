import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './Map.css';

const classColors = {
  industrial_fire: '#ef4444',
  wildfire: '#f97316',
  crop_burning: '#eab308',
  gas_flare: '#3b82f6',
  mining: '#a855f7',
};

const classLabels = {
  industrial_fire: 'Industrial Fire',
  wildfire: 'Wildfire',
  crop_burning: 'Crop Burning',
  gas_flare: 'Gas Flare',
  mining: 'Mining',
};

function createClassIcon(className, priorityScore = 0.5) {
  const color = classColors[className] || '#ef4444';
  const baseSize = 24;
  const maxSize = 36;
  const size = Math.round(baseSize + (maxSize - baseSize) * priorityScore);
  const glowOpacity = 0.3 + 0.5 * priorityScore;

  return L.divIcon({
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid #0f172a;
        box-shadow: 
          0 0 ${Math.round(8 + 16 * priorityScore)}px ${Math.round(2 + 4 * priorityScore)}px ${color}${Math.round(glowOpacity * 255).toString(16).padStart(2, '0')},
          0 0 0 2px ${color};
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: ${Math.round(size * 0.4)}px;
          height: ${Math.round(size * 0.4)}px;
          border-radius: 50%;
          background: ${color};
          opacity: 0.9;
        "></div>
      </div>
    `,
    className: 'custom-marker-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

function createPendingIcon(priorityScore = 0.5) {
  const color = '#f59e0b';
  const baseSize = 24;
  const maxSize = 36;
  const size = Math.round(baseSize + (maxSize - baseSize) * priorityScore);
  const glowOpacity = 0.3 + 0.5 * priorityScore;

  return L.divIcon({
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid #0f172a;
        box-shadow: 
          0 0 ${Math.round(8 + 16 * priorityScore)}px ${Math.round(2 + 4 * priorityScore)}px ${color}${Math.round(glowOpacity * 255).toString(16).padStart(2, '0')},
          0 0 0 2px ${color};
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: ${Math.round(size * 0.4)}px;
          height: ${Math.round(size * 0.4)}px;
          border-radius: 50%;
          background: ${color};
          opacity: 0.9;
        "></div>
      </div>
    `,
    className: 'custom-marker-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

function PopupContent({ location, selectedLocationId, onLocationClick, classLabels }) {
  const classColorMap = {
    industrial_fire: 'red',
    wildfire: 'orange',
    crop_burning: 'yellow',
    gas_flare: 'blue',
    mining: 'purple',
  };
  const statusColorMap = {
    new: 'green',
    recurring: 'amber',
    persistent: 'red',
    escalated: 'red',
  };
  const hasClassification = location.current_class && location.current_confidence !== null;
  const currentClass = location.current_class;
  const cClass = hasClassification ? classColorMap[currentClass] : 'amber';
  const cStatus = statusColorMap[location.status] || 'green';

  return (
    <div className="p-2 min-w-[200px]">
      <h3 className="font-semibold text-slate-100 text-sm">{location.name}</h3>
      <p className="text-xs text-slate-400 mt-1">
        {location.region} • {hasClassification ? classLabels[currentClass] : 'Pending classification'}
      </p>
      <div className="flex items-center gap-2 mt-2">
        {hasClassification ? (
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-${cClass}-500/20 text-${cClass}-400 border-${cClass}-500/30`}>
            {classLabels[currentClass]}
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-amber-500/20 text-amber-400 border-amber-500/30">
            Pending classification
          </span>
        )}
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-${cStatus}-500/20 text-${cStatus}-400 border-${cStatus}-500/30`}>
          {location.status}
        </span>
      </div>
      <p className="text-xs text-slate-500 mt-2">
        Confidence: {location.current_confidence ? (location.current_confidence * 100).toFixed(0) + '%' : '—'} • Detections: {location.detection_count}
      </p>
      <button
        onClick={() => onLocationClick(location.id)}
        className="mt-2 w-full btn-primary text-xs py-1"
      >
        {selectedLocationId === location.id ? 'Selected' : 'Select Location'}
      </button>
    </div>
  );
}

function MapView({ locations, selectedLocationId, onLocationClick }) {
  const mapCenter = [23.5, 80.0];
  const mapZoom = 4;

  return (
    <MapContainer
      center={mapCenter}
      zoom={mapZoom}
      zoomControl={true}
      scrollWheelZoom={true}
      className="w-full h-full"
      style={{ height: '100%', zIndex: 1 }}
    >
      <TileLayer
        url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={20}
      />
      {locations.map((location) => (
        <Marker
          key={location.id}
          position={[location.latitude, location.longitude]}
          icon={location.current_class
            ? createClassIcon(location.current_class, location.priority_score || 0.5)
            : createPendingIcon(location.priority_score || 0.5)}
        >
          <Popup offset={[0, -10]} className="agni-popup">
            <PopupContent
              location={location}
              selectedLocationId={selectedLocationId}
              onLocationClick={onLocationClick}
              classLabels={classLabels}
            />
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default MapView;