import { useState } from 'react';
import { ChevronDown, ChevronUp, ShieldAlert } from 'lucide-react';

interface SuspectVessel {
  mmsi: number;
  vessel_name: string;
  vessel_type: string;
  ai_explanation?: string;
  distance_deg: number;
  proximity_score: number;
  anomaly_score: number;
  ais_gap_flag: boolean;
  total_score: number;
}

function riskLabel(score: number) {
  if (score >= 0.6) return { text: 'High risk', color: 'text-rose-400', bg: 'bg-rose-950/40 border-rose-800' };
  if (score >= 0.3) return { text: 'Moderate risk', color: 'text-amber-400', bg: 'bg-slate-950/60 border-slate-800' };
  return { text: 'Low risk', color: 'text-slate-400', bg: 'bg-slate-950/60 border-slate-800' };
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2 text-xs mb-1.5">
      <span className="w-20 text-slate-500 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-9 text-right text-slate-400">{pct}%</span>
    </div>
  );
}

export default function VesselList({ vessels }: { vessels: SuspectVessel[] }) {
  const [openMmsi, setOpenMmsi] = useState<number | null>(vessels[0]?.mmsi ?? null);

  if (!vessels.length) {
    return (
      <div className="text-slate-600 text-xs py-6 text-center italic">
        No vessels found in the estimated origin window.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {vessels.map((v) => {
        const risk = riskLabel(v.total_score);
        const open = openMmsi === v.mmsi;
        return (
          <div
            key={v.mmsi}
            className={`rounded-xl border p-3 cursor-pointer transition-colors ${risk.bg}`}
            onClick={() => setOpenMmsi(open ? null : v.mmsi)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className={`w-4 h-4 ${risk.color}`} />
                <span className="text-sm font-medium text-slate-200">{v.vessel_name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-semibold ${risk.color}`}>{v.total_score}</span>
                {open ? (
                  <ChevronUp className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                )}
              </div>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {risk.text} Â· MMSI {v.mmsi} Â· {v.vessel_type}
            </p>

            {open && (
              <div className="mt-3 pt-3 border-t border-slate-800/80">
                {v.ai_explanation && (
                  <p className="text-xs text-slate-300 leading-relaxed mb-3 italic">
                    "{v.ai_explanation}"
                  </p>
                )}
                <ScoreBar label="Proximity" value={v.proximity_score} color="#378add" />
                <ScoreBar label="Behavior" value={v.anomaly_score} color="#ef9f27" />
                <ScoreBar label="AIS gap" value={v.ais_gap_flag ? 1 : 0} color="#e24b4a" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}