import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Navigation, Fuel, Clock, User, Hash, Gauge,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function VehicleDetailOverlay({ vehicle, onClose }) {
  const navigate = useNavigate();

  if (!vehicle) return null;

  const statusColors = {
    active: { bg: 'bg-fg-green/15', text: 'text-fg-green', label: 'On Route' },
    idle: { bg: 'bg-content-muted/10', text: 'text-content-muted', label: 'Idle' },
    delayed: { bg: 'bg-fg-amber/15', text: 'text-fg-amber', label: 'Delayed' },
    alert: { bg: 'bg-fg-red/15', text: 'text-fg-red', label: 'Alert' },
  };
  const status = statusColors[vehicle.status] || statusColors.active;

  return (
    <AnimatePresence>
      <motion.div
        className="absolute bottom-4 right-4 z-[600] w-[260px] bg-[#0B1018]/95 backdrop-blur-xl border border-white/8 rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.5)] overflow-hidden"
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
          <div>
            <p className="text-[13px] font-semibold text-white tracking-tight">{vehicle.id}</p>
            <p className="text-[10px] text-white/50 font-light mt-0.5">{vehicle.route || '—'}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/5 text-white/40 hover:text-white/70 transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Metrics grid */}
        <div className="grid grid-cols-3 gap-px bg-white/5 mx-3 my-3 rounded-xl overflow-hidden">
          <div className="bg-[#0B1018] p-2.5 text-center">
            <Gauge className="w-3 h-3 text-white/40 mx-auto mb-1" />
            <p className="text-[12px] font-semibold text-white">{vehicle.speed || 0}</p>
            <p className="text-[8px] text-white/40 uppercase tracking-wider">km/h</p>
          </div>
          <div className="bg-[#0B1018] p-2.5 text-center">
            <Fuel className="w-3 h-3 text-white/40 mx-auto mb-1" />
            <p className="text-[12px] font-semibold text-white">{vehicle.fuel || '—'}%</p>
            <p className="text-[8px] text-white/40 uppercase tracking-wider">Fuel</p>
          </div>
          <div className="bg-[#0B1018] p-2.5 text-center">
            <Clock className="w-3 h-3 text-white/40 mx-auto mb-1" />
            <p className="text-[12px] font-semibold text-white">{vehicle.eta || '—'}</p>
            <p className="text-[8px] text-white/40 uppercase tracking-wider">ETA</p>
          </div>
        </div>

        {/* Driver & Trip */}
        <div className="px-4 pb-3 space-y-2">
          <div className="flex items-center gap-2">
            <User className="w-3 h-3 text-white/30" />
            <span className="text-[11px] text-white/70 font-light">{vehicle.driver_name || 'Unknown'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Hash className="w-3 h-3 text-white/30" />
            <span className="text-[11px] text-white/70 font-light">Trip {vehicle.trip || '—'}</span>
          </div>

          {/* Status + Action */}
          <div className="flex items-center justify-between pt-2 border-t border-white/5">
            <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-md ${status.bg} ${status.text}`}>
              {status.label}
            </span>
            <button
              onClick={() => navigate('/dashboard/trips')}
              className="text-[10px] font-semibold text-fg-green hover:text-fg-green/80 transition-colors"
            >
              View Trip →
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
