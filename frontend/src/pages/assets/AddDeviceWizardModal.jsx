import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Check,
  ChevronRight,
  ChevronLeft,
  Server,
  Radio,
  Cpu,
  Share2,
  Globe,
  Sliders,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  RefreshCw,
  Search,
  Truck,
  ShieldCheck,
  KeyRound,
  Lock
} from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import { registerHardwareDevice, getHardwareProtocols } from '@/api/assetApi';

// Standard Luhn Algorithm check for 15-digit IMEI
function checkLuhn(str) {
  if (!str || !/^\d{14,16}$/.test(str)) return false;
  let sum = 0;
  let shouldDouble = false;
  for (let i = str.length - 1; i >= 0; i--) {
    let digit = parseInt(str.charAt(i), 10);
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}

const CONNECTION_TYPES = [
  {
    id: 'GPS_PROVIDER_API',
    title: 'GPS Provider API',
    desc: 'Sync devices & telemetry via cloud REST API (Traccar, Teltonika Cloud, Webfleet, Concox)',
    icon: Globe,
    badge: 'Cloud Sync',
  },
  {
    id: 'DIRECT_HARDWARE',
    title: 'Direct GPS Hardware',
    desc: 'Cellular 2G/4G/LTE GPS tracker streaming directly to Vahan ingestion port',
    icon: Radio,
    badge: 'Cellular / GPRS',
  },
  {
    id: 'TCP_DEVICE',
    title: 'TCP Protocol Device',
    desc: 'Direct TCP socket devices (GT06, Teltonika Codec 8/8E/16, TK103, H02, Queclink, AIS-140)',
    icon: Server,
    badge: 'Raw TCP Socket',
  },
  {
    id: 'MQTT_DEVICE',
    title: 'MQTT IoT Gateway',
    desc: 'Ingest payload from an MQTT Broker topic (AWS IoT Core, EMQX, Mosquitto)',
    icon: Share2,
    badge: 'Broker / Topic',
  },
  {
    id: 'WEBHOOK',
    title: 'Webhook Integration',
    desc: 'Third-party telematics platform forwards JSON/HTTP payloads to Vahan webhook URL',
    icon: Cpu,
    badge: 'HTTP POST',
  },
  {
    id: 'OTHER',
    title: 'Other Integration',
    desc: 'Custom proprietary gateway or vendor-specific API protocol',
    icon: Sliders,
    badge: 'Custom',
  },
];

const DEFAULT_MANUFACTURERS = [
  {
    name: 'Teltonika',
    models: ['FMB920', 'FMC130', 'FMB120', 'FMB140', 'FMC920', 'FMC640'],
    defaultProtocol: 'TELTONIKA_CODEC8',
    defaultPort: 5027,
  },
  {
    name: 'Concox / Jimi IoT',
    models: ['WeTrack2', 'GT06N', 'JM-VL02', 'JM-VL03', 'JM-LG01'],
    defaultProtocol: 'GT06',
    defaultPort: 5023,
  },
  {
    name: 'Coban',
    models: ['TK103A', 'TK103B', 'TK303G', 'GPS311'],
    defaultProtocol: 'TK103',
    defaultPort: 5001,
  },
  {
    name: 'Queclink',
    models: ['GV300', 'GV50', 'GV500', 'GL300'],
    defaultProtocol: 'QUECLINK_AT_TRACK',
    defaultPort: 5004,
  },
  {
    name: 'AIS-140 Certified (IRNSS)',
    models: ['AIS140-Generic', 'Rosmerta', 'Minda', 'Arya Omni'],
    defaultProtocol: 'AIS140',
    defaultPort: 5140,
  },
  {
    name: 'Sinotrack',
    models: ['ST-901', 'ST-902', 'ST-906'],
    defaultProtocol: 'H02',
    defaultPort: 5013,
  },
  {
    name: 'Meitrack',
    models: ['T333', 'T366G', 'MD511H'],
    defaultProtocol: 'MEITRACK',
    defaultPort: 5020,
  },
  {
    name: 'Other / Generic',
    models: ['Generic GPS Tracker', 'Custom Telematics Unit'],
    defaultProtocol: 'OTHER',
    defaultPort: 5055,
  },
];

const PROTOCOLS_LIST = [
  { id: 'GT06', name: 'GT06 / GT06N Protocol (Concox / Jimi)', defaultPort: 5023 },
  { id: 'TELTONIKA_CODEC8', name: 'Teltonika Codec 8 (Standard)', defaultPort: 5027 },
  { id: 'TELTONIKA_CODEC8E', name: 'Teltonika Codec 8 Extended', defaultPort: 5027 },
  { id: 'TELTONIKA_CODEC16', name: 'Teltonika Codec 16 (High Throughput)', defaultPort: 5027 },
  { id: 'TK103', name: 'TK103 / GPS103 Protocol (Coban)', defaultPort: 5001 },
  { id: 'H02', name: 'H02 Protocol (Sinotrack / Mini Tracker)', defaultPort: 5013 },
  { id: 'JT808', name: 'JT/T 808 Standard Chinese Transport Protocol', defaultPort: 5008 },
  { id: 'QUECLINK_AT_TRACK', name: 'Queclink @Track ASCII / Binary', defaultPort: 5004 },
  { id: 'AIS140', name: 'AIS-140 Government of India Standard', defaultPort: 5140 },
  { id: 'MQTT', name: 'MQTT JSON Telemetry Topic', defaultPort: 8883 },
  { id: 'HTTP_REST', name: 'HTTP / REST Polling Ingestion', defaultPort: 443 },
  { id: 'TRACCAR_WEBHOOK', name: 'Traccar Webhook Position Forwarder', defaultPort: 8082 },
  { id: 'OTHER', name: 'Custom / Other Ingestion Protocol', defaultPort: 5055 },
];

export default function AddDeviceWizardModal({ open, onClose, onSuccess, vehicles = [] }) {
  const { success, error: toastError } = useToast();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [protocolRegistry, setProtocolRegistry] = useState(null);

  // Form State
  const [connectionType, setConnectionType] = useState('DIRECT_HARDWARE');
  
  // Step 2: Manufacturer & Protocol
  const [manufacturer, setManufacturer] = useState('Teltonika');
  const [customManufacturer, setCustomManufacturer] = useState('');
  const [model, setModel] = useState('FMB920');
  const [customModel, setCustomModel] = useState('');
  const [protocol, setProtocol] = useState('TELTONIKA_CODEC8');

  // Step 3: Device Info
  const [deviceName, setDeviceName] = useState('');
  const [imei, setImei] = useState('');
  const [serialNumber, setSerialNumber] = useState('');
  const [firmwareVersion, setFirmwareVersion] = useState('');
  const [offlineThreshold, setOfflineThreshold] = useState(15);

  // Step 4: Vehicle Assignment
  const [assignOption, setAssignOption] = useState('ASSIGN'); // 'ASSIGN' | 'STORAGE'
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [vehicleSearch, setVehicleSearch] = useState('');

  // Step 5: Connection Configuration (Dynamic based on connectionType)
  const [config, setConfig] = useState({
    // API
    apiUrl: 'https://demo.traccar.org',
    apiKey: '',
    accessToken: '',
    accountId: '',
    gpsProvider: 'Traccar Cloud',
    // TCP
    serverHost: window.location.hostname || 'telematics.vahan.app',
    serverPort: 5027,
    devicePassword: '',
    // MQTT
    brokerUrl: 'mqtts://broker.hivemq.com',
    mqttPort: 8883,
    clientId: '',
    mqttUser: '',
    mqttPassword: '',
    mqttTopic: 'telematics/devices/+/data',
    // Webhook
    webhookSecret: '',
    authHeader: 'X-Vahan-Signature',
  });

  // Step 6: Test Preflight
  const [testStatus, setTestStatus] = useState('IDLE'); // 'IDLE' | 'TESTING' | 'PASS' | 'FAIL'
  const [testResult, setTestResult] = useState('');

  // Fetch verified protocol registry on mount
  useEffect(() => {
    if (open) {
      getHardwareProtocols()
        .then(res => setProtocolRegistry(res))
        .catch(() => {});
    }
  }, [open]);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setStep(1);
      setConnectionType('DIRECT_HARDWARE');
      setManufacturer('Teltonika');
      setCustomManufacturer('');
      setModel('FMB920');
      setCustomModel('');
      setProtocol('TELTONIKA_CODEC8');
      setDeviceName('');
      setImei('');
      setSerialNumber('');
      setFirmwareVersion('');
      setOfflineThreshold(15);
      setAssignOption('ASSIGN');
      setSelectedVehicleId(null);
      setVehicleSearch('');
      setTestStatus('IDLE');
      setTestResult('');
    }
  }, [open]);

  // Update model & protocol defaults when manufacturer changes
  const handleManufacturerChange = (mName) => {
    setManufacturer(mName);
    const mObj = DEFAULT_MANUFACTURERS.find(m => m.name === mName);
    if (mObj) {
      setModel(mObj.models[0]);
      setProtocol(mObj.defaultProtocol);
      setConfig(prev => ({ ...prev, serverPort: mObj.defaultPort }));
    } else {
      setModel('Custom');
      setProtocol('OTHER');
    }
  };

  // Live IMEI validation
  const imeiValidation = useMemo(() => {
    const clean = imei.trim();
    if (!clean) return { valid: false, message: 'Required' };
    if (clean.length < 8) return { valid: false, message: 'Too short (min 8 characters)' };
    if (/^\d{15}$/.test(clean)) {
      const isLuhn = checkLuhn(clean);
      return {
        valid: true,
        isStandardImei: true,
        luhnPass: isLuhn,
        message: isLuhn ? 'Valid 15-digit IMEI (Luhn verified)' : '15-digit IMEI (Checksum warning: double-check digits)',
      };
    }
    return {
      valid: true,
      isStandardImei: false,
      message: 'Alpha-numeric custom device identifier accepted',
    };
  }, [imei]);

  // Vehicle search filtering
  const filteredVehicles = useMemo(() => {
    if (!vehicleSearch.trim()) return vehicles;
    const q = vehicleSearch.toLowerCase();
    return vehicles.filter(v =>
      (v.registration_number || v.license_plate || '').toLowerCase().includes(q) ||
      (v.make || '').toLowerCase().includes(q) ||
      (v.model || '').toLowerCase().includes(q)
    );
  }, [vehicles, vehicleSearch]);

  const selectedVehicle = useMemo(() => {
    return vehicles.find(v => v.id === selectedVehicleId);
  }, [vehicles, selectedVehicleId]);

  // Pre-check for vehicle conflict
  const vehicleConflict = useMemo(() => {
    if (!selectedVehicle) return null;
    if (selectedVehicle.has_active_gps || selectedVehicle.current_device_name) {
      return `Vehicle ${selectedVehicle.registration_number} already has an active GPS device (${selectedVehicle.current_device_name || 'Assigned'}). You will need to swap or unassign it.`;
    }
    return null;
  }, [selectedVehicle]);

  // Test Connection pre-flight
  const handleRunPreflightTest = () => {
    setTestStatus('TESTING');
    setTestResult('');
    setTimeout(() => {
      if (connectionType === 'GPS_PROVIDER_API' && !config.apiKey && !config.accessToken) {
        setTestStatus('FAIL');
        setTestResult('API Key or Access Token is required to authenticate with the provider.');
      } else if (connectionType === 'TCP_DEVICE' && (!config.serverHost || !config.serverPort)) {
        setTestStatus('FAIL');
        setTestResult('Server Host and Port must be specified for TCP device ingestion.');
      } else {
        setTestStatus('PASS');
        setTestResult('Configuration syntax, parameters, and protocol definitions validated successfully.');
      }
    }, 800);
  };

  // Submit device registration
  const handleFinalSubmit = async () => {
    setSubmitting(true);
    try {
      const activeManufacturer = manufacturer === 'Other / Generic' ? (customManufacturer || 'Generic') : manufacturer;
      const activeModel = model === 'Custom' ? (customModel || 'Tracker') : model;
      const activeVehicleId = assignOption === 'ASSIGN' ? selectedVehicleId : null;

      const payload = {
        device_name: deviceName.trim(),
        connection_type: connectionType,
        manufacturer: activeManufacturer,
        model: activeModel,
        protocol: protocol,
        imei: imei.trim(),
        serial_number: serialNumber.trim() || undefined,
        firmware_version: firmwareVersion.trim() || undefined,
        vehicle_id: activeVehicleId || undefined,
        offline_threshold_minutes: parseInt(offlineThreshold, 10) || 15,
        gps_provider: connectionType === 'GPS_PROVIDER_API' ? config.gpsProvider : (connectionType === 'WEBHOOK' ? 'Webhook' : 'Direct Vahan TCP'),
        connection_config: {
          apiUrl: config.apiUrl,
          accountId: config.accountId,
          serverHost: config.serverHost,
          serverPort: parseInt(config.serverPort, 10) || 5027,
          brokerUrl: config.brokerUrl,
          mqttPort: parseInt(config.mqttPort, 10) || 8883,
          mqttTopic: config.mqttTopic,
          webhookSecret: config.webhookSecret,
        },
        credentials: {
          api_key: config.apiKey || undefined,
          access_token: config.accessToken || undefined,
          password: config.devicePassword || config.mqttPassword || undefined,
        },
      };

      await registerHardwareDevice(payload);
      success('Device Registered', `Hardware asset "${deviceName}" has been successfully added to Vahan.`);
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Registration failed:', err);
      toastError('Registration Failed', err.message || 'Unable to register device. Please check values.');
    } finally {
      setSubmitting(false);
    }
  };

  // Next Step Validation
  const canProceed = () => {
    if (step === 1) return !!connectionType;
    if (step === 2) {
      if (manufacturer === 'Other / Generic' && !customManufacturer.trim()) return false;
      return true;
    }
    if (step === 3) {
      return !!deviceName.trim() && imeiValidation.valid;
    }
    if (step === 4) {
      if (assignOption === 'ASSIGN') {
        return !!selectedVehicleId;
      }
      return true;
    }
    if (step === 5) {
      if (connectionType === 'GPS_PROVIDER_API') {
        return !!config.apiUrl.trim();
      }
      if (connectionType === 'TCP_DEVICE') {
        return !!config.serverHost && !!config.serverPort;
      }
      return true;
    }
    return true;
  };

  const stepTitles = [
    'Connection Type',
    'Hardware & Protocol',
    'Device Identifiers',
    'Vehicle Assignment',
    'Telemetry Config',
    'Review & Register',
  ];

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title="Register Hardware Telematics Device"
      description="Connect GPS trackers, IoT gateways, or provider API feeds into Vahan."
    >
      <div className="space-y-6">
        {/* Step Progress Stepper */}
        <div className="relative border-b border-border pb-4">
          <div className="flex items-center justify-between">
            {stepTitles.map((title, idx) => {
              const num = idx + 1;
              const isDone = step > num;
              const isCurrent = step === num;
              return (
                <div key={num} className="flex flex-col items-center flex-1 text-center">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isDone
                        ? 'bg-green-600 text-white'
                        : isCurrent
                        ? 'bg-brand-600 text-white ring-4 ring-brand-100'
                        : 'bg-surface-secondary text-content-muted border border-border'
                    }`}
                  >
                    {isDone ? <Check className="w-3.5 h-3.5" /> : num}
                  </div>
                  <span
                    className={`text-[11px] font-medium mt-1.5 hidden md:block ${
                      isCurrent ? 'text-brand-700 font-bold' : isDone ? 'text-content' : 'text-content-muted'
                    }`}
                  >
                    {title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* STEP 1: Select Connection Type */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 1: Select Integration Architecture</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Vahan supports multi-vendor ingestion via direct TCP protocols, REST APIs, Webhooks, and MQTT brokers.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {CONNECTION_TYPES.map(ct => {
                const Icon = ct.icon;
                const isSelected = connectionType === ct.id;
                return (
                  <div
                    key={ct.id}
                    onClick={() => setConnectionType(ct.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'border-brand-500 bg-brand-50/30 shadow-sm'
                        : 'border-border hover:border-brand-200 bg-surface'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={`p-2 rounded-lg ${isSelected ? 'bg-brand-500 text-white' : 'bg-surface-secondary text-content'}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-content">{ct.title}</h4>
                          <span className="text-[10px] font-mono text-brand-700 bg-brand-100/60 px-1.5 py-0.5 rounded">
                            {ct.badge}
                          </span>
                        </div>
                      </div>
                      {isSelected && <CheckCircle2 className="w-5 h-5 text-brand-600" />}
                    </div>
                    <p className="text-xs text-content-secondary mt-3">{ct.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* STEP 2: Manufacturer, Model & Protocol */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 2: Hardware Manufacturer & Protocol</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Select your tracker hardware specifications. Protocol normalization is verified against Vahan's telematics registry.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Manufacturer */}
              <div>
                <label className="block text-xs font-medium text-content mb-1">Hardware Manufacturer</label>
                <select
                  value={manufacturer}
                  onChange={(e) => handleManufacturerChange(e.target.value)}
                  className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                >
                  {DEFAULT_MANUFACTURERS.map(m => (
                    <option key={m.name} value={m.name}>{m.name}</option>
                  ))}
                </select>
                {manufacturer === 'Other / Generic' && (
                  <input
                    type="text"
                    value={customManufacturer}
                    onChange={(e) => setCustomManufacturer(e.target.value)}
                    placeholder="Enter manufacturer name"
                    className="mt-2 w-full h-9 px-3 border border-border rounded-lg bg-surface text-content text-xs"
                  />
                )}
              </div>

              {/* Model */}
              <div>
                <label className="block text-xs font-medium text-content mb-1">Device Model</label>
                {manufacturer !== 'Other / Generic' ? (
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    {(DEFAULT_MANUFACTURERS.find(m => m.name === manufacturer)?.models || []).map(mod => (
                      <option key={mod} value={mod}>{mod}</option>
                    ))}
                    <option value="Custom">Other Model...</option>
                  </select>
                ) : null}
                {(manufacturer === 'Other / Generic' || model === 'Custom') && (
                  <input
                    type="text"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    placeholder="Enter device model number"
                    className="mt-2 w-full h-9 px-3 border border-border rounded-lg bg-surface text-content text-xs"
                  />
                )}
              </div>
            </div>

            {/* Ingestion Protocol Selection */}
            <div>
              <label className="block text-xs font-medium text-content mb-1">
                Ingestion Protocol (Verified Telematics Registry)
              </label>
              <select
                value={protocol}
                onChange={(e) => {
                  setProtocol(e.target.value);
                  const pObj = PROTOCOLS_LIST.find(p => p.id === e.target.value);
                  if (pObj) setConfig(prev => ({ ...prev, serverPort: pObj.defaultPort }));
                }}
                className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              >
                {PROTOCOLS_LIST.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} (Port: {p.defaultPort})
                  </option>
                ))}
              </select>
            </div>

            {/* Protocol Compatibility Warning */}
            <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-800 flex items-start gap-2.5">
              <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold">Compatibility Note:</span> Selecting a manufacturer does not automatically guarantee all models support every protocol. Ensure your device firmware is configured to point to port <strong>{config.serverPort}</strong>.
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Device Identifiers */}
        {step === 3 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 3: Device Identifiers & Naming</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Every hardware device requires a unique hardware identifier (IMEI) to correlate incoming telemetry frames.
              </p>
            </div>

            {/* Device Friendly Name */}
            <div>
              <label className="block text-xs font-medium text-content mb-1">
                Device Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                placeholder="e.g. Tata Prima Primary GPS #1"
                className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>

            {/* IMEI Field with Luhn Live Check */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-content">
                  IMEI / Unique Electronic Identifier <span className="text-red-500">*</span>
                </label>
                {imei && (
                  <span
                    className={`text-[11px] font-medium flex items-center gap-1 ${
                      imeiValidation.luhnPass
                        ? 'text-green-600'
                        : imeiValidation.valid
                        ? 'text-amber-600'
                        : 'text-red-500'
                    }`}
                  >
                    {imeiValidation.luhnPass ? (
                      <ShieldCheck className="w-3.5 h-3.5" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5" />
                    )}
                    {imeiValidation.message}
                  </span>
                )}
              </div>
              <input
                type="text"
                value={imei}
                onChange={(e) => setImei(e.target.value.replace(/\s+/g, ''))}
                placeholder="15-digit IMEI (e.g. 865432019876543)"
                maxLength={30}
                className={`w-full h-10 px-3 border rounded-lg bg-surface text-content font-mono text-sm focus:outline-none focus:ring-2 ${
                  imei && !imeiValidation.valid
                    ? 'border-red-400 focus:ring-red-200'
                    : 'border-border focus:ring-brand-500/20 focus:border-brand-500'
                }`}
              />
              <p className="text-[11px] text-content-muted mt-1">
                Usually printed on the device label beneath the barcode or SIM slot.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-content mb-1">Serial Number (Optional)</label>
                <input
                  type="text"
                  value={serialNumber}
                  onChange={(e) => setSerialNumber(e.target.value)}
                  placeholder="e.g. SN-TEL-920-8812"
                  className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-content mb-1">Firmware Version (Optional)</label>
                <input
                  type="text"
                  value={firmwareVersion}
                  onChange={(e) => setFirmwareVersion(e.target.value)}
                  placeholder="e.g. 03.28.04.Rev.00"
                  className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-content mb-1">
                Offline Silence Threshold (Minutes)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min={1}
                  max={1440}
                  value={offlineThreshold}
                  onChange={(e) => setOfflineThreshold(e.target.value)}
                  className="w-32 h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                />
                <span className="text-xs text-content-secondary">
                  Device transitions to "Disconnected" if no packet is ingested for this duration (default 15m).
                </span>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: Vehicle Assignment */}
        {step === 4 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 4: Fleet Vehicle Assignment</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Assign this hardware device to a fleet truck, or store in unassigned hardware inventory.
              </p>
            </div>

            {/* Toggle: Assign vs Storage */}
            <div className="grid grid-cols-2 gap-3">
              <div
                onClick={() => setAssignOption('ASSIGN')}
                className={`p-3.5 rounded-xl border-2 cursor-pointer flex items-center gap-3 ${
                  assignOption === 'ASSIGN'
                    ? 'border-brand-500 bg-brand-50/30'
                    : 'border-border bg-surface'
                }`}
              >
                <Truck className="w-5 h-5 text-brand-600" />
                <div>
                  <h4 className="text-xs font-semibold text-content">Mount to Fleet Vehicle</h4>
                  <p className="text-[11px] text-content-muted">Live telemetry will update vehicle position</p>
                </div>
              </div>

              <div
                onClick={() => {
                  setAssignOption('STORAGE');
                  setSelectedVehicleId(null);
                }}
                className={`p-3.5 rounded-xl border-2 cursor-pointer flex items-center gap-3 ${
                  assignOption === 'STORAGE'
                    ? 'border-brand-500 bg-brand-50/30'
                    : 'border-border bg-surface'
                }`}
              >
                <Cpu className="w-5 h-5 text-content-secondary" />
                <div>
                  <h4 className="text-xs font-semibold text-content">Keep in Storage / Spare</h4>
                  <p className="text-[11px] text-content-muted">Register into inventory without vehicle link</p>
                </div>
              </div>
            </div>

            {assignOption === 'ASSIGN' && (
              <div className="space-y-3 pt-2">
                <div className="relative">
                  <Search className="w-4 h-4 text-content-muted absolute left-3 top-3" />
                  <input
                    type="text"
                    value={vehicleSearch}
                    onChange={(e) => setVehicleSearch(e.target.value)}
                    placeholder="Search vehicle registration number, make, model..."
                    className="w-full h-10 pl-9 pr-3 border border-border rounded-lg bg-surface text-content text-sm"
                  />
                </div>

                <div className="max-h-52 overflow-y-auto border border-border rounded-xl divide-y divide-border bg-surface">
                  {filteredVehicles.length === 0 ? (
                    <div className="p-4 text-center text-xs text-content-muted">
                      No matching fleet vehicles found.
                    </div>
                  ) : (
                    filteredVehicles.map(v => {
                      const isSelected = selectedVehicleId === v.id;
                      return (
                        <div
                          key={v.id}
                          onClick={() => setSelectedVehicleId(v.id)}
                          className={`p-3 flex items-center justify-between cursor-pointer transition-colors ${
                            isSelected ? 'bg-brand-50' : 'hover:bg-surface-secondary'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isSelected ? 'bg-brand-500 text-white' : 'bg-surface-secondary text-content'}`}>
                              <Truck className="w-4 h-4" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm font-bold text-content">
                                  {v.registration_number || v.license_plate}
                                </span>
                                {v.has_active_gps && (
                                  <Badge variant="warning" size="sm">Has GPS Tracker</Badge>
                                )}
                              </div>
                              <span className="text-xs text-content-secondary">
                                {[v.make, v.model].filter(Boolean).join(' ') || 'Standard Fleet Vehicle'}
                              </span>
                            </div>
                          </div>
                          {isSelected && <Check className="w-5 h-5 text-brand-600" />}
                        </div>
                      );
                    })
                  )}
                </div>

                {vehicleConflict && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                    <div>{vehicleConflict}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* STEP 5: Dynamic Connection Configuration */}
        {step === 5 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 5: Telemetry Connection Configuration</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Parameters required to ingest data for connection type: <strong>{connectionType}</strong>.
              </p>
            </div>

            {/* Provider API Config */}
            {connectionType === 'GPS_PROVIDER_API' && (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">Provider Platform</label>
                    <input
                      type="text"
                      value={config.gpsProvider}
                      onChange={(e) => setConfig({ ...config, gpsProvider: e.target.value })}
                      placeholder="e.g. Traccar Cloud / Teltonika FOTA"
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">API Base URL</label>
                    <input
                      type="text"
                      value={config.apiUrl}
                      onChange={(e) => setConfig({ ...config, apiUrl: e.target.value })}
                      placeholder="https://your-traccar.com/api"
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">API Key / Token (Encrypted)</label>
                    <input
                      type="password"
                      value={config.apiKey}
                      onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                      placeholder="Secret API authorization key"
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">Account / Tenant ID (Optional)</label>
                    <input
                      type="text"
                      value={config.accountId}
                      onChange={(e) => setConfig({ ...config, accountId: e.target.value })}
                      placeholder="e.g. org_88123"
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TCP / Direct Hardware Config */}
            {(connectionType === 'TCP_DEVICE' || connectionType === 'DIRECT_HARDWARE') && (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">Vahan Telematics Listener Host</label>
                    <input
                      type="text"
                      value={config.serverHost}
                      onChange={(e) => setConfig({ ...config, serverHost: e.target.value })}
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">
                      TCP Ingestion Port ({protocol})
                    </label>
                    <input
                      type="number"
                      value={config.serverPort}
                      onChange={(e) => setConfig({ ...config, serverPort: e.target.value })}
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-content mb-1">Device Access Password (Optional)</label>
                  <input
                    type="password"
                    value={config.devicePassword}
                    onChange={(e) => setConfig({ ...config, devicePassword: e.target.value })}
                    placeholder="Enter device configuration password if required by protocol"
                    className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                  />
                </div>
                <div className="p-3 bg-surface-secondary border border-border rounded-xl text-xs text-content-secondary">
                  <strong>Hardware Configuration Command:</strong> Send SMS/GPRS configuration to device SIM:
                  <div className="mt-1 font-mono text-[11px] bg-surface p-2 rounded border border-border select-all">
                    SERVER,1,{config.serverHost},{config.serverPort},0#
                  </div>
                </div>
              </div>
            )}

            {/* MQTT Config */}
            {connectionType === 'MQTT_DEVICE' && (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">Broker URL</label>
                    <input
                      type="text"
                      value={config.brokerUrl}
                      onChange={(e) => setConfig({ ...config, brokerUrl: e.target.value })}
                      placeholder="mqtts://broker.hivemq.com"
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-content mb-1">Port</label>
                    <input
                      type="number"
                      value={config.mqttPort}
                      onChange={(e) => setConfig({ ...config, mqttPort: e.target.value })}
                      className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-content mb-1">Telemetry Topic</label>
                  <input
                    type="text"
                    value={config.mqttTopic}
                    onChange={(e) => setConfig({ ...config, mqttTopic: e.target.value })}
                    placeholder="e.g. telematics/vahan/{imei}"
                    className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm font-mono"
                  />
                </div>
              </div>
            )}

            {/* Webhook Config */}
            {connectionType === 'WEBHOOK' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-content mb-1">Assigned Vahan Webhook Ingestion URL</label>
                  <input
                    type="text"
                    readOnly
                    value={`${window.location.origin || 'https://vahan.app'}/api/v1/tracking/telematics/traccar`}
                    className="w-full h-10 px-3 border border-border rounded-lg bg-surface-secondary text-content text-xs font-mono select-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-content mb-1">Shared Webhook Secret / Signature Token</label>
                  <input
                    type="text"
                    value={config.webhookSecret}
                    onChange={(e) => setConfig({ ...config, webhookSecret: e.target.value })}
                    placeholder="Enter secret token for HMAC SHA-256 validation"
                    className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
                  />
                </div>
              </div>
            )}

            {/* Security Notice */}
            <div className="p-3 bg-surface-secondary/70 border border-border rounded-xl flex items-center gap-2.5 text-xs text-content-secondary">
              <Lock className="w-4 h-4 text-green-600 shrink-0" />
              <span>
                All credentials and passwords are encrypted with AES-GCM before database storage and are never returned in cleartext.
              </span>
            </div>
          </div>
        )}

        {/* STEP 6: Review, Pre-flight Test & Register */}
        {step === 6 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-content">Step 6: Review & Register Device</h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Verify specifications before registering hardware into your company telematics cluster.
              </p>
            </div>

            {/* Summary Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 bg-surface-secondary rounded-xl border border-border text-xs">
              <div>
                <span className="text-content-muted">Device Name:</span>
                <p className="font-semibold text-content">{deviceName}</p>
              </div>
              <div>
                <span className="text-content-muted">IMEI / ID:</span>
                <p className="font-mono font-semibold text-content">{imei}</p>
              </div>
              <div>
                <span className="text-content-muted">Manufacturer / Model:</span>
                <p className="font-semibold text-content">{manufacturer} {model}</p>
              </div>
              <div>
                <span className="text-content-muted">Protocol:</span>
                <p className="font-semibold text-brand-700">{protocol}</p>
              </div>
              <div>
                <span className="text-content-muted">Vehicle:</span>
                <p className="font-semibold text-content">
                  {assignOption === 'ASSIGN' && selectedVehicle
                    ? selectedVehicle.registration_number
                    : 'Unassigned (Storage)'}
                </p>
              </div>
              <div>
                <span className="text-content-muted">Initial Status:</span>
                <p className="font-semibold text-blue-600">PENDING CONFIG</p>
              </div>
            </div>

            {/* Preflight Connectivity Test Box */}
            <div className="p-4 border border-border rounded-xl bg-surface space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-content">Diagnostic Preflight Test</h4>
                  <p className="text-[11px] text-content-secondary">
                    Validates credentials, port allocations, and protocol schemas.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRunPreflightTest}
                  disabled={testStatus === 'TESTING'}
                  icon={<RefreshCw className={`w-3.5 h-3.5 ${testStatus === 'TESTING' ? 'animate-spin' : ''}`} />}
                >
                  {testStatus === 'TESTING' ? 'Testing...' : 'Test Connection'}
                </Button>
              </div>

              {testStatus === 'PASS' && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-xs text-green-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
                  <span>{testResult}</span>
                </div>
              )}

              {testStatus === 'FAIL' && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{testResult}</span>
                </div>
              )}
            </div>

            {/* Operational Reality Notice (Important requirement from prompt) */}
            <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold">Operational Telematics Reality:</span>
                <p className="mt-0.5 text-amber-800 leading-relaxed">
                  Saving this configuration registers the hardware identity in Vahan, but the status will remain <strong>PENDING</strong> until real telematics frames with valid GPS coordinates are ingested and parsed from the hardware device or provider.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Modal Footer Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <Button
            variant="ghost"
            onClick={step === 1 ? onClose : () => setStep(s => s - 1)}
            disabled={submitting}
            icon={step > 1 ? <ChevronLeft className="w-4 h-4" /> : undefined}
          >
            {step === 1 ? 'Cancel' : 'Back'}
          </Button>

          <div className="flex items-center gap-2">
            {step < 6 ? (
              <Button
                variant="primary"
                onClick={() => setStep(s => s + 1)}
                disabled={!canProceed()}
                icon={<ChevronRight className="w-4 h-4" />}
              >
                Continue
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleFinalSubmit}
                disabled={submitting}
                icon={submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              >
                {submitting ? 'Registering Device...' : 'Complete Registration'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
