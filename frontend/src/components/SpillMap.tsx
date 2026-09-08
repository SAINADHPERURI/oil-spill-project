import { MapContainer, TileLayer, Popup, Polyline, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface VesselPoint {
  mmsi: number;
  vessel_name: string;
  lat: number;
  lon: number;
  total_score: number;
}

interface SpillMapProps {
  detectionCenter: [number, number];
  originCenter: [number, number];
  vessels: VesselPoint[];
}

function riskColor(score: number): string {
  if (score >= 0.6) return '#e24b4a';
  if (score >= 0.3) return '#ef9f27';
  return '#888780';
}

export default function SpillMap({ detectionCenter, originCenter, vessels }: SpillMapProps) {
  const mid: [number, number] = [
    (detectionCenter[0] + originCenter[0]) / 2,
    (detectionCenter[1] + originCenter[1]) / 2,
  ];

  const plottedVessels = vessels.filter(
    (v) => typeof v.lat === 'number' && typeof v.lon === 'number'
  );

  return (
    <MapContainer
      center={mid}
      zoom={9}
      style={{ height: '100%', width: '100%', minHeight: '420px', borderRadius: '16px' }}
    >
      <TileLayer
  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  attribution='&copy; OpenStreetMap contributors'
/>
      {/* Drift path: origin -> detected position */}
      <Polyline
        positions={[originCenter, detectionCenter]}
        pathOptions={{ color: '#d85a30', dashArray: '6 6', weight: 2 }}
      />

      {/* Detected slick */}
      <CircleMarker
        center={detectionCenter}
        radius={12}
        pathOptions={{ color: '#2c2c2a', fillColor: '#2c2c2a', fillOpacity: 0.6, weight: 1 }}
      >
        <Popup>Detected slick (current position)</Popup>
      </CircleMarker>

      {/* Estimated origin */}
      <CircleMarker
        center={originCenter}
        radius={8}
        pathOptions={{ color: '#993c1d', fillColor: '#f0997b', fillOpacity: 0.9, weight: 1.5 }}
      >
        <Popup>Estimated origin point/time</Popup>
      </CircleMarker>

      {/* Suspect vessels, colored by risk */}
      {plottedVessels.map((v) => (
        <CircleMarker
          key={v.mmsi}
          center={[v.lat, v.lon]}
          radius={6}
          pathOptions={{
            color: riskColor(v.total_score),
            fillColor: riskColor(v.total_score),
            fillOpacity: 0.9,
            weight: 1.5,
          }}
        >
          <Popup>
            {v.vessel_name} <br /> Risk score: {v.total_score}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
