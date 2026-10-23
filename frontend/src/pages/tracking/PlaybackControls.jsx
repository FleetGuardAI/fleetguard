import React, { useMemo } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  SkipBack, 
  SkipForward, 
  ChevronLeft, 
  ChevronRight, 
  Gauge, 
  Compass, 
  Clock, 
  MapPin,
  Crosshair
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatDateTime, formatDurationMinutes } from '@/utils/dateTime';

/**
 * PlaybackControls
 * Floating playback dock providing scrubber timeline, telemetry HUD, 
 * variable speeds (1x, 2x, 4x, 8x), and step controls.
 */
export function PlaybackControls({
  points = [],
  currentIndex = 0,
  isPlaying = false,
  speedMultiplier = 1,
  onPlayPause,
  onSeek,
  onRestart,
  onSpeedChange,
  onStepBack,
  onStepForward,
  onJumpStart,
  onJumpEnd,
  className
}) {
  if (!points || points.length === 0) return null;

  const currentPoint = points[currentIndex] || points[0];
  const startPoint = points[0];
  const endPoint = points[points.length - 1];

  // Calculate elapsed time from start of dataset
  const elapsedTimeText = useMemo(() => {
    if (!startPoint || !currentPoint) return '0m';
    const startMs = new Date(startPoint.timestamp).getTime();
    const currMs = new Date(currentPoint.timestamp).getTime();
    const diffMinutes = Math.max(0, Math.round((currMs - startMs) / 60000));
    return formatDurationMinutes(diffMinutes);
  }, [startPoint, currentPoint]);

  // Current speed in km/h
  const currentSpeedKmh = useMemo(() => {
    if (!currentPoint) return null;
    if (typeof currentPoint.speed_kmh === 'number') return currentPoint.speed_kmh;
    if (typeof currentPoint.speed === 'number') return currentPoint.speed * 3.6;
    return null;
  }, [currentPoint]);

  const speeds = [1, 2, 4, 8];

  return (
    <div 
      className={cn(
        "bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 shadow-2xl p-3 sm:p-4 text-slate-800 transition-all",
        className
      )}
    >
      {/* ── Top Row: Timeline Scrubber + Timestamps ─────────────────────── */}
      <div className="space-y-1.5 mb-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
          <div className="flex items-center gap-2">
            <span className="font-mono text-brand-700 bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200">
              {formatDateTime(currentPoint.timestamp, 'HH:mm:ss')}
            </span>
            <span className="text-[11px] text-slate-400">
              {formatDateTime(currentPoint.timestamp, 'dd MMM yyyy')}
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] font-medium text-slate-500">
            <span>+{elapsedTimeText} elapsed</span>
            <span>•</span>
            <span className="font-mono">
              Pt {currentIndex + 1} / {points.length}
            </span>
          </div>
        </div>

        {/* Scrubber Range Input */}
        <div className="relative flex items-center">
          <input
            type="range"
            min={0}
            max={points.length - 1}
            value={currentIndex}
            onChange={(e) => onSeek && onSeek(parseInt(e.target.value, 10))}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600 focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
          <span>{formatDateTime(startPoint.timestamp, 'HH:mm')}</span>
          <span>{formatDateTime(endPoint.timestamp, 'HH:mm')}</span>
        </div>
      </div>

      {/* ── Bottom Row: HUD Telemetry + Playback Buttons + Speeds ───────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-100">
        {/* Left: Telemetry Badges */}
        <div className="flex items-center gap-3">
          {/* Speed Badge */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg">
            <Gauge className="w-3.5 h-3.5 text-brand-600" />
            <div className="flex flex-col">
              <span className="text-[8px] uppercase tracking-wider text-slate-400 font-bold leading-none">Speed</span>
              <span className="text-xs font-mono font-bold text-slate-800 leading-tight">
                {currentSpeedKmh !== null ? `${currentSpeedKmh.toFixed(1)} km/h` : 'N/A'}
              </span>
            </div>
          </div>

          {/* Heading Badge */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg">
            <Compass 
              className="w-3.5 h-3.5 text-blue-600 transition-transform" 
              style={{ transform: `rotate(${currentPoint.heading || 0}deg)` }} 
            />
            <div className="flex flex-col">
              <span className="text-[8px] uppercase tracking-wider text-slate-400 font-bold leading-none">Heading</span>
              <span className="text-xs font-mono font-bold text-slate-800 leading-tight">
                {typeof currentPoint.heading === 'number' ? `${Math.round(currentPoint.heading)}°` : 'N/A'}
              </span>
            </div>
          </div>

          {/* GPS Accuracy Badge */}
          {typeof currentPoint.accuracy === 'number' && (
            <div className="hidden md:flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg">
              <Crosshair className="w-3.5 h-3.5 text-emerald-600" />
              <div className="flex flex-col">
                <span className="text-[8px] uppercase tracking-wider text-slate-400 font-bold leading-none">Accuracy</span>
                <span className="text-xs font-mono font-bold text-slate-800 leading-tight">
                  &plusmn;{currentPoint.accuracy.toFixed(1)}m
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Center: Controls Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={onRestart}
            title="Restart from beginning"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onJumpStart}
            title="Jump to start"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onStepBack}
            title="Previous GPS point"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Big Play / Pause Button */}
          <button
            type="button"
            onClick={onPlayPause}
            title={isPlaying ? "Pause playback (Space)" : "Play route (Space)"}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-brand-600 text-white hover:bg-brand-700 shadow-md transition-transform active:scale-95"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5 fill-white" />
            ) : (
              <Play className="w-5 h-5 fill-white ml-0.5" />
            )}
          </button>

          <button
            type="button"
            onClick={onStepForward}
            title="Next GPS point"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onJumpEnd}
            title="Jump to end"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        {/* Right: Playback Speeds */}
        <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
          {speeds.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSpeedChange && onSpeedChange(s)}
              className={cn(
                "px-2 py-0.5 text-xs font-bold rounded-md transition-colors",
                speedMultiplier === s
                  ? "bg-white text-brand-700 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
