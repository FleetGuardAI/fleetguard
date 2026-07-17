import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ArrowRight,
  CheckCircle,
  MapPin,
  FileWarning,
  Fuel,
  Phone,
  Upload,
  Bot,
  BadgeCheck,
  Truck,
  Eye,
  BarChart3,
  MessageSquare,
  Mail,
  Instagram,
  LayoutDashboard,
  Sparkles,
  Cpu,
  Check,
  Lock,
  Coins,
  AlertTriangle,
  Zap,
  Sun,
  Moon,
  Trash2,
  X
} from 'lucide-react';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';


/**
 * 3D Mouse Tilt Card Wrapper
 */
function TiltCard({ children, className = "", ...props }) {
  const handleMouseMove = (e) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -8; // subtle tilt X
    const rotateY = ((x - centerX) / centerX) * 8;  // subtle tilt Y
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.015, 1.015, 1.015)`;
  };

  const handleMouseLeave = (e) => {
    const card = e.currentTarget;
    card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
  };

  return (
    <div
      className={`transition-all duration-300 ease-out preserve-3d ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ transformStyle: 'preserve-3d', transition: 'transform 0.15s ease-out' }}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * Interactive Network Node Canvas Background
 */
function InteractiveNetworkBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const particles = [];
    const particleCount = Math.min(65, Math.floor((width * height) / 28000));
    
    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.25;
        this.vy = (Math.random() - 0.5) * 0.25;
        this.radius = Math.random() * 2 + 1;
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > width) this.vx = -this.vx;
        if (this.y < 0 || this.y > height) this.vy = -this.vy;
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 200, 83, 0.4)';
        ctx.fill();
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }

    const mouse = { x: null, y: null, radius: 150 };

    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const handleMouseLeave = () => {
      mouse.x = null;
      mouse.y = null;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw subtle background grid lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.012)';
      ctx.lineWidth = 1;
      const gridSize = 45;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw & update particles
      particles.forEach((p) => {
        p.update();
        p.draw();
      });

      // Connect particles within proximity
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 110) {
            const alpha = (1 - dist / 110) * 0.12;
            ctx.strokeStyle = `rgba(0, 200, 83, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }

        // Connect particles to mouse cursor (gravitational node styling)
        if (mouse.x !== null && mouse.y !== null) {
          const dx = particles[i].x - mouse.x;
          const dy = particles[i].y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const alpha = (1 - dist / mouse.radius) * 0.2;
            ctx.strokeStyle = `rgba(0, 200, 83, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-0" />;
}

/**
 * Interactive AI Scan / Tracker widget
 */
function InteractiveScanner() {
  const [trackingCode, setTrackingCode] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [telemetryLogs, setTelemetryLogs] = useState([]);
  const [scanResult, setScanResult] = useState(null);
  
  const fileInputRef = useRef(null);

  // Setup preview URL for selected file
  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }
    if (selectedFile.type.startsWith('image/')) {
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [selectedFile]);

  // Global Ctrl + V paste listener for receipt image
  useEffect(() => {
    const handlePaste = (e) => {
      // Don't intercept text pastes in inputs unless they contain files
      if (document.activeElement?.tagName === 'INPUT' && document.activeElement?.type === 'text') {
        const items = e.clipboardData?.items;
        let hasImage = false;
        if (items) {
          for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
              hasImage = true;
              break;
            }
          }
        }
        if (!hasImage) return; // Proceed with text paste
      }

      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            if (file.size > 20 * 1024 * 1024) {
              alert('File size exceeds the 20MB limit.');
              return;
            }
            setSelectedFile(file);
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.size > 20 * 1024 * 1024) {
        alert("File size exceeds the 20MB limit.");
        return;
      }
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf'];
      if (!validTypes.includes(file.type)) {
        alert("Invalid file format. Please upload JPG, PNG, WEBP, or PDF.");
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 20 * 1024 * 1024) {
        alert("File size exceeds the 20MB limit.");
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const startScan = async (e) => {
    e.preventDefault();
    if (isScanning || !selectedFile || !trackingCode) return;

    setIsScanning(true);
    setScanResult(null);
    setTelemetryLogs([]);

    const formData = new FormData();
    formData.append('receipt_image', selectedFile);
    formData.append('claim_id', trackingCode);
    formData.append('driver_id', 'DRIVER-9921');
    formData.append('truck_id', 'RJ14-XX-1234');

    try {
      const response = await fetch('/api/v1/receipts/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          const lines = part.split('\n');
          for (const line of lines) {
            const cleanLine = line.trim();
            if (cleanLine.startsWith('data: ')) {
              const rawJson = cleanLine.substring(6).trim();
              try {
                const data = JSON.parse(rawJson);
                if (data.type === 'telemetry') {
                  setTelemetryLogs((prev) => [...prev, data.step]);
                } else if (data.type === 'result') {
                  setScanResult(data);
                } else if (data.type === 'error') {
                  setTelemetryLogs((prev) => [...prev, `❌ Error: ${data.detail}`]);
                }
              } catch (err) {
                console.warn('Error parsing JSON from SSE chunk:', err, rawJson);
              }
            }
          }
        }
      }
    } catch (error) {
      setTelemetryLogs((prev) => [...prev, `❌ Analysis failed: ${error.message}`]);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white dark:bg-slate-950/80 rounded-2xl p-6 relative overflow-hidden border border-slate-200 dark:border-slate-800/80 shadow-2xl shadow-[#00c853]/5 transition-colors duration-300">
        
        {/* Glow background filters */}
        <div className="absolute -top-12 -right-12 w-28 h-28 bg-[#00c853]/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -bottom-12 -left-12 w-28 h-28 bg-[#00c853]/5 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-[#00c853]/10 flex items-center justify-center border border-[#00c853]/20">
            <Cpu className="w-4 h-4 text-[#00c853]" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white tracking-wide transition-colors duration-300">
            Interactive AI Claim Scanner
          </h3>
        </div>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-5 leading-relaxed transition-colors duration-300">
          Test live verification capability. Watch FleetGuard parse receipts, query telematics, and audit risk instantly.
        </p>

        {/* Input Bar & Upload */}
        <form onSubmit={startScan} className="space-y-4 mb-5 text-left">
          <div>
            <label className="block text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Claim ID</label>
            <input
              type="text"
              value={trackingCode}
              onChange={(e) => setTrackingCode(e.target.value)}
              placeholder="Enter receipt code e.g. CLAIM-8831..."
              className="w-full bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-[#00c853] transition-all duration-300"
              disabled={isScanning}
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Receipt Upload</label>
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={handleUploadClick}
              className={`w-full border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 text-center relative overflow-hidden ${
                selectedFile 
                  ? "border-[#00c853]/50 bg-[#00c853]/5 dark:bg-[#00c853]/3" 
                  : isDragActive
                    ? "border-[#00c853] bg-[#00c853]/10 dark:bg-[#00c853]/5 shadow-lg shadow-[#00c853]/5"
                    : "border-slate-200 dark:border-slate-800/80 hover:border-[#00c853]/40 bg-slate-50 dark:bg-slate-950/30"
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/jpeg,image/jpg,image/png,image/webp,application/pdf"
                className="hidden"
                disabled={isScanning}
              />
              
              {!selectedFile ? (
                <div className="flex flex-col items-center gap-1.5 text-slate-500 dark:text-slate-400">
                  <Upload className="w-5 h-5 text-[#00c853]" />
                  <span className="text-[11px] font-bold">Drag & drop, paste, or click to upload</span>
                  <span className="text-[9px] opacity-60">JPG, PNG, WEBP, PDF (Max 20MB)</span>
                </div>
              ) : (
                <div className="w-full flex items-center justify-between gap-3 text-left" onClick={(e) => e.stopPropagation()}>
                  {/* Thumbnail Preview */}
                  <div className="flex items-center gap-3">
                    {previewUrl ? (
                      <img src={previewUrl} className="w-10 h-10 rounded-lg object-cover border border-slate-200 dark:border-slate-800" alt="receipt preview" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-[#00c853]/10 border border-[#00c853]/20 flex items-center justify-center">
                        <span className="text-[9px] font-black text-[#00c853]">PDF</span>
                      </div>
                    )}
                    <div className="overflow-hidden max-w-[120px] sm:max-w-[160px]">
                      <p className="text-[10px] font-bold text-slate-850 dark:text-slate-200 truncate">{selectedFile.name}</p>
                      <p className="text-[9px] text-slate-500 font-semibold">{formatSize(selectedFile.size)}</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={handleUploadClick}
                      className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 text-[10px] font-bold transition-colors active:scale-95"
                      disabled={isScanning}
                    >
                      Replace
                    </button>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-500 text-[10px] font-bold transition-colors active:scale-95"
                      disabled={isScanning}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isScanning || !trackingCode || !selectedFile}
            className="w-full bg-[#00c853] hover:bg-[#00b848] text-white text-xs font-bold py-3 rounded-xl transition-all duration-200 shadow-md shadow-green-500/20 active:scale-95 disabled:opacity-40 disabled:scale-100 disabled:shadow-none flex items-center justify-center gap-1.5"
          >
            {isScanning ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Auditing Receipt...
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                Audit
              </>
            )}
          </button>
        </form>

        {/* Simulated Document Scanning Window */}
        <div className="bg-slate-100 dark:bg-slate-950/95 rounded-xl border border-slate-200 dark:border-slate-900 aspect-[16/10] relative overflow-hidden flex flex-col justify-between p-4 font-mono text-[9px] text-slate-650 dark:text-slate-550 transition-colors duration-300">
          
          {/* Laser Scan line overlay */}
          {isScanning && <div className="scanner-line" />}

          {/* Top Panel */}
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-600 border-b border-slate-200 dark:border-slate-900/60 pb-2 transition-colors duration-300">
            <span>SECURE_PAY_TELEMETRY</span>
            <span className={isScanning ? 'text-green-650 dark:text-green-500 animate-pulse font-bold' : 'text-slate-450 dark:text-slate-700'}>
              ● {isScanning ? 'PROCESSING_PROOF' : 'STANDBY'}
            </span>
          </div>

          {/* Middle Section */}
          <div className="flex-1 py-3 flex flex-col gap-1.5 overflow-y-auto custom-scrollbar text-left scroll-smooth">
            {telemetryLogs.length === 0 && !scanResult && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 dark:text-slate-655 text-center gap-2 transition-colors duration-300">
                <Truck className="w-7 h-7 opacity-30 dark:opacity-20 text-slate-600 dark:text-slate-400" />
                <span className="max-w-[200px] leading-relaxed">Enter a mock ID above, upload a receipt, or click Audit to trigger the telemetry audit simulator.</span>
              </div>
            )}

            {telemetryLogs.map((log, index) => {
              const isSuccess = log.includes('✓') || log.includes('passed') || log.includes('success') || log.includes('validated') || log.includes('verified') || log.includes('complete') || log.includes('matches') || log.includes('identified');
              const isPending = log.includes('...') || log.includes('Running') || log.includes('Calculating') || log.includes('Generating') || log.includes('Initializing') || log.includes('Loading');
              const isError = log.includes('❌') || log.includes('Error') || log.includes('failed');

              return (
                <div key={index} className="flex items-center gap-1.5 animate-fade-in text-slate-800 dark:text-slate-300 transition-colors duration-300">
                  <span className={isSuccess ? "text-[#00c853]" : isPending ? "text-yellow-500" : isError ? "text-red-500" : "text-[#00c853]"}>
                    {isSuccess ? '✓' : isPending ? '⚡' : isError ? '❌' : '❯'}
                  </span>
                  <span>{log}</span>
                </div>
              );
            })}
          </div>

          {/* Bottom Panel */}
          <div className="flex justify-between text-[7px] text-slate-500 dark:text-slate-700 border-t border-slate-200 dark:border-slate-900/60 pt-1.5 transition-colors duration-300">
            <span>PIPELINE: ACTIVE_RUNNER_v2.0</span>
            <span>SHIELD: READY</span>
          </div>
        </div>

        {/* Final Analysis Result Card */}
        {scanResult && (
          <div className="mt-6 border border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/90 rounded-2xl p-5 shadow-xl animate-fade-in text-left transition-colors duration-300">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-200 dark:border-slate-900 pb-3">
              <Shield className="w-5 h-5 text-[#00c853]" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">AI Fraud Audit Result</h4>
            </div>

            {/* Fraud Risk Indicator */}
            <div className="grid grid-cols-12 gap-4 items-center mb-6 bg-white dark:bg-slate-900/30 p-4 rounded-xl border border-slate-200 dark:border-slate-900/80 transition-colors duration-300">
              
              <div className="col-span-4 flex flex-col items-center justify-center border-r border-slate-200 dark:border-slate-905 pr-4">
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-200 dark:text-slate-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={
                        scanResult.fraud_assessment.risk_score <= 30
                          ? "text-green-500"
                          : scanResult.fraud_assessment.risk_score <= 50
                            ? "text-yellow-500"
                            : scanResult.fraud_assessment.risk_score <= 80
                              ? "text-orange-500"
                              : "text-red-500"
                      }
                      strokeDasharray={`${scanResult.fraud_assessment.risk_score}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-xs font-black text-slate-900 dark:text-white">{scanResult.fraud_assessment.risk_score}%</span>
                    <span className="text-[6px] text-slate-500 uppercase tracking-wider font-bold">Risk</span>
                  </div>
                </div>
              </div>

              <div className="col-span-8 flex flex-col justify-center">
                <div className="flex flex-wrap items-center gap-1.5 mb-1">
                  <span className="text-[9px] font-extrabold uppercase tracking-wide text-slate-500">Risk Level:</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${
                    scanResult.fraud_assessment.risk_level === 'Low'
                      ? "bg-green-500/10 text-green-500 border-green-500/20"
                      : scanResult.fraud_assessment.risk_level === 'Medium'
                        ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                        : scanResult.fraud_assessment.risk_level === 'High'
                          ? "bg-orange-500/10 text-orange-500 border-orange-500/20"
                          : "bg-red-500/10 text-red-500 border-red-500/20"
                  }`}>
                    {scanResult.fraud_assessment.risk_level}
                  </span>
                </div>
                <div className="text-[9px] text-slate-600 dark:text-slate-400 space-y-0.5 font-semibold">
                  <p>Confidence: <strong className="text-slate-800 dark:text-slate-200">{scanResult.fraud_assessment.confidence}%</strong></p>
                  <p>Recommendation: <strong className={
                    scanResult.fraud_assessment.recommendation === 'Approve' ? 'text-[#00c853]' : 'text-red-500'
                  }>{scanResult.fraud_assessment.recommendation}</strong></p>
                </div>
              </div>
            </div>

            {/* Grid of details */}
            <div className="space-y-4 text-[10px]">
              
              {/* Receipt Summary */}
              <div className="border border-slate-200 dark:border-slate-900 rounded-xl p-3 bg-white dark:bg-slate-900/30 transition-colors duration-300">
                <h5 className="font-bold text-slate-800 dark:text-slate-300 border-b border-slate-200 dark:border-slate-900 pb-1 mb-2">Receipt Summary</h5>
                <div className="grid grid-cols-3 gap-y-1 text-slate-600 dark:text-slate-400 font-semibold">
                  <span>Merchant:</span><span className="col-span-2 text-slate-800 dark:text-slate-200 font-bold">{scanResult.receipt.merchant}</span>
                  <span>Category:</span><span className="col-span-2 text-slate-800 dark:text-slate-200">{scanResult.receipt.category}</span>
                  <span>Purpose:</span><span className="col-span-2 text-slate-800 dark:text-slate-200">{scanResult.receipt.purpose}</span>
                  <span>Amount:</span><span className="col-span-2 text-[#00c853] font-bold">₹{scanResult.receipt.amount}</span>
                  <span>GSTIN:</span><span className="col-span-2 font-mono text-slate-800 dark:text-slate-200">{scanResult.receipt.gst}</span>
                  <span>Invoice No:</span><span className="col-span-2 font-mono text-slate-800 dark:text-slate-200">{scanResult.receipt.invoice_number}</span>
                </div>
              </div>

              {/* Image & Business Analysis */}
              <div className="border border-slate-200 dark:border-slate-900 rounded-xl p-3 bg-white dark:bg-slate-900/30 transition-colors duration-300">
                <h5 className="font-bold text-slate-800 dark:text-slate-300 border-b border-slate-200 dark:border-slate-900 pb-1 mb-2">AI Analysis Checks</h5>
                <div className="space-y-1.5 text-slate-655 dark:text-slate-455 font-semibold">
                  <div className="flex justify-between items-center">
                    <span>Tampering / Manipulation:</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold border ${
                      scanResult.image_analysis.edited
                        ? "bg-red-500/10 text-red-500 border-red-500/20"
                        : "bg-green-500/10 text-green-500 border-green-500/20"
                    }`}>
                      {scanResult.image_analysis.edited ? "Possible manipulation detected" : "No manipulation detected"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Merchant Verification:</span>
                    <span className={scanResult.business_validation.merchant_verified ? "text-[#00c853]" : "text-red-500"}>
                      {scanResult.business_validation.merchant_verified ? "Verified ✓" : "Unverified ✗"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>GST Format & Status:</span>
                    <span className={scanResult.business_validation.gst_valid ? "text-[#00c853]" : "text-red-500"}>
                      {scanResult.business_validation.gst_valid ? "Valid ✓" : "Invalid ✗"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Price Deviation:</span>
                    <span className={`px-1 rounded text-[8px] font-bold ${
                      scanResult.price_analysis.status === 'Normal' ? 'text-[#00c853] bg-green-500/10' : 'text-red-500 bg-red-500/10'
                    }`}>
                      {scanResult.price_analysis.status} ({scanResult.price_analysis.deviation_percent}% deviation)
                    </span>
                  </div>
                </div>
              </div>

              {/* History Intelligence */}
              <div className="border border-slate-200 dark:border-slate-900 rounded-xl p-3 bg-white dark:bg-slate-900/30 transition-colors duration-300">
                <h5 className="font-bold text-slate-800 dark:text-slate-300 border-b border-slate-200 dark:border-slate-900 pb-1 mb-2">History & Duplicate Checks</h5>
                <div className="grid grid-cols-2 gap-y-1 text-slate-600 dark:text-slate-400 font-semibold">
                  <span>Truck Previous Repairs:</span><span className="text-slate-800 dark:text-slate-200 font-bold">{scanResult.truck_history.previous_repairs} repairs</span>
                  <span>Days Since Last Repair:</span><span className="text-slate-800 dark:text-slate-200">{scanResult.truck_history.last_repair_days} days ago</span>
                  <span>Driver Claims This Month:</span><span className="text-slate-800 dark:text-slate-200">{scanResult.driver_history.claims_this_month} claims</span>
                  <span>Duplicate Claims:</span><span className={scanResult.business_validation.duplicate ? "text-red-500 font-bold" : "text-[#00c853]"}>
                    {scanResult.business_validation.duplicate ? "Duplicate Found" : "No duplicates"}
                  </span>
                </div>
              </div>

              {/* Reasoning */}
              <div className="border border-slate-200 dark:border-slate-900 rounded-xl p-3 bg-white dark:bg-slate-900/30 transition-colors duration-300">
                <h5 className="font-bold text-slate-800 dark:text-slate-300 border-b border-slate-200 dark:border-slate-900 pb-1 mb-2">AI Reasonings</h5>
                <ul className="list-disc list-inside space-y-1 text-slate-650 dark:text-slate-400 text-[9px] font-semibold leading-relaxed">
                  {scanResult.reasoning.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>

            </div>
          </div>
        )}

      </div>
    </div>
  );
}

/**
 * 3D WhatsApp Live Simulator
 */
function WhatsAppSimulator({ t }) {
  const [messages, setMessages] = useState([]);
  const [typingState, setTypingState] = useState(null); // 'driver' | 'bot' | 'owner'
  const chatContainerRef = useRef(null);

  const conversation = [
    { sender: 'driver', type: 'text', text: t('chat.driverMsg'), time: '10:14 AM' },
    { sender: 'bot', type: 'text', text: t('chat.botMsg'), time: '10:14 AM', bullets: [t('chat.repairVideo'), t('chat.billPhoto'), t('chat.liveLocation'), t('chat.requestedAmount')] },
    { sender: 'driver', type: 'media', text: '📹 video_repair.mp4', time: '10:16 AM' },
    { sender: 'driver', type: 'receipt', text: `🧾 bill_photo.jpg\n📍 NH-48, Udaipur\n💰 ₹450`, time: '10:17 AM' },
    { sender: 'bot', type: 'verify', text: t('chat.verificationComplete'), time: '10:19 AM', details: { truck: 'RJ14 XX 1234', issue: 'Tyre Puncture', amount: '₹450', loc: 'Verified ✓', bill: 'Authentic ✓', fraud: 'Low' } },
    { sender: 'owner', type: 'alert', text: t('chat.ownerAlert'), time: '10:19 AM', details: { desc: t('chat.verifiedExpense'), detail: 'Truck RJ14 XX 1234\nIssue: Puncture — ₹450', checks: t('chat.allChecksPassed'), action: t('chat.viewProof') } }
  ];

  useEffect(() => {
    let index = 0;
    let isActive = true;
    setMessages([]);
    
    const playNext = () => {
      if (!isActive) return;
      if (index >= conversation.length) {
        // Wait and reset
        setTimeout(() => {
          if (!isActive) return;
          setMessages([]);
          index = 0;
          playNext();
        }, 5500);
        return;
      }

      const nextMsg = conversation[index];
      
      if (nextMsg.sender === 'driver') {
        setTypingState('driver');
      } else if (nextMsg.sender === 'bot') {
        setTypingState('bot');
      } else {
        setTypingState('owner');
      }

      setTimeout(() => {
        if (!isActive) return;
        setMessages((prev) => [...prev, nextMsg]);
        setTypingState(null);
        index++;
        
        setTimeout(playNext, 2200);
      }, 1500);
    };

    // Delay start slightly
    setTimeout(playNext, 800);

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, typingState]);

  return (
    <div className="w-full max-w-xs mx-auto">
      <div className="rounded-[40px] border-4 border-slate-800 bg-[#efeae2] relative shadow-2xl overflow-hidden aspect-[9/18] flex flex-col justify-between shadow-black/80">
        
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 bg-slate-800 h-5 w-28 rounded-b-xl z-20 flex items-center justify-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
          <div className="w-8 h-1 rounded-full bg-slate-700" />
        </div>

        {/* WhatsApp Header */}
        <div className="bg-[#005c4b] text-white pt-8 pb-3 px-4 flex items-center gap-3 shadow-md z-10">
          <div className="w-9 h-9 rounded-full bg-[#00c853] text-white flex items-center justify-center font-bold text-xs shadow-inner shadow-black/20 font-sans">
            FG
          </div>
          <div>
            <h4 className="font-bold text-[11px] tracking-wide font-sans">FleetGuard Bot</h4>
            <p className="text-[9px] text-emerald-300 font-medium font-sans">online</p>
          </div>
        </div>

        {/* Chat Area */}
        <div ref={chatContainerRef} className="flex-1 p-3.5 space-y-3 overflow-y-auto custom-scrollbar flex flex-col bg-[#efeae2] relative z-0">
          {messages.map((msg, i) => {
            if (msg.sender === 'driver') {
              return (
                <div key={i} className="flex justify-end animate-slide-up">
                  <div className="bg-[#d9fdd3] text-slate-800 p-2.5 rounded-xl rounded-tr-none max-w-[85%] shadow-sm border border-emerald-100/40">
                    <p className="text-[10px] leading-relaxed whitespace-pre-line font-medium font-sans">{msg.text}</p>
                    <span className="text-[7.5px] text-slate-400 block text-right mt-1 font-semibold font-sans">{msg.time}</span>
                  </div>
                </div>
              );
            }

            if (msg.sender === 'bot') {
              return (
                <div key={i} className="flex justify-start animate-slide-up">
                  <div className="bg-white text-slate-800 p-2.5 rounded-xl rounded-tl-none max-w-[85%] shadow-sm border border-slate-100">
                    <p className="text-[10px] leading-relaxed whitespace-pre-line font-medium font-sans">{msg.text}</p>
                    {msg.bullets && (
                      <ul className="mt-1 space-y-0.5 pl-1 text-slate-600 font-medium text-[9px] font-sans">
                        {msg.bullets.map((b, idx) => (
                          <li key={idx} className="flex items-center gap-1">
                            <span className="text-[#00c853]">●</span> {b}
                          </li>
                        ))}
                      </ul>
                    )}
                    {msg.details && (
                      <div className="mt-2 pt-1 border-t border-slate-100 text-[9px] text-slate-600 space-y-0.5 font-medium font-sans">
                        <p>🚛 Truck: <strong className="text-slate-800">{msg.details.truck}</strong></p>
                        <p>🔧 Issue: <strong className="text-slate-800">{msg.details.issue}</strong></p>
                        <p>💰 Amount: <strong className="text-slate-800">{msg.details.amount}</strong></p>
                        <p>📍 Location: <strong className="text-[#00c853]">{msg.details.loc}</strong></p>
                        <p>🧾 Bill: <strong className="text-[#00c853]">{msg.details.bill}</strong></p>
                        <p>⚠️ Risk: <strong className="text-[#00c853] font-bold">{msg.details.fraud}</strong></p>
                      </div>
                    )}
                    <span className="text-[7.5px] text-slate-400 block text-right mt-1 font-semibold font-sans">{msg.time}</span>
                  </div>
                </div>
              );
            }

            if (msg.sender === 'owner') {
              return (
                <div key={i} className="flex justify-start animate-slide-up">
                  <div className="bg-[#e1f5fe] border border-blue-200 text-slate-800 p-2.5 rounded-xl rounded-tl-none max-w-[85%] shadow-sm">
                    <div className="flex items-center gap-1 border-b border-blue-100 pb-1 mb-1 font-sans">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                      <span className="font-bold text-[9px] text-blue-800 uppercase tracking-wider">{msg.text}</span>
                    </div>
                    <p className="text-[9px] font-bold text-slate-700 font-sans">{msg.details.desc}</p>
                    <p className="text-[9px] text-slate-600 mt-1 font-mono bg-white/50 p-1.5 rounded border border-blue-100/50 whitespace-pre-line">{msg.details.detail}</p>
                    <div className="mt-1.5 flex items-center gap-1 text-[8.5px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full w-fit font-sans">
                      <Check className="w-2.5 h-2.5" />
                      {msg.details.checks}
                    </div>
                    <button className="mt-2 w-full py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-[8.5px] transition-colors shadow-sm font-sans">
                      {msg.details.action}
                    </button>
                    <span className="text-[7.5px] text-slate-400 block text-right mt-1 font-semibold font-sans">{msg.time}</span>
                  </div>
                </div>
              );
            }
            return null;
          })}

          {/* Typing Indicator */}
          {typingState && (
            <div className={`flex ${typingState === 'driver' ? 'justify-end' : 'justify-start'} animate-pulse`}>
              <div className={`p-2 px-2.5 rounded-full text-[9px] ${typingState === 'driver' ? 'bg-[#d9fdd3] rounded-tr-none text-emerald-800' : 'bg-white rounded-tl-none text-slate-500'} flex items-center gap-1`}>
                <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
        </div>

        {/* Home Button Indicator */}
        <div className="bg-slate-900 py-2.5 w-full flex justify-center items-center z-10">
          <div className="w-24 h-1 rounded-full bg-white/30" />
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const { t } = useLanguage();
  const [isDark, setIsDark] = useState(() => {
    const cached = localStorage.getItem('fleetguard_theme');
    return cached === 'dark' || !cached;
  });
  const [isScrolled, setIsScrolled] = useState(false);

  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem('fleetguard_theme', next ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', next);
  };

  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_theme');
    const defaultDark = cached === 'dark' || !cached;
    document.documentElement.classList.toggle('dark', defaultDark);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: t('nav.problem'), href: '#problem' },
    { label: t('nav.howItWorks'), href: '#how-it-works' },
    { label: t('nav.features'), href: '#features' },
    { label: t('nav.demo'), href: '#demo' },
    { label: t('nav.about'), href: '#about' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#070a13] font-sans text-slate-700 dark:text-slate-300 overflow-x-hidden relative selection:bg-[#00c853]/30 selection:text-white transition-colors duration-300">
      
      {/* Interactive nodes and lines backdrop */}
      <InteractiveNetworkBackground />

      {/* Radiant glow vectors behind page */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-[#00c853]/5 rounded-full blur-[140px] pointer-events-none z-0" />
      <div className="absolute top-1/3 right-10 w-[400px] h-[400px] bg-[#00c853]/3 rounded-full blur-[140px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 left-10 w-[450px] h-[450px] bg-[#00c853]/4 rounded-full blur-[140px] pointer-events-none z-0" />

      {/* ===== NAVBAR ===== */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-in-out ${
        isScrolled 
          ? "bg-white/70 dark:bg-[#070a13]/70 backdrop-blur-lg border-b border-slate-200/50 dark:border-slate-900/60 shadow-sm" 
          : "bg-transparent border-b border-transparent"
      }`} id="navbar">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 flex items-center justify-center group-hover:scale-105 transition-transform duration-200">
              <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              <span className="text-slate-900 dark:text-white transition-colors duration-300">Fleet </span>
              <span className="text-[#00c853]">Guard</span>
            </span>
          </Link>

          {/* Nav Items */}
          <div className={cn(
            "hidden md:flex items-center gap-1.5 border rounded-full px-2 py-1 transition-all duration-300 shadow-sm",
            isScrolled
              ? "bg-slate-100/85 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800/80 shadow-black/5"
              : "bg-white/10 dark:bg-white/5 border-white/15 dark:border-white/10 shadow-black/10"
          )}>
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={cn(
                  "text-[11px] font-bold px-3 py-1.5 rounded-full transition-all duration-200 relative group",
                  isScrolled
                    ? "text-slate-700 dark:text-slate-200 hover:text-[#00c853] dark:hover:text-[#00c853] hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
                    : "text-white/90 hover:text-white hover:bg-white/10"
                )}
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className={cn(
                "p-2 rounded-full border transition-all duration-300 active:scale-95 backdrop-blur-md shadow-sm",
                isScrolled
                  ? "bg-slate-100/80 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-white hover:bg-slate-200/50 dark:hover:bg-slate-800/50"
                  : "bg-white/10 dark:bg-white/5 border-white/15 dark:border-white/10 text-white hover:bg-white/15 dark:hover:bg-white/10"
              )}
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-indigo-500" />}
            </button>
            <LanguageSelector variant={isScrolled ? "glass-scrolled" : "glass-transparent"} />
            <Link
              to="/login"
              className={cn(
                "px-4 py-2 rounded-full border transition-all duration-300 hidden sm:inline-flex items-center gap-2 backdrop-blur-md shadow-sm text-xs font-bold",
                isScrolled
                  ? "bg-slate-100/80 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-white hover:bg-slate-200/50 dark:hover:bg-slate-800/50"
                  : "bg-white/10 dark:bg-white/5 border-white/15 dark:border-white/10 text-white hover:bg-white/15 dark:hover:bg-white/10"
              )}
              id="dashboard-login-btn"
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-[#00c853]" />
              {t('nav.dashboard')}
            </Link>
            <a
              href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
              className="px-4 py-2 rounded-full bg-[#00c853]/85 hover:bg-[#00b848]/95 border border-[#00c853]/20 hover:border-[#00c853]/40 text-white text-xs font-bold transition-all duration-200 hover:shadow-lg hover:shadow-green-500/20 backdrop-blur-md inline-flex items-center gap-1.5 active:scale-95"
              id="book-demo-btn"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {t('nav.bookDemo')}
            </a>
          </div>
        </div>
      </nav>

      <section className="relative min-h-[90vh] flex items-center overflow-hidden z-10 pt-32 pb-24" id="hero">
        
        {/* Full-Screen Background Image */}
        <div className="absolute inset-0 z-0 opacity-100 pointer-events-none">
          <picture>
            <source
              type="image/webp"
              srcSet="/assets/hero_bg_640.webp 640w,
                      /assets/hero_bg_1200.webp 1200w,
                      /assets/hero_bg_1920.webp 1920w,
                      /assets/hero_bg_3840.webp 3840w"
              sizes="100vw"
            />
            <source
              type="image/jpeg"
              srcSet="/assets/hero_bg_640.jpg 640w,
                      /assets/hero_bg_1200.jpg 1200w,
                      /assets/hero_bg_1920.jpg 1920w,
                      /assets/hero_bg_3840.jpg 3840w"
              sizes="100vw"
            />
            <img
              src="/assets/hero_bg_1920.jpg"
              alt="Hero background"
              className="w-full h-full object-cover object-center"
              style={{ imageRendering: 'auto' }}
              loading="eager"
              fetchpriority="high"
            />
          </picture>
          {/* Subtle overlay to guarantee high-contrast text readability */}
          <div className="absolute inset-0 bg-black/30 dark:bg-black/55 transition-colors duration-300" />
          {/* Top scrim overlay to make navbar options pop against sky */}
          <div className="absolute top-0 left-0 right-0 h-28 bg-gradient-to-b from-black/15 to-transparent dark:from-black/35 pointer-events-none" />
        </div>

        <div className="max-w-7xl mx-auto relative z-10 w-full px-6">
          {/* Left - Typography & Buttons */}
          <div className="max-w-2xl flex flex-col items-start text-left">
            {/* Main Header */}
            <h1 className="text-4xl lg:text-[54px] font-extrabold leading-[1.1] tracking-tight text-white mb-6">
              {t('hero.title1')}{' '}
              <span className="block text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text mt-1">
                {t('hero.title2')} {t('hero.title3')}
              </span>
              <span className="inline-block text-[#00c853] mt-2 relative italic font-black">
                {t('hero.title4')} {t('hero.title5')}
                <span className="absolute left-0 bottom-0.5 w-full h-[3px] bg-[#00c853]/40 blur-[1px] rounded" />
              </span>
            </h1>

            {/* Description */}
            <p className="text-sm md:text-base text-slate-200 leading-relaxed mb-8 max-w-xl">
              {t('hero.desc')}
            </p>

            {/* CTA Controls */}
            <div className="flex flex-wrap items-center gap-4 mb-12">
              <a
                href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl
                  bg-[#00c853] hover:bg-[#00b848] text-white font-bold text-sm
                  transition-all duration-200 hover:shadow-lg hover:shadow-green-500/25 active:scale-95"
                id="hero-cta"
              >
                <Sparkles className="w-4 h-4" />
                {t('nav.bookDemo')}
              </a>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl
                  bg-white/10 hover:bg-white/20 border border-white/20
                  text-white font-bold text-sm transition-all duration-200 active:scale-95 backdrop-blur-sm"
              >
                <LayoutDashboard className="w-4 h-4 text-[#00c853]" />
                {t('nav.dashboardLogin')}
              </Link>
            </div>

            {/* Stats list with glowing text */}
            <div className="grid grid-cols-3 gap-6 md:gap-10 border-t border-white/20 pt-8 w-full max-w-md">
              <div>
                <p className="text-2xl md:text-3xl font-black text-[#00c853] drop-shadow-[0_0_8px_rgba(0,200,83,0.3)]">40%</p>
                <p className="text-[10px] text-slate-300 font-bold uppercase tracking-wider mt-1">{t('hero.stat1Label')}</p>
              </div>
              <div>
                <p className="text-2xl md:text-3xl font-black text-[#00c853] drop-shadow-[0_0_8px_rgba(0,200,83,0.3)]">500+</p>
                <p className="text-[10px] text-slate-300 font-bold uppercase tracking-wider mt-1">{t('hero.stat2Label')}</p>
              </div>
              <div>
                <p className="text-2xl md:text-3xl font-black text-white">0</p>
                <p className="text-[10px] text-slate-300 font-bold uppercase tracking-wider mt-1">{t('hero.stat3Label')}</p>
              </div>
            </div>
          </div>
        </div>

      </section>

      {/* ===== INTEGRATIONS BAR ===== */}
      <section className="py-8 bg-slate-100/60 dark:bg-slate-950/40 border-y border-slate-200 dark:border-slate-900/80 relative z-10 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Compatible Fleet Telematics Systems</p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 opacity-40">
            {['Volvo', 'Scania', 'Tata Fleets', 'Daimler', 'BharatBenz'].map((logo, i) => (
              <span key={i} className="text-sm md:text-base font-black tracking-widest text-slate-850 dark:text-slate-300 font-mono select-none transition-colors duration-300">
                {logo.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ===== THE PROBLEM (Glassmorphism & Glow Accents) ===== */}
      <section className="py-24 px-6 relative z-10 transition-colors duration-300" id="problem">
        <div className="max-w-7xl mx-auto">
          
          <div className="mb-16 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00c853] uppercase tracking-widest">{t('problem.label')}</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight transition-colors duration-300">
              {t('problem.title1')}{' '}
              <span className="text-[#00c853] italic font-black">{t('problem.title2')}</span>
            </h2>
            <p className="text-sm md:text-base text-slate-650 dark:text-slate-400 mt-4 max-w-xl leading-relaxed transition-colors duration-300">
              {t('problem.desc')}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: FileWarning, title: t('problem.fake.title'), desc: t('problem.fake.desc'), color: 'text-red-500 dark:text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
              { icon: Fuel, title: t('problem.fuel.title'), desc: t('problem.fuel.desc'), color: 'text-rose-500 dark:text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20' },
              { icon: Eye, title: t('problem.proof.title'), desc: t('problem.proof.desc'), color: 'text-orange-500 dark:text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
              { icon: Phone, title: t('problem.pressure.title'), desc: t('problem.pressure.desc'), color: 'text-amber-500 dark:text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
            ].map((item, i) => (
              <TiltCard key={i} className="h-full">
                <div className="p-6 rounded-2xl bg-white dark:bg-slate-950/80 border border-slate-200 dark:border-slate-900 shadow-lg dark:shadow-2xl h-full flex flex-col justify-between group transition-colors duration-300">
                  <div>
                    <div className={`p-3 rounded-xl ${item.bg} border ${item.border} w-fit mb-5 group-hover:scale-110 transition-transform duration-200`}>
                      <item.icon className={`w-5 h-5 ${item.color}`} />
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3 tracking-wide transition-colors duration-300">{item.title}</h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed transition-colors duration-300">{item.desc}</p>
                  </div>
                </div>
              </TiltCard>
            ))}
          </div>

        </div>
      </section>

      {/* ===== HOW IT WORKS (Interactive Pipeline) ===== */}
      <section className="py-24 px-6 bg-slate-100/40 dark:bg-slate-950/30 border-y border-slate-200 dark:border-slate-900/80 relative z-10 transition-colors duration-300" id="how-it-works">
        <div className="max-w-5xl mx-auto text-center">
          
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-8 h-0.5 bg-[#00c853]" />
            <span className="text-xs font-bold text-[#00c853] uppercase tracking-widest">{t('how.label')}</span>
            <div className="w-8 h-0.5 bg-[#00c853]" />
          </div>
          
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white mb-4 transition-colors duration-300">
            {t('how.title1')} <span className="text-[#00c853] italic font-black">{t('how.title2')}</span>
          </h2>
          <p className="text-sm md:text-base text-slate-650 dark:text-slate-400 mb-16 max-w-xl mx-auto leading-relaxed transition-colors duration-300">
            {t('how.desc')}
          </p>

          {/* Pipeline milestones */}
          <div className="relative">
            
            {/* Glowing Connecting Pipeline Laser Line */}
            <div className="absolute top-10 left-[12%] right-[12%] h-[2px] bg-gradient-to-r from-green-500/20 via-[#00c853] to-green-500/20 hidden md:block laser-connection" />

            <div className="grid md:grid-cols-3 gap-12">
              {[
                { num: 1, title: t('how.step1.title'), desc: t('how.step1.desc'), glow: 'shadow-green-500/20', color: 'from-[#00e676] to-[#00c853]' },
                { num: 2, title: t('how.step2.title'), desc: t('how.step2.desc'), glow: 'shadow-green-500/30', color: 'from-[#00c853] to-[#00a844]' },
                { num: 3, title: t('how.step3.title'), desc: t('how.step3.desc'), glow: 'shadow-green-500/40', color: 'from-[#00a844] to-[#008837]' },
              ].map((step) => (
                <div key={step.num} className="flex flex-col items-center group font-sans">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${step.color}
                    flex items-center justify-center text-white text-base font-black mb-6
                    shadow-lg ${step.glow} relative z-10 group-hover:scale-110 transition-transform duration-200`}
                  >
                    0{step.num}
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2 tracking-wide group-hover:text-[#00c853] transition-colors duration-300">{step.title}</h3>
                  <p className="text-xs text-slate-650 dark:text-slate-400 leading-relaxed max-w-xs transition-colors duration-300">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Inline Live Scanner Simulator Widget inside pipeline context */}
          <div className="mt-20">
            <InteractiveScanner />
          </div>

        </div>
      </section>

      {/* ===== LIVE DEMO (WhatsApp Simulator + Visual Merge) ===== */}
      <section className="py-24 px-6 relative z-10 transition-colors duration-300" id="demo">
        <div className="max-w-6xl mx-auto grid md:grid-cols-12 gap-12 items-center">
          
          {/* Left - Narrative */}
          <div className="md:col-span-6 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00c853] uppercase tracking-widest">{t('demo.label')}</span>
            </div>
            
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white mb-4 leading-tight transition-colors duration-300">
              {t('demo.title1')}{' '}
              <span className="text-[#00c853] italic font-black">{t('demo.title2')}</span>
            </h2>
            <p className="text-sm md:text-base text-slate-650 dark:text-slate-400 mb-10 leading-relaxed transition-colors duration-300">
              {t('demo.desc')}
            </p>

            <div className="space-y-4 max-w-md mx-auto md:mx-0">
              {[
                { num: '01', title: t('demo.step1.title'), desc: t('demo.step1.desc') },
                { num: '02', title: t('demo.step2.title'), desc: t('demo.step2.desc') },
                { num: '03', title: t('demo.step3.title'), desc: t('demo.step3.desc') },
              ].map((w) => (
                <div key={w.num} className="flex gap-4 p-4 rounded-xl bg-white dark:bg-slate-950/50 border border-slate-200 dark:border-slate-900/60 items-start text-left hover:border-[#00c853]/35 transition-colors shadow-sm duration-300">
                  <div className="text-xs font-extrabold text-[#00c853] bg-[#00c853]/10 w-6 h-6 rounded flex items-center justify-center shrink-0 border border-[#00c853]/20">
                    {w.num}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white text-xs tracking-wide transition-colors duration-300">{w.title}</h3>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 leading-relaxed transition-colors duration-300">{w.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right - Live Self-typing Simulator (3D perspective tilt) */}
          <div className="md:col-span-6 flex justify-center relative">
            
            {/* Pulsing light rings behind simulated phone */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-[#00c853]/5 rounded-full blur-2xl pointer-events-none" />

            <TiltCard className="w-full max-w-xs">
              <WhatsAppSimulator t={t} />
            </TiltCard>
          </div>

        </div>
      </section>

      {/* ===== FEATURES GRID (Obsidian Glassmorphism SaaS Grid) ===== */}
      <section className="py-24 px-6 bg-slate-100/30 dark:bg-slate-950/30 border-t border-slate-200 dark:border-slate-900/80 relative z-10 transition-colors duration-300" id="features">
        <div className="max-w-7xl mx-auto">
          
          <div className="text-center mb-16">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00c853] uppercase tracking-widest">{t('features.label')}</span>
              <div className="w-8 h-0.5 bg-[#00c853]" />
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white transition-colors duration-300">
              {t('features.title1')} <span className="text-[#00c853] italic font-black">{t('features.title2')}</span>
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: MessageSquare, title: t('features.whatsapp.title'), desc: t('features.whatsapp.desc') },
              { icon: Eye, title: t('features.ocr.title'), desc: t('features.ocr.desc') },
              { icon: MapPin, title: t('features.location.title'), desc: t('features.location.desc') },
              { icon: BarChart3, title: t('features.dashboard.title'), desc: t('features.dashboard.desc') },
              { icon: Fuel, title: t('features.fuel.title'), desc: t('features.fuel.desc') },
              { icon: Shield, title: t('features.risk.title'), desc: t('features.risk.desc') },
            ].map((feat, i) => (
              <TiltCard key={i} className="h-full">
                <div className="p-6 rounded-2xl bg-white dark:bg-slate-950/80 border border-slate-200 dark:border-slate-900 shadow-lg dark:shadow-2xl h-full flex flex-col justify-between group transition-colors duration-300">
                  <div>
                    <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 w-fit mb-5 group-hover:bg-[#00c853]/25 transition-colors">
                      <feat.icon className="w-5 h-5 text-[#00c853]" />
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3 tracking-wide group-hover:text-[#00c853] transition-colors font-sans duration-300">{feat.title}</h3>
                    <p className="text-xs text-slate-650 dark:text-slate-400 leading-relaxed font-sans transition-colors duration-300">{feat.desc}</p>
                  </div>
                </div>
              </TiltCard>
            ))}
          </div>

        </div>
      </section>

      {/* ===== CALL TO ACTION (CTA Banner with Pulsing Backdrops) ===== */}
      <section className="py-24 px-6 relative z-10 transition-colors duration-300" id="cta">
        <div className="max-w-4xl mx-auto rounded-3xl border border-[#00c853]/20 bg-white dark:bg-slate-950/60 p-10 md:p-16 text-center relative overflow-hidden shadow-2xl shadow-green-500/5 transition-colors duration-300">
          
          {/* Radial green glow */}
          <div className="absolute -top-24 -left-24 w-48 h-48 bg-[#00c853]/10 rounded-full blur-[60px]" />
          <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-[#00c853]/10 rounded-full blur-[60px]" />

          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white mb-5 italic font-sans transition-colors duration-300">
            {t('cta.title1')} <span className="not-italic text-[#00c853] font-sans">{t('cta.title2')}</span>
          </h2>
          <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 mb-8 max-w-xl mx-auto leading-relaxed font-sans transition-colors duration-300">
            {t('cta.desc')}
          </p>
          
          <a
            href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl
              bg-[#00c853] hover:bg-[#00b848] text-white font-bold text-sm
              transition-all duration-200 hover:shadow-xl hover:shadow-green-500/30
              active:scale-95 font-sans"
            id="cta-btn"
          >
            <Sparkles className="w-5 h-5" />
            {t('nav.bookDemo')}
          </a>
        </div>
      </section>

      {/* ===== FOOTER (Clean Slate Dark) ===== */}
      <footer className="bg-slate-100 dark:bg-slate-950/90 text-slate-500 py-16 px-6 border-t border-slate-200 dark:border-slate-900/60 relative z-10 transition-colors duration-300" id="about">
        <div className="max-w-7xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 flex items-center justify-center">
                <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
              </div>
              <span className="text-lg font-bold tracking-tight">
                <span className="text-slate-900 dark:text-white font-sans transition-colors duration-300">Fleet </span>
                <span className="text-[#00e676] font-sans">Guard</span>
              </span>
            </div>
            <p className="text-xs leading-relaxed text-slate-650 dark:text-slate-400 max-w-xs font-sans transition-colors duration-300">
              {t('footer.tagline')}
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-widest mb-4 font-sans transition-colors duration-300">{t('footer.product')}</h4>
            <ul className="space-y-2.5 text-xs font-semibold font-sans">
              <li><a href="#features" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('nav.features')}</a></li>
              <li><a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('nav.howItWorks')}</a></li>
              <li><Link to="/dashboard" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('footer.liveDemo')}</Link></li>
              <li><a href="#demo" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('nav.bookDemo')}</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-widest mb-4 font-sans transition-colors duration-300">{t('footer.company')}</h4>
            <ul className="space-y-2.5 text-xs font-semibold font-sans">
              <li><a href="#about" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('nav.about')}</a></li>
              <li><a href="#" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('footer.testimonials')}</a></li>
              <li><a href="#" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('footer.careers')}</a></li>
              <li><a href="#" className="hover:text-slate-900 dark:hover:text-white transition-colors">{t('footer.blog')}</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-widest mb-4 font-sans transition-colors duration-300">{t('footer.contact')}</h4>
            <ul className="space-y-2.5 text-xs font-semibold font-sans">
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#00c853]" />
                <a href="mailto:fleetguardinfo@gmail.com" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  fleetguardinfo@gmail.com
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Instagram className="w-4 h-4 text-[#00c853]" />
                <a href="#" className="hover:text-slate-900 dark:hover:text-white transition-colors">Instagram</a>
              </li>
            </ul>
          </div>

        </div>

        <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-slate-200 dark:border-slate-900 flex items-center justify-between transition-colors duration-300">
          <p className="text-[10px] font-semibold text-slate-500 dark:text-slate-600 font-sans transition-colors duration-300">{t('footer.copyright')}</p>
          <div className="flex items-center gap-4 text-slate-450 dark:text-slate-700 transition-colors duration-300">
            <Truck className="w-4 h-4" />
            <BarChart3 className="w-4 h-4" />
          </div>
        </div>
      </footer>

    </div>
  );
}
