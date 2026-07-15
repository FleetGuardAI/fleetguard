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
  ClipboardList,
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
  Moon
} from 'lucide-react';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { useLanguage } from '@/i18n/LanguageContext';

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
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [scanResult, setScanResult] = useState(null);

  const startScan = (e) => {
    e.preventDefault();
    if (isScanning) return;
    setIsScanning(true);
    setScanResult(null);
    setScanStep(1);

    setTimeout(() => {
      setScanStep(2);
    }, 900);

    setTimeout(() => {
      setScanStep(3);
    }, 1800);

    setTimeout(() => {
      setIsScanning(false);
      setScanStep(4);
      setScanResult({
        status: 'VERIFIED & APPROVED',
        vendor: 'National Highway Tyres, Udaipur',
        amount: '₹450',
        telematics: 'RJ14 XX 1234 — GPS matched NH-48 (0.2km radius)',
        ocr: 'Receipt #NHT-8831 OCR Valid — Puncture repairs matching standard rate list.',
        risk: 'Low (1.8% Risk Index)',
      });
    }, 2800);
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

        {/* Input Bar */}
        <form onSubmit={startScan} className="flex gap-2 mb-5">
          <input
            type="text"
            value={trackingCode}
            onChange={(e) => setTrackingCode(e.target.value)}
            placeholder="Enter receipt code e.g. CLAIM-8831..."
            className="flex-1 bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-605 focus:outline-none focus:border-[#00c853] transition-all duration-300"
            disabled={isScanning}
          />
          <button
            type="submit"
            disabled={isScanning}
            className="bg-[#00c853] hover:bg-[#00b848] text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all duration-200 shadow-md shadow-green-500/20 active:scale-95 disabled:opacity-50 disabled:scale-100 flex items-center gap-1.5"
          >
            {isScanning ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Scanning
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
        <div className="bg-slate-100 dark:bg-slate-950/95 rounded-xl border border-slate-200 dark:border-slate-900 aspect-[16/10] relative overflow-hidden flex flex-col justify-between p-4 font-mono text-[9px] text-slate-600 dark:text-slate-500 transition-colors duration-300">
          
          {/* Laser Scan line overlay */}
          {isScanning && <div className="scanner-line" />}

          {/* Top Panel */}
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-600 border-b border-slate-200 dark:border-slate-900/60 pb-2 transition-colors duration-300">
            <span>SECURE_PAY_TELEMETRY</span>
            <span className={isScanning ? 'text-green-650 dark:text-green-500 animate-pulse font-bold' : 'text-slate-400 dark:text-slate-700'}>
              ● {isScanning ? 'SCANNING_PROOF' : 'STANDBY'}
            </span>
          </div>

          {/* Middle Section */}
          <div className="flex-1 py-3 flex flex-col gap-1.5 overflow-hidden">
            {!isScanning && !scanResult && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 dark:text-slate-600 text-center gap-2 transition-colors duration-300">
                <Truck className="w-7 h-7 opacity-30 dark:opacity-20 text-slate-650 dark:text-slate-405" />
                <span className="max-w-[200px] leading-relaxed">Enter a mock ID above or click Audit to trigger the telemetry audit simulator.</span>
              </div>
            )}

            {isScanning && (
              <div className="space-y-1.5 text-left">
                <div className="text-slate-650 dark:text-slate-400 flex items-center gap-1.5 transition-colors duration-300">
                  <span className="text-[#00c853] animate-pulse">❯</span> OCR: LOADING IMAGE ATTACHMENT...
                </div>
                {scanStep >= 1 && (
                  <div className="text-slate-800 dark:text-slate-300 flex items-center gap-1.5 animate-fade-in transition-colors duration-300">
                    <span className="text-[#00c853]">✓</span> OCR EXTRACTED: Udaipur Spares, Puncture Repair ₹450
                  </div>
                )}
                {scanStep >= 2 && (
                  <div className="text-slate-800 dark:text-slate-300 flex items-center gap-1.5 animate-fade-in transition-colors duration-300">
                    <span className="text-[#00c853]">✓</span> GPS: Telematics match Udaipur NH-48 coordinates
                  </div>
                )}
                {scanStep >= 3 && (
                  <div className="text-yellow-605 dark:text-yellow-400 flex items-center gap-1.5 animate-fade-in transition-colors duration-300">
                    <span className="text-yellow-600 dark:text-yellow-500">⚡</span> AUDITING: Cross-checking invoice metadata...
                  </div>
                )}
              </div>
            )}

            {scanResult && (
              <div className="space-y-1.5 animate-fade-in text-left">
                <div className="flex justify-between border-b border-slate-205 dark:border-slate-900 pb-1 transition-colors duration-300">
                  <span className="text-slate-800 dark:text-slate-300 font-bold text-[#00c853]">{scanResult.status}</span>
                  <span className="text-slate-500 dark:text-slate-600">AUDIT OK</span>
                </div>
                <div className="space-y-1 text-slate-600 dark:text-slate-400 transition-colors duration-300">
                  <div>
                    <span className="text-slate-500 dark:text-slate-600 font-bold uppercase mr-1">[Vendor]:</span>
                    <span className="text-slate-800 dark:text-slate-200">{scanResult.vendor}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-600 font-bold uppercase mr-1">[Amount]:</span>
                    <span className="text-[#00c853] font-bold">{scanResult.amount}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-600 font-bold uppercase mr-1">[GPS Coordinates]:</span>
                    <span className="text-slate-800 dark:text-slate-200">{scanResult.telematics}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-600 font-bold uppercase mr-1">[OCR Validation]:</span>
                    <span className="text-slate-800 dark:text-slate-200 block truncate">{scanResult.ocr}</span>
                  </div>
                </div>
                <div className="pt-1 border-t border-slate-200 dark:border-slate-900 flex justify-between items-center text-[8px] transition-colors duration-300">
                  <span>RISK EVALUATION:</span>
                  <span className="px-1.5 py-0.5 rounded bg-green-500/10 text-[#00c853] font-bold border border-green-500/20">{scanResult.risk}</span>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Panel */}
          <div className="flex justify-between text-[7px] text-slate-500 dark:text-slate-700 border-t border-slate-200 dark:border-slate-900/60 pt-1.5 transition-colors duration-300">
            <span>PIPELINE: ACTIVE_RUNNER_v2.0</span>
            <span>SHIELD: READY</span>
          </div>

        </div>
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
          ? "bg-white/80 dark:bg-[#070a13]/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-900/80 shadow-sm" 
          : "bg-transparent border-b border-transparent"
      }`} id="navbar">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00e676] to-[#00c853] flex items-center justify-center shadow-lg shadow-green-500/20 group-hover:scale-105 transition-transform duration-200">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              <span className="text-slate-900 dark:text-white transition-colors duration-300">Fleet </span>
              <span className="text-[#00c853]">Guard</span>
            </span>
          </Link>

          {/* Nav Items */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-xs font-bold text-slate-900 dark:text-slate-100 hover:text-[#00c853] dark:hover:text-[#00c853] transition-colors relative group py-1"
              >
                {item.label}
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-[#00c853] transition-all duration-300 group-hover:w-full" />
              </a>
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-white/70 hover:bg-white/90 dark:bg-slate-900/80 dark:hover:bg-slate-800 border border-slate-300/80 dark:border-slate-800 text-slate-900 dark:text-white transition-all duration-200 active:scale-95 backdrop-blur-sm"
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-indigo-500" />}
            </button>
            <LanguageSelector variant={isDark ? "light" : "dark"} />
            <Link
              to="/login"
              className="px-4 py-2 rounded-xl bg-white/75 hover:bg-white/95 dark:bg-slate-950/40 dark:hover:bg-slate-950/80 border border-slate-300/80 dark:border-slate-800/80 text-slate-900 dark:text-white text-xs font-bold transition-all duration-200 hidden sm:inline-flex items-center gap-2 backdrop-blur-sm"
              id="dashboard-login-btn"
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-[#00c853]" />
              {t('nav.dashboard')}
            </Link>
            <a
              href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
              className="px-4 py-2 rounded-xl bg-[#00c853] hover:bg-[#00b848]
                text-white text-xs font-bold
                transition-all duration-200 hover:shadow-lg hover:shadow-green-500/20
                inline-flex items-center gap-1.5 active:scale-95"
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
          <img
            src="/assets/full_page_truck.png"
            alt="Hero background"
            className="w-full h-full object-cover object-center"
          />
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

          {/* Extra centering Card */}
          <div className="mt-8 flex justify-center">
            <TiltCard className="w-full max-w-md">
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-950/80 border border-slate-200 dark:border-slate-900 shadow-lg dark:shadow-2xl flex items-start gap-4 transition-colors duration-300">
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 w-fit shrink-0">
                  <ClipboardList className="w-5 h-5 text-blue-500 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2 tracking-wide transition-colors duration-300">{t('problem.tracking.title')}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed transition-colors duration-300">{t('problem.tracking.desc')}</p>
                </div>
              </div>
            </TiltCard>
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
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00e676] to-[#00c853] flex items-center justify-center shadow-lg shadow-green-500/10">
                <Shield className="w-5 h-5 text-white" />
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
