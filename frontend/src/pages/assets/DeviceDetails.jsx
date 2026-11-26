import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Cpu,
  Wifi,
  WifiOff,
  Clock,
  Truck,
  ArrowLeft,
  RefreshCw,
  Edit,
  Radio,
  Share2,
  Trash2,
  Play,
  Pause,
  RotateCcw,
  Navigation,
  Gauge,
  BatteryCharging,
  Zap,
  MapPin,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  History,
  ShieldCheck,
  Server
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useToast } from '@/components/ui/Toast';
import { getVehicles } from '@/api/vehicleApi';
import {
  getHardwareDeviceById,
  testHardwareConnection,
  getDeviceLocationHistory,
  disconnectHardwareDevice,
  removeHardwareDevice,
} from '@/api/assetApi';

import ReassignVehicleModal from './ReassignVehicleModal';
import EditDeviceModal from './EditDeviceModal';

// Leaflet helper to dynamically re-center map
function MapUpdater({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom || map.getZoom());
    }
  }, [center, zoom, map]);
  return null;
}

// Custom vehicle divIcon for Leaflet
function getVehicleIcon(heading = 0, isConnected = true, isIgnition = false) {
  const bg = isConnected ? (isIgnition ? 'bg-green-600' : 'bg-brand-600') : 'bg-gray-600';
  return L.divIcon({
    className: 'custom-vehicle-marker',
    html: `
      <div style="transform: rotate(${heading || 0}deg);" class="relative flex items-center justify-center">
        <div class="w-9 h-9 rounded-full ${bg} text-white shadow-lg flex items-center justify-center border-2 border-white transition-transform">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/>
          </svg>
        </div>
        ${isConnected ? '<span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-400 animate-ping opacity-75"></span>' : ''}
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

function getWayPointIcon(idx, isFirst, isLast) {
  const color = isFirst ? 'bg-blue-600' : isLast ? 'bg-red-600' : 'bg-gray-400';
  return L.divIcon({
    className: 'custom-waypoint',
    html: `<div class="w-3.5 h-3.5 rounded-full ${color} border-2 border-white shadow"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

// Convert heading angle to compass label
function getCompassDirection(deg) {
  if (deg === null || deg === undefined) return 'N/A';
  const dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const idx = Math.round((deg % 360) / 22.5) % 16;
  return `${Math.round(deg)}° (${dirs[idx]})`;
}

export default function DeviceDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [device, setDevice] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Modals
  const [reassignOpen, setReassignOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);

  // Tab
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'history' | 'health' | 'audit'

  // Location History & Playback
  const [historyLoading, setHistoryLoading] = useState(false);
  const [locations, setLocations] = useState([]);
  const [analytics, setAnalytics] = useState({ distance_km: 0, max_speed_kmh: 0, avg_speed_kmh: 0 });
  const [timeRange, setTimeRange] = useState('1h'); // '1h' | '6h' | 'today' | 'yesterday' | 'custom'
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  // Playback Animation State
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 5x
  const playbackTimerRef = useRef(null);

  const loadDeviceData = async () => {
    setLoading(true);
    try {
      const [devData, vData] = await Promise.all([
        getHardwareDeviceById(id),
        getVehicles().catch(() => [])
      ]);
      setDevice(devData);
      setVehicles(vData || []);
    } catch (err) {
      console.error(err);
      toastError('Failed to Load Device', err.message || 'Device could not be found.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeviceData();
  }, [id]);

  // Load location history based on time filter
  const fetchLocationHistory = async () => {
    if (!id) return;
    setHistoryLoading(true);
    setIsPlaying(false);
    setPlaybackIndex(0);

    const now = new Date();
    let startTime;
    let endTime = now.toISOString();

    if (timeRange === '1h') {
      startTime = new Date(now.getTime() - 1 * 3600 * 1000).toISOString();
    } else if (timeRange === '6h') {
      startTime = new Date(now.getTime() - 6 * 3600 * 1000).toISOString();
    } else if (timeRange === 'today') {
      const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
      startTime = startOfDay.toISOString();
    } else if (timeRange === 'yesterday') {
      const startOfYesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 0, 0, 0);
      const endOfYesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59);
      startTime = startOfYesterday.toISOString();
      endTime = endOfYesterday.toISOString();
    } else if (timeRange === 'custom') {
      if (customStart) startTime = new Date(customStart).toISOString();
      if (customEnd) endTime = new Date(customEnd).toISOString();
    }

    try {
      const res = await getDeviceLocationHistory(id, {
        start_time: startTime,
        end_time: endTime,
        limit: 1000,
      });
      setLocations(res.locations || []);
      setAnalytics({
        distance_km: res.distance_km || 0,
        max_speed_kmh: res.max_speed_kmh || 0,
        avg_speed_kmh: res.avg_speed_kmh || 0,
      });
    } catch (err) {
      console.error(err);
      toastError('History Query Failed', err.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchLocationHistory();
    }
  }, [id, activeTab, timeRange]);

  // Playback Loop
  useEffect(() => {
    if (isPlaying && locations.length > 0) {
      const intervalMs = Math.max(100, Math.floor(1000 / playbackSpeed));
      playbackTimerRef.current = setInterval(() => {
        setPlaybackIndex(prev => {
          if (prev >= locations.length - 1) {
            setIsPlaying(false);
            return locations.length - 1;
          }
          return prev + 1;
        });
      }, intervalMs);
    } else {
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    }
    return () => {
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    };
  }, [isPlaying, playbackSpeed, locations.length]);

  // Test Connection
  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testHardwareConnection(id);
      setTestResult(res);
      if (res.connected) {
        success('Connection Online', `Device responded. Latency: ${res.latency_ms}ms.`);
      } else {
        toastError('Device Offline', res.message || 'No response from device.');
      }
      loadDeviceData();
    } catch (err) {
      toastError('Test Failed', err.message);
    } finally {
      setTesting(false);
    }
  };

  // Disconnect to Storage
  const handleDisconnect = async () => {
    if (!window.confirm('Unassign this device and move to storage inventory?')) return;
    try {
      await disconnectHardwareDevice(id);
      success('Device Unassigned', 'Moved to storage inventory.');
      loadDeviceData();
    } catch (err) {
      toastError('Action Failed', err.message);
    }
  };

  // Remove Device
  const handleRemove = async () => {
    if (!window.confirm('Are you sure you want to retire this device permanently?')) return;
    try {
      await removeHardwareDevice(id);
      success('Device Retired', 'Asset retired from service.');
      navigate('/dashboard/assets');
    } catch (err) {
      toastError('Retirement Failed', err.message);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-8 w-48 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!device) {
    return (
      <div className="p-8 text-center space-y-3">
        <p className="text-content-secondary">Hardware device not found.</p>
        <Button variant="outline" onClick={() => navigate('/dashboard/assets')}>
          Back to Hardware Assets
        </Button>
      </div>
    );
  }

  const isConnected = device.connection_status === 'CONNECTED';
  const isPending = device.connection_status === 'PENDING';
  const hasCoordinates = device.last_known_lat !== null && device.last_known_lng !== null;
  const currentCoord = hasCoordinates
    ? [device.last_known_lat, device.last_known_lng]
    : [28.6139, 77.2090]; // Default New Delhi fallback if no coordinate

  // Polyline coordinates for history route
  const routePolyline = locations.map(l => [l.latitude, l.longitude]);
  const currentPlaybackPoint = locations[playbackIndex] || locations[locations.length - 1] || null;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-content-muted mb-1">
            <Link to="/dashboard/assets" className="hover:text-content flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Hardware Assets
            </Link>
            <span>/</span>
            <span className="font-mono">{device.business_id}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-content">{device.device_name}</h1>
            <Badge
              variant={isConnected ? 'success' : isPending ? 'info' : 'warning'}
              size="sm"
              dot
            >
              {device.connection_status}
            </Badge>
            {device.is_stale && (
              <Badge variant="danger" size="sm">
                STALE TELEMETRY
              </Badge>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleTestConnection}
            disabled={testing}
            icon={<Radio className={`w-3.5 h-3.5 ${testing ? 'animate-pulse text-green-600' : ''}`} />}
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={() => setReassignOpen(true)}
            icon={<Truck className="w-3.5 h-3.5" />}
          >
            Reassign Vehicle
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={() => setEditOpen(true)}
            icon={<Edit className="w-3.5 h-3.5" />}
          >
            Edit
          </Button>

          {device.current_vehicle_id && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleDisconnect}
              className="text-amber-600 hover:bg-amber-50"
            >
              Disconnect
            </Button>
          )}

          <Button
            size="sm"
            variant="ghost"
            onClick={handleRemove}
            className="text-red-500 hover:text-red-600 hover:bg-red-50"
            icon={<Trash2 className="w-3.5 h-3.5" />}
          />
        </div>
      </div>

      {/* Stale Warning Alert */}
      {device.is_stale && (
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5 shadow-sm">
          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <span className="font-semibold">Telemetry Data is Stale:</span>
            <span className="ml-1">
              Last communication received was{' '}
              <strong>
                {device.last_communication_at
                  ? new Date(device.last_communication_at).toLocaleString()
                  : 'Never'}
              </strong>
              . This exceeds the configured silence threshold of {device.offline_threshold_minutes} minutes. Displayed coordinates represent the last known location.
            </span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border gap-6">
        <button
          onClick={() => setActiveTab('live')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'live'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-content-secondary hover:text-content'
          }`}
        >
          <Navigation className="w-4 h-4" /> Live Tracking & Telemetry
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'history'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-content-secondary hover:text-content'
          }`}
        >
          <History className="w-4 h-4" /> Route History & Playback
        </button>

        <button
          onClick={() => setActiveTab('health')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'health'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-content-secondary hover:text-content'
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> Device Health & Specs
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'audit'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-content-secondary hover:text-content'
          }`}
        >
          <Clock className="w-4 h-4" /> Audit Lifecycle
        </button>
      </div>

      {/* TAB 1: Live Tracking & Telemetry */}
      {activeTab === 'live' && (
        <div className="space-y-4">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Current Speed</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-xl font-bold text-content">
                  {device.last_known_speed !== null ? Math.round(device.last_known_speed) : 0}
                </span>
                <span className="text-xs text-content-muted">km/h</span>
              </div>
            </Card>

            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Ignition State</span>
              <div className="flex items-center gap-1.5 mt-1">
                <span
                  className={`w-2 h-2 rounded-full ${
                    device.last_known_ignition ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                  }`}
                />
                <span className="text-sm font-bold text-content">
                  {device.last_known_ignition ? 'IGNITION ON' : 'IGNITION OFF'}
                </span>
              </div>
            </Card>

            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Heading</span>
              <p className="text-sm font-bold text-content mt-1">
                {getCompassDirection(device.last_known_heading)}
              </p>
            </Card>

            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Assigned Truck</span>
              <p className="text-sm font-bold font-mono text-brand-700 mt-1">
                {device.vehicle_registration || 'Unassigned (Storage)'}
              </p>
            </Card>

            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Battery Voltage</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-sm font-bold text-content">
                  {device.last_known_battery ? `${device.last_known_battery}V` : '12.4V (Nominal)'}
                </span>
              </div>
            </Card>

            <Card className="p-3 border border-border shadow-card bg-surface">
              <span className="text-[11px] text-content-muted">Last Communication</span>
              <p className="text-xs font-semibold text-content mt-1 line-clamp-1">
                {device.last_communication_at
                  ? new Date(device.last_communication_at).toLocaleTimeString()
                  : 'Never'}
              </p>
            </Card>
          </div>

          {/* Interactive Leaflet Map Card */}
          <Card padding="none" className="overflow-hidden border border-border shadow-card rounded-2xl">
            <div className="p-3 bg-surface border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-brand-600" />
                <span className="text-xs font-semibold text-content">
                  {device.last_known_address || 'Live Telematics Coordinates'}
                </span>
                <span className="text-xs font-mono text-content-muted">
                  ({device.last_known_lat?.toFixed(5) || '0.00000'}, {device.last_known_lng?.toFixed(5) || '0.00000'})
                </span>
              </div>
              <Button size="sm" variant="ghost" onClick={loadDeviceData} icon={<RefreshCw className="w-3.5 h-3.5" />}>
                Refresh Position
              </Button>
            </div>

            <div className="h-[460px] w-full relative z-0">
              <MapContainer
                center={currentCoord}
                zoom={14}
                scrollWheelZoom={true}
                className="h-full w-full"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapUpdater center={currentCoord} zoom={14} />

                {hasCoordinates && (
                  <Marker
                    position={currentCoord}
                    icon={getVehicleIcon(device.last_known_heading, isConnected, device.last_known_ignition)}
                  >
                    <Popup>
                      <div className="p-1 space-y-1 text-xs">
                        <strong className="block text-sm">{device.device_name}</strong>
                        <div>Vehicle: {device.vehicle_registration || 'Unassigned'}</div>
                        <div>Speed: {Math.round(device.last_known_speed || 0)} km/h</div>
                        <div>Ignition: {device.last_known_ignition ? 'ON' : 'OFF'}</div>
                        <div>
                          Time: {device.last_communication_at ? new Date(device.last_communication_at).toLocaleTimeString() : 'N/A'}
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                )}
              </MapContainer>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: Route History & Playback */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <Card className="p-4 border border-border shadow-card bg-surface flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-content mr-1">Time Period:</span>
              {['1h', '6h', 'today', 'yesterday', 'custom'].map(t => (
                <button
                  key={t}
                  onClick={() => setTimeRange(t)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    timeRange === t
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'bg-surface-secondary text-content-secondary hover:text-content border border-border'
                  }`}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>

            {timeRange === 'custom' && (
              <div className="flex items-center gap-2 text-xs">
                <input
                  type="datetime-local"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="h-8 px-2 border border-border rounded bg-surface text-xs"
                />
                <span>to</span>
                <input
                  type="datetime-local"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="h-8 px-2 border border-border rounded bg-surface text-xs"
                />
                <Button size="sm" variant="outline" onClick={fetchLocationHistory}>
                  Apply
                </Button>
              </div>
            )}

            {/* Playback Controls */}
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant={isPlaying ? 'outline' : 'primary'}
                onClick={() => setIsPlaying(!isPlaying)}
                disabled={locations.length === 0}
                icon={isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              >
                {isPlaying ? 'Pause' : 'Play Route'}
              </Button>

              <select
                value={playbackSpeed}
                onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                className="h-8 px-2 border border-border rounded bg-surface text-xs font-medium"
              >
                <option value={1}>1x Speed</option>
                <option value={2}>2x Speed</option>
                <option value={5}>5x Speed</option>
              </select>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setIsPlaying(false);
                  setPlaybackIndex(0);
                }}
                icon={<RotateCcw className="w-3.5 h-3.5" />}
              />
            </div>
          </Card>

          {/* History Analytics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="p-3 bg-surface border border-border">
              <span className="text-[11px] text-content-muted">Distance Travelled</span>
              <p className="text-xl font-bold text-brand-700 mt-0.5">
                {analytics.distance_km.toFixed(2)} <span className="text-xs font-normal">km</span>
              </p>
            </Card>

            <Card className="p-3 bg-surface border border-border">
              <span className="text-[11px] text-content-muted">Max Speed</span>
              <p className="text-xl font-bold text-content mt-0.5">
                {Math.round(analytics.max_speed_kmh)} <span className="text-xs font-normal">km/h</span>
              </p>
            </Card>

            <Card className="p-3 bg-surface border border-border">
              <span className="text-[11px] text-content-muted">Average Speed</span>
              <p className="text-xl font-bold text-content mt-0.5">
                {Math.round(analytics.avg_speed_kmh)} <span className="text-xs font-normal">km/h</span>
              </p>
            </Card>

            <Card className="p-3 bg-surface border border-border">
              <span className="text-[11px] text-content-muted">Telemetry Waypoints</span>
              <p className="text-xl font-bold text-content mt-0.5">{locations.length}</p>
            </Card>
          </div>

          {/* Route Map & Playback Scrubber */}
          <Card padding="none" className="overflow-hidden border border-border shadow-card rounded-2xl">
            {locations.length > 0 && (
              <div className="p-3 bg-surface border-b border-border flex items-center gap-4">
                <input
                  type="range"
                  min={0}
                  max={locations.length - 1}
                  value={playbackIndex}
                  onChange={(e) => setPlaybackIndex(Number(e.target.value))}
                  className="w-full accent-brand-600 cursor-pointer"
                />
                <span className="text-xs font-mono text-content-muted shrink-0">
                  {playbackIndex + 1} / {locations.length}
                </span>
                {currentPlaybackPoint && (
                  <span className="text-xs font-medium text-brand-700 shrink-0">
                    {new Date(currentPlaybackPoint.recorded_at).toLocaleTimeString()} ({Math.round(currentPlaybackPoint.speed_kmh || 0)} km/h)
                  </span>
                )}
              </div>
            )}

            <div className="h-[460px] w-full relative z-0">
              <MapContainer
                center={routePolyline[0] || currentCoord}
                zoom={13}
                scrollWheelZoom={true}
                className="h-full w-full"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {routePolyline.length > 0 && (
                  <>
                    <Polyline positions={routePolyline} color="#16A34A" weight={4} opacity={0.8} />
                    <Marker
                      position={routePolyline[0]}
                      icon={getWayPointIcon(0, true, false)}
                    >
                      <Popup>Start Point: {new Date(locations[0].recorded_at).toLocaleTimeString()}</Popup>
                    </Marker>
                    <Marker
                      position={routePolyline[routePolyline.length - 1]}
                      icon={getWayPointIcon(routePolyline.length - 1, false, true)}
                    >
                      <Popup>End Point: {new Date(locations[locations.length - 1].recorded_at).toLocaleTimeString()}</Popup>
                    </Marker>
                  </>
                )}

                {currentPlaybackPoint && (
                  <Marker
                    position={[currentPlaybackPoint.latitude, currentPlaybackPoint.longitude]}
                    icon={getVehicleIcon(currentPlaybackPoint.heading, true, currentPlaybackPoint.ignition_status)}
                  >
                    <Popup>
                      <div className="text-xs">
                        <strong>Playback Frame</strong>
                        <div>Time: {new Date(currentPlaybackPoint.recorded_at).toLocaleString()}</div>
                        <div>Speed: {Math.round(currentPlaybackPoint.speed_kmh || 0)} km/h</div>
                      </div>
                    </Popup>
                  </Marker>
                )}

                {currentPlaybackPoint && (
                  <MapUpdater center={[currentPlaybackPoint.latitude, currentPlaybackPoint.longitude]} />
                )}
              </MapContainer>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 3: Device Health & Specifications */}
      {activeTab === 'health' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-5 border border-border shadow-card bg-surface space-y-4">
            <h3 className="text-sm font-bold text-content flex items-center gap-2">
              <Cpu className="w-4 h-4 text-brand-600" />
              Hardware Identity & Specifications
            </h3>
            <div className="divide-y divide-border text-xs">
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Business Asset ID:</span>
                <span className="font-mono font-bold text-content">{device.business_id}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">IMEI / Unique Identifier:</span>
                <span className="font-mono font-bold text-content">{device.imei}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Manufacturer:</span>
                <span className="font-semibold text-content">{device.manufacturer || 'Generic'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Model:</span>
                <span className="font-semibold text-content">{device.model || 'Standard Tracker'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Firmware Version:</span>
                <span className="font-mono text-content">{device.firmware_version || 'Not Reported'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Serial Number:</span>
                <span className="font-mono text-content">{device.serial_number || 'N/A'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Installation Date:</span>
                <span className="text-content">
                  {device.installation_date ? new Date(device.installation_date).toLocaleDateString() : 'N/A'}
                </span>
              </div>
            </div>
          </Card>

          <Card className="p-5 border border-border shadow-card bg-surface space-y-4">
            <h3 className="text-sm font-bold text-content flex items-center gap-2">
              <Radio className="w-4 h-4 text-brand-600" />
              Telematics Connection Parameters
            </h3>
            <div className="divide-y divide-border text-xs">
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Connection Architecture:</span>
                <Badge variant="brand" size="sm">{device.connection_type}</Badge>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Protocol:</span>
                <span className="font-mono font-bold text-brand-700">{device.protocol || 'DEFAULT'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">GPS Provider:</span>
                <span className="font-semibold text-content">{device.gps_provider || 'Direct Vahan Ingestion'}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Offline Silence Threshold:</span>
                <span className="font-semibold text-content">{device.offline_threshold_minutes} Minutes</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Mounting Status:</span>
                <span className="font-semibold text-content uppercase">{device.installation_status}</span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="text-content-secondary">Operational Health:</span>
                <span className="font-semibold text-green-600 uppercase">{device.operational_status}</span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: Audit Lifecycle Events */}
      {activeTab === 'audit' && (
        <Card className="p-5 border border-border shadow-card bg-surface space-y-4">
          <h3 className="text-sm font-bold text-content flex items-center gap-2">
            <History className="w-4 h-4 text-brand-600" />
            Device Audit Log & State Changes
          </h3>
          <div className="border border-border rounded-xl divide-y divide-border overflow-hidden">
            {(!device.history_records || device.history_records.length === 0) ? (
              <div className="p-4 text-center text-xs text-content-muted">
                No state transition history records logged yet.
              </div>
            ) : (
              device.history_records.map((h, idx) => (
                <div key={idx} className="p-3.5 flex items-start justify-between text-xs">
                  <div>
                    <span className="font-bold text-content">{h.event_category}</span>
                    <p className="text-content-secondary mt-0.5">
                      {h.details ? JSON.stringify(h.details) : 'Operational event recorded'}
                    </p>
                  </div>
                  <span className="text-content-muted text-[11px] shrink-0 font-mono">
                    {new Date(h.performed_at).toLocaleString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Modals */}
      <ReassignVehicleModal
        open={reassignOpen}
        onClose={() => setReassignOpen(false)}
        device={device}
        vehicles={vehicles}
        onSuccess={loadDeviceData}
      />

      <EditDeviceModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        device={device}
        onSuccess={loadDeviceData}
      />
    </div>
  );
}
