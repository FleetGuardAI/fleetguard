import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Smartphone, Download, ShieldCheck, Zap } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

// Brand SVGs for Apple & Android
const AppleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 384 512" fill="currentColor">
    <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
  </svg>
);

const AndroidIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 576 512" fill="currentColor">
    <path d="M420.55,301.93a24,24,0,1,1,24-24,24,24,0,0,1-24,24m-265.1,0a24,24,0,1,1,24-24,24,24,0,0,1-24,24m273.7-144.48,47.94-83a10,10,0,1,0-17.27-10h0l-48.54,84.07a301.25,301.25,0,0,0-246.56,0L116.18,64.45a10,10,0,1,0-17.27,10h0l48,83.24C73.16,215.94,22.76,318.57,0,440.18H576c-22.76-121.61-73.16-224.24-146.85-282.73" />
  </svg>
);

export default function Downloads() {
  const [device, setDevice] = useState('desktop');

  useEffect(() => {
    const ua = navigator.userAgent;
    if (/android/i.test(ua)) {
      setDevice('android');
    } else if (/iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) {
      setDevice('ios');
    } else {
      setDevice('desktop');
    }
  }, []);

  useEffect(() => {
    document.title = 'FleetGuard Apps — Download';
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute('content', 'Download FleetGuard Owner and Driver apps for Android and iOS.');
    }
  }, []);

  const config = {
    driver: {
      androidUrl: import.meta.env.VITE_DRIVER_ANDROID_URL,
      iosUrl: import.meta.env.VITE_DRIVER_IOS_URL,
      androidVersion: import.meta.env.VITE_DRIVER_ANDROID_VERSION,
      iosVersion: import.meta.env.VITE_DRIVER_IOS_VERSION,
    },
    owner: {
      androidUrl: import.meta.env.VITE_OWNER_ANDROID_URL,
      iosUrl: import.meta.env.VITE_OWNER_IOS_URL,
      androidVersion: import.meta.env.VITE_OWNER_ANDROID_VERSION,
      iosVersion: import.meta.env.VITE_OWNER_IOS_VERSION,
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Navigation Header */}
      <header className="sticky top-0 z-20 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center px-4 md:px-8">
        <Link to="/" className="flex items-center gap-2 text-[#00c853] hover:text-[#00b848] transition-colors">
          <ArrowLeft className="h-5 w-5" />
          <span className="font-bold text-sm tracking-wide uppercase">Back to Home</span>
        </Link>
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-[#00c853]" />
          <span className="text-sm font-bold text-slate-800">Verified Secure</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12 md:py-20">
        
        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto mb-16 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-[#00c853] text-xs font-bold uppercase tracking-wider mb-6">
            <Zap className="h-3.5 w-3.5" /> FleetGuard Mobile
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 tracking-tight mb-4">
            FleetGuard Apps
          </h1>
          <p className="text-lg md:text-xl text-slate-500 font-medium">
            Run your fleet from anywhere. Download the FleetGuard app built for your role.
          </p>
        </div>

        {/* Application Cards */}
        <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
          <AppCard 
            title="FleetGuard Driver"
            role="For Drivers"
            description="Everything drivers need to manage trips, receive assignments, submit expenses, share PODs, and stay connected with fleet operations."
            theme="blue"
            device={device}
            config={config.driver}
          />
          
          <AppCard 
            title="FleetGuard Owner"
            role="For Fleet Managers & Owners"
            description="Manage your fleet, drivers, trips, payments, vehicles, and operations from anywhere."
            theme="green"
            device={device}
            config={config.owner}
          />
        </div>

      </main>

      {/* Footer minimal */}
      <footer className="border-t border-slate-200 bg-white py-8 text-center text-sm text-slate-500">
        <p>&copy; {new Date().getFullYear()} FleetGuard. All rights reserved.</p>
      </footer>
    </div>
  );
}

function AppCard({ title, role, description, theme, device, config }) {
  const isGreen = theme === 'green';
  const themeColor = isGreen ? '#00c853' : '#2563eb';
  const themeClass = isGreen ? 'text-[#00c853]' : 'text-blue-600';
  const bgClass = isGreen ? 'bg-green-500' : 'bg-blue-600';
  const hoverClass = isGreen ? 'hover:bg-[#00b848]' : 'hover:bg-blue-700';

  const androidPrimary = device === 'android';
  const iosPrimary = device === 'ios';

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 overflow-hidden flex flex-col transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
      <div className="p-8 flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-start gap-4 mb-6">
          <div className={`w-16 h-16 rounded-2xl ${bgClass} shadow-lg flex items-center justify-center shrink-0`}>
             {/* Abstract app icon placeholder - replace with actual if needed */}
             <Smartphone className="w-8 h-8 text-white" />
          </div>
          <div>
            <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${themeClass}`}>
              {role}
            </div>
            <h2 className="text-2xl font-black text-slate-900">{title}</h2>
          </div>
        </div>

        {/* Description */}
        <p className="text-slate-600 leading-relaxed mb-8 flex-1 font-medium">
          {description}
        </p>

        <div className="space-y-3 mb-8">
          <div className="flex items-center gap-2 text-sm text-slate-700 font-semibold">
            <CheckCircle2 className={`w-4 h-4 ${themeClass}`} /> Native performance
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-700 font-semibold">
            <CheckCircle2 className={`w-4 h-4 ${themeClass}`} /> Offline support
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-700 font-semibold">
            <CheckCircle2 className={`w-4 h-4 ${themeClass}`} /> Real-time sync
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-4 flex flex-col">
          {/* Android Button */}
          <DownloadButton 
            url={config.androidUrl} 
            version={config.androidVersion} 
            platform="Android" 
            primary={androidPrimary || device === 'desktop'}
            bgClass={bgClass}
            hoverClass={hoverClass}
          />

          {/* iOS Button */}
          <DownloadButton 
            url={config.iosUrl} 
            version={config.iosVersion} 
            platform="iOS" 
            primary={iosPrimary || device === 'desktop'}
            bgClass={bgClass}
            hoverClass={hoverClass}
          />
        </div>
      </div>

      {/* QR Codes Section (Desktop only) */}
      {device === 'desktop' && (config.androidUrl || config.iosUrl) && (
        <div className="bg-slate-50 border-t border-slate-200 p-6">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 text-center">Scan to download</h3>
          <div className="flex justify-center gap-8">
            {config.androidUrl && (
              <div className="flex flex-col items-center gap-2">
                <div className="p-2 bg-white rounded-xl border border-slate-200 shadow-sm">
                  <QRCodeSVG value={config.androidUrl} size={80} fgColor="#0f172a" />
                </div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-600">
                  <AndroidIcon className="w-3.5 h-3.5" /> Android
                </div>
              </div>
            )}
            {config.iosUrl && (
              <div className="flex flex-col items-center gap-2">
                <div className="p-2 bg-white rounded-xl border border-slate-200 shadow-sm">
                  <QRCodeSVG value={config.iosUrl} size={80} fgColor="#0f172a" />
                </div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-600">
                  <AppleIcon className="w-3.5 h-3.5" /> iOS
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DownloadButton({ url, version, platform, primary, bgClass, hoverClass }) {
  const isAndroid = platform === 'Android';
  const Icon = isAndroid ? AndroidIcon : AppleIcon;
  const label = isAndroid ? 'Download for Android' : 'Download on the App Store';
  
  if (!url) {
    return (
      <button disabled className="w-full py-3.5 px-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-400 font-bold text-sm flex items-center justify-center gap-2 cursor-not-allowed">
        <Icon className="w-5 h-5 opacity-50" />
        Coming soon
      </button>
    );
  }

  const baseClasses = "w-full py-3.5 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-3 transition-all duration-200 shadow-sm active:scale-[0.98]";
  
  const primaryClasses = `${bgClass} text-white ${hoverClass} shadow-md`;
  const secondaryClasses = "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300";

  return (
    <div className="flex flex-col items-center gap-1.5 w-full">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        className={`${baseClasses} ${primary ? primaryClasses : secondaryClasses}`}
      >
        <Icon className="w-5 h-5" />
        {label}
      </a>
      {version && (
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          v{version}
        </span>
      )}
    </div>
  );
}
