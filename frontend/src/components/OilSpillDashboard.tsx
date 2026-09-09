import { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Compass, 
  Activity, 
  Layers, 
  RefreshCw,
  Search,
  ShieldAlert
} from 'lucide-react';
import SpillMap from './SpillMap';
import VesselList from './VesselList';

// --- Type Definitions ---
interface Centroid {
  lat: number;
  lon: number;
}

interface Detection {
  centroid: Centroid;
  area_km2: number;
  detected_at: string;
  shape: string;
}

interface Origin {
  lat: number;
  lon: number;
  estimated_time: string;
  confidence: string;
}

interface SuspectVessel {
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  lat: number;
  lon: number;
  ai_explanation?: string;
  distance_deg: number;
  proximity_score: number;
  anomaly_score: number;
  ais_gap_flag: boolean;
  total_score: number;
}

interface AnalysisResponse {
  detection: Detection;
  origin: Origin;
  suspects: SuspectVessel[];
}

export default function OilSpillDashboard() {
  // State Management
  const [spillId, setSpillId] = useState<string>('spill_01');
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Backend API URL Base
  const API_BASE_URL = 'http://127.0.0.1:8000';

  // Fetch Data from FastAPI Backend
  const handleAnalyzeSpill = async (idToAnalyze = spillId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/spill-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ spill_id: idToAnalyze }),
      });

      if (!response.ok) {
        throw new Error(`Server returned code ${response.status}. Ensure mock JSON file exists.`);
      }

      const result: AnalysisResponse = await response.json();
      console.log("--- FASTAPI API PIPELINE RESPONSE ---", result);

      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  };

  // Trigger initial fetch on load for spill_01
  useEffect(() => {
    handleAnalyzeSpill('spill_01');
  }, []);

  return (
    <div className="min-h-screen lg:h-screen bg-slate-900 text-slate-100 font-sans p-3 lg:p-4 overflow-auto lg:overflow-hidden">
      {/* Header Panel */}
      <header className="shrink-0 flex flex-col lg:flex-row justify-between items-start lg:items-center border-b border-slate-800 pb-3 mb-3 lg:mb-4 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-amber-500 w-8 h-8 animate-pulse" />
            <h1 className="text-xl sm:text-2xl lg:text-2xl font-bold leading-tight tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
              OceanGuard: Oil Spill Drift & Attribution Matrix
            </h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">
           
          </p>
        </div>

        {/* Query Input Section */}
        <div className="flex items-center gap-2 w-full lg:w-auto shrink-0">
          <div className="relative flex-grow md:flex-grow-0">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={spillId}
              onChange={(e) => setSpillId(e.target.value)}
              placeholder="Enter Spill ID (e.g. spill_01)"
              className="bg-slate-950 text-slate-200 pl-9 pr-4 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-amber-500 w-full lg:w-52 xl:w-60 text-sm transition-all"
            />
          </div>
          <button
            onClick={() => handleAnalyzeSpill()}
            disabled={loading}
            className="flex items-center gap-2 bg-amber-600 hover:bg-amber-500 active:bg-amber-700 disabled:bg-slate-800 disabled:text-slate-500 px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-amber-900/20"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            Analyze Pipeline
          </button>
        </div>
      </header>

      {/* Error Alert Bar */}
      {error && (
        <div className="bg-rose-950/40 border border-rose-800 text-rose-300 p-4 rounded-xl mb-6 text-sm flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <span><strong>API Error:</strong> {error}</span>
        </div>
      )}

      {/* Primary Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 lg:gap-4 items-stretch lg:h-[calc(100vh-155px)] lg:min-h-0">
        
        {/* LEFT COLUMN: TELEMETRY & GEO-DATA */}
        <div className="grid grid-rows-2 gap-3 lg:gap-4 lg:min-h-0">
          {/* Section 1: SAR Sat Output */}
          <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-2xl border border-slate-800/80 min-h-0 overflow-hidden">
            <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase flex items-center gap-2 mb-4">
              <Layers className="w-4 h-4 text-sky-400" />
              SAR Satellite Segmentation Input
            </h2>
            {data ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">Target Spill Identifier:</span>
                  <span className="font-mono text-amber-400 font-medium">{spillId}</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">SAR Profile Shape:</span>
                  <span className="capitalize text-slate-300 font-medium">{data.detection.shape}</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">Surface Boundary Area:</span>
                  <span className="text-slate-300 font-medium">{data.detection.area_km2} km²</span>
                </div>
                <div className="flex justify-between pb-1">
                  <span className="text-slate-500">Sensing Timestamp:</span>
                  <span className="text-slate-300 font-mono text-xs">{data.detection.detected_at}</span>
                </div>
              </div>
            ) : (
              <div className="text-slate-600 text-xs py-4 text-center italic">Waiting for analysis sequence execution...</div>
            )}
          </div>

          {/* Section 2: Hydrodynamic Drift Simulation */}
          <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-2xl border border-slate-800/80 min-h-0 overflow-hidden">
            <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase flex items-center gap-2 mb-4">
              <Compass className="w-4 h-4 text-teal-400" />
              Backward Drift Trajectory Matrix
            </h2>
            <p className="text-[11px] text-slate-500 italic mt-0.5 mb-3">
  Origin traced backward from drift — not just current slick position
</p>
            {data ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">Estimated Source Lat:</span>
                  <span className="font-mono text-teal-400 font-medium">{data.origin.lat.toFixed(4)}° N</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">Estimated Source Lon:</span>
                  <span className="font-mono text-teal-400 font-medium">{data.origin.lon.toFixed(4)}° E</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-500">Calculated Spill Release:</span>
                  <span className="text-slate-300 font-mono text-xs">{data.origin.estimated_time}</span>
                </div>
                <div className="flex justify-between pb-1">
                  <span className="text-slate-500">Solver State:</span>
                  <span className="text-slate-400 italic capitalize">{data.origin.confidence}</span>
                </div>
              </div>
            ) : (
              <div className="text-slate-600 text-xs py-4 text-center italic">Awaiting trajectory compute vector...</div>
            )}
          </div>
        </div>

        {/* CENTER COLUMN: LIVE MAP LEAFLET VIEWPORT CANVAS */}
                {/* CENTER COLUMN: LIVE MAP LEAFLET VIEWPORT CANVAS */}
        <div className="lg:col-span-1 min-h-0">
          <div className="bg-slate-950/60 backdrop-blur-md p-3 rounded-2xl border border-slate-800/80 flex flex-col h-[430px] lg:h-full min-h-0">
            {data ? (
              <SpillMap
                detectionCenter={[data.detection.centroid.lat, data.detection.centroid.lon]}
                originCenter={[data.origin.lat, data.origin.lon]}
                vessels={data.suspects}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-600 text-xs italic">
                Waiting for analysis sequence execution...
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: RANKED SUSPECT VESSELS */}
        <div className="lg:col-span-1 min-h-0">
          <div className="bg-slate-950/60 backdrop-blur-md p-4 rounded-2xl border border-slate-800/80 h-[430px] lg:h-full flex flex-col min-h-0 overflow-hidden">
            <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Ranked Suspect Vessels
            </h2>
            <p className="text-[11px] text-slate-500 italic mb-4">
  Scored on proximity + behavior + AIS gaps, not distance alone
</p>
            {data ? (
              <div className="flex-1 overflow-y-auto pr-1">
  <VesselList vessels={data.suspects} />
</div>
            ) : (
              <div className="text-slate-600 text-xs py-4 text-center italic">Awaiting attribution scan...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}