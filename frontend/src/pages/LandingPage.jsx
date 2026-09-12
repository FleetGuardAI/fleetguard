import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  X,
  ArrowRight,
  ShieldCheck,
  FileText,
  Users,
  Smartphone,
  Server,
  LayoutDashboard,
  CheckCircle,
  FileSignature,
  FileCheck2,
  ListTodo,
  Clock,
  ShieldAlert,
  UploadCloud
} from 'lucide-react';

export default function LandingPage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const sectionVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-[#00c853]/20 relative overflow-hidden">
      
      {/* Global Background ambient glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#00c853]/5 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-100/30 blur-[150px] rounded-full pointer-events-none -z-10" />
      
      {/* 1. NAVBAR (Floating Glass) */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 pt-4 px-4 md:px-8 pointer-events-none`}>
        <div className={`max-w-7xl mx-auto flex items-center justify-between rounded-2xl pointer-events-auto transition-all duration-300 ${scrolled ? 'bg-white/70 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.04)] border border-white/40 px-4 py-3' : 'bg-white/40 backdrop-blur-md shadow-sm border border-white/20 px-4 py-4'}`}>
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center shadow-[0_2px_10px_rgba(0,200,83,0.3)] group-hover:scale-105 transition-transform border border-white/20">
              <ShieldCheck className="w-5 h-5 text-white drop-shadow-sm" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">Fleet<span className="text-[#00c853]">Guard</span></span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <a href="#product" className="hover:text-slate-900 transition-colors">Product</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How It Works</a>
            <a href="#driver-app" className="hover:text-slate-900 transition-colors">Driver App</a>
            <a href="#dashboard" className="hover:text-slate-900 transition-colors">Fleet Dashboard</a>
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Link to="/login" className="text-sm font-bold text-slate-700 hover:text-[#00c853] px-4 py-2 transition-colors">
              Dashboard
            </Link>
            <Link to="/login" className="bg-slate-900/90 backdrop-blur-md hover:bg-slate-900 text-white text-sm font-bold px-5 py-2.5 rounded-xl transition-all shadow-[0_4px_12px_rgba(0,0,0,0.1)] border border-slate-700/50">
              Book a Demo
            </Link>
          </div>

          <button className="md:hidden p-2 text-slate-600 hover:bg-white/50 rounded-lg transition-colors" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="md:hidden bg-white/80 backdrop-blur-xl border border-white/50 shadow-xl rounded-2xl mx-auto mt-2 p-4 max-w-7xl pointer-events-auto"
            >
              <div className="flex flex-col gap-4 text-sm font-semibold text-slate-600">
                <a href="#product" className="px-2" onClick={() => setIsMobileMenuOpen(false)}>Product</a>
                <a href="#how-it-works" className="px-2" onClick={() => setIsMobileMenuOpen(false)}>How It Works</a>
                <a href="#driver-app" className="px-2" onClick={() => setIsMobileMenuOpen(false)}>Driver App</a>
                <a href="#dashboard" className="px-2" onClick={() => setIsMobileMenuOpen(false)}>Fleet Dashboard</a>
                <div className="h-px bg-slate-200/50 my-2" />
                <Link to="/login" className="px-2 text-slate-900 font-bold" onClick={() => setIsMobileMenuOpen(false)}>Dashboard Login</Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* 2. HERO (Primary Glass) */}
      <section className="pt-48 pb-24 px-6 relative">
        <div className="absolute top-0 inset-x-0 h-[800px] bg-gradient-to-b from-slate-100/50 via-slate-50/50 to-transparent -z-10 pointer-events-none" />
        
        <div className="max-w-7xl mx-auto text-center relative z-10">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight leading-[1.15] mb-6 drop-shadow-sm"
          >
            Manage Your Fleet.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00c853] to-[#009040]">Verify Every Driver.</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed font-medium"
          >
            FleetGuard connects drivers, verification workflows, and fleet teams in one platform — from onboarding and document submission to verification and approval.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/login" className="w-full sm:w-auto bg-gradient-to-b from-[#00c853] to-[#00b048] hover:to-[#00a040] text-white text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-[0_4px_20px_rgba(0,200,83,0.3)] hover:shadow-[0_6px_25px_rgba(0,200,83,0.4)] border border-[#00e05d]/30 flex items-center justify-center gap-2 relative overflow-hidden group">
              <div className="absolute inset-0 bg-white/20 translate-y-[-100%] group-hover:translate-y-[100%] transition-transform duration-500 blur-sm" />
              Book a Demo <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="w-full sm:w-auto bg-white/60 backdrop-blur-md hover:bg-white/80 text-slate-800 text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-[0_2px_15px_rgba(0,0,0,0.03)] border border-white/50">
              Open Dashboard
            </Link>
          </motion.div>

          {/* HERO VISUAL - Ecosystem (Layered Glass) */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.4 }}
            className="mt-24 relative max-w-4xl mx-auto"
          >
            <div className="relative p-2 rounded-[2rem] bg-white/30 backdrop-blur-xl border border-white/50 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-8 bg-white/40 rounded-3xl border border-white/60 shadow-inner relative overflow-hidden">
                
                <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-white/60 backdrop-blur-md rounded-2xl border border-white/80 shadow-[0_4px_16px_rgba(0,0,0,0.03)] relative group hover:-translate-y-1 transition-transform">
                  <div className="w-12 h-12 bg-blue-50/80 text-blue-600 rounded-xl flex items-center justify-center mb-4 border border-blue-100/50 shadow-sm">
                    <Smartphone className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-slate-900 mb-3 tracking-tight">Driver App</h3>
                  <div className="flex flex-col gap-2 w-full">
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">OTP</div>
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">Profile</div>
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">Documents</div>
                  </div>
                </div>

                {/* Connecting Lines */}
                <div className="hidden md:flex flex-col items-center justify-center relative w-12 h-px bg-[#00c853]/20">
                  <div className="absolute w-2 h-2 rounded-full bg-[#00c853] shadow-[0_0_8px_#00c853] animate-ping opacity-50" />
                </div>
                <div className="md:hidden w-px h-8 bg-[#00c853]/20 relative"></div>

                <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-[#00c853]/5 backdrop-blur-md rounded-2xl border border-[#00c853]/20 shadow-[0_4px_20px_rgba(0,200,83,0.05)] relative group hover:-translate-y-1 transition-transform">
                  <div className="w-12 h-12 bg-[#00c853]/10 text-[#00c853] rounded-xl flex items-center justify-center mb-4 border border-[#00c853]/20 shadow-sm">
                    <Server className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-slate-900 mb-3 tracking-tight text-center leading-tight">FleetGuard<br/>Platform</h3>
                  <div className="flex flex-col gap-2 w-full">
                    <div className="text-[11px] font-semibold text-[#00c853] bg-white/50 rounded-md py-1.5 px-3 border border-[#00c853]/10 text-center">Verification</div>
                    <div className="text-[11px] font-semibold text-[#00c853] bg-white/50 rounded-md py-1.5 px-3 border border-[#00c853]/10 text-center">Processing</div>
                    <div className="text-[11px] font-semibold text-[#00c853] bg-white/50 rounded-md py-1.5 px-3 border border-[#00c853]/10 text-center">Driver Records</div>
                  </div>
                </div>

                <div className="hidden md:flex flex-col items-center justify-center relative w-12 h-px bg-[#00c853]/20">
                  <div className="absolute w-2 h-2 rounded-full bg-[#00c853] shadow-[0_0_8px_#00c853] animate-ping opacity-50" style={{ animationDelay: '0.5s' }} />
                </div>
                <div className="md:hidden w-px h-8 bg-[#00c853]/20 relative"></div>

                <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-white/60 backdrop-blur-md rounded-2xl border border-white/80 shadow-[0_4px_16px_rgba(0,0,0,0.03)] group hover:-translate-y-1 transition-transform">
                  <div className="w-12 h-12 bg-purple-50/80 text-purple-600 rounded-xl flex items-center justify-center mb-4 border border-purple-100/50 shadow-sm">
                    <LayoutDashboard className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-slate-900 mb-3 tracking-tight text-center leading-tight">Fleet<br/>Dashboard</h3>
                  <div className="flex flex-col gap-2 w-full">
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">Drivers</div>
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">Documents</div>
                    <div className="text-[11px] font-semibold text-slate-600 bg-white/50 rounded-md py-1.5 px-3 border border-white/40 text-center">Approvals</div>
                  </div>
                </div>

              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 3. THE PROBLEM (Secondary Glass) */}
      <section className="py-24 relative px-6" id="problem">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto relative z-10"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">Fleet Operations Are Fragmented.</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto font-medium">Driver information, documents, verification, and approvals often live across disconnected workflows.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: "Manual Onboarding", desc: "Collecting and managing driver information manually creates unnecessary operational work.", icon: Users },
              { title: "Scattered Documents", desc: "Driver documents are difficult to track when submissions and records are spread across different workflows.", icon: FileText },
              { title: "Slow Verification", desc: "Fleet teams need a clear way to review driver information and document status before approval.", icon: Clock },
              { title: "Disconnected Ops", desc: "Drivers and fleet managers need one connected workflow instead of separate processes.", icon: ShieldAlert },
            ].map((item, i) => (
              <div key={i} className="p-6 rounded-2xl bg-white/40 backdrop-blur-lg border border-white/60 shadow-[0_4px_24px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_32px_rgba(0,200,83,0.05)] hover:-translate-y-1 hover:border-white/80 hover:bg-white/60 transition-all duration-300 group">
                <div className="w-12 h-12 rounded-full bg-white/50 border border-white/80 shadow-sm flex items-center justify-center mb-5 group-hover:bg-[#00c853]/5 group-hover:border-[#00c853]/20 transition-colors">
                  <item.icon className="w-6 h-6 text-slate-500 group-hover:text-[#00c853] transition-colors" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 4. HOW IT WORKS (Glass Timeline) */}
      <section className="py-24 px-6 relative" id="how-it-works">
        {/* Subtle separator */}
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent opacity-50" />
        
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto relative z-10"
        >
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">From Driver Onboarding to Fleet Approval</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto font-medium">A seamless workflow connecting drivers to fleet management.</p>
          </div>

          <div className="relative max-w-5xl mx-auto">
            {/* Glowing Glass Line (Desktop) */}
            <div className="hidden md:block absolute top-[40px] left-[15%] right-[15%] h-[2px] bg-gradient-to-r from-[#00c853]/10 via-[#00c853]/40 to-[#00c853]/10 -z-10 blur-[1px]" />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8">
              {[
                { num: "01", title: "Driver Onboards", desc: "Drivers authenticate, provide their information, and complete the onboarding process." },
                { num: "02", title: "Documents Processed", desc: "Drivers submit required documents through the App and FleetGuard processes the information." },
                { num: "03", title: "Manager Approves", desc: "Fleet teams review driver information, documents, and verification status via the dashboard." }
              ].map((step, i) => (
                <div key={i} className="relative flex flex-col items-center text-center">
                  <div className="w-20 h-20 rounded-full bg-white/70 backdrop-blur-md border-[3px] border-[#00c853]/20 shadow-[0_0_20px_rgba(0,200,83,0.1)] flex items-center justify-center text-xl font-black text-[#00c853] mb-6 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-white to-transparent opacity-50" />
                    <span className="relative z-10">{step.num}</span>
                  </div>
                  <div className="bg-white/40 backdrop-blur-md border border-white/60 p-5 rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
                    <h3 className="text-lg font-bold text-slate-900 mb-2">{step.title}</h3>
                    <p className="text-slate-600 text-sm leading-relaxed max-w-[250px] mx-auto font-medium">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* 5. PRODUCT ECOSYSTEM (Impressive Architecture Panel) */}
      <section className="py-32 px-6 relative overflow-hidden" id="product">
        <div className="absolute inset-0 bg-slate-900 -z-20" />
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-[#00c853]/10 blur-[120px] rounded-full mix-blend-screen -z-10" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-blue-500/10 blur-[100px] rounded-full mix-blend-screen -z-10" />

        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto relative z-10"
        >
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-4 tracking-tight drop-shadow-sm">One Connected Fleet Ecosystem</h2>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto font-medium">FleetGuard connects the driver side and fleet-management side through our backend platform.</p>
          </div>

          <div className="relative max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-4 relative perspective-1000">
              
              {/* Driver App Module */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] md:-rotate-y-12 md:translate-x-4 md:translate-z-[-20px] transform-gpu hover:rotate-0 hover:translate-x-0 transition-transform duration-500 relative z-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-400/20"><Smartphone className="w-5 h-5 text-blue-400" /></div>
                  <h3 className="text-xl font-bold text-white tracking-wide">DRIVER APP</h3>
                </div>
                <div className="space-y-3">
                  {['OTP Authentication', 'Driver Profile', 'Onboarding', 'Document Upload', 'Document Status'].map((item, i) => (
                    <div key={i} className="bg-black/20 border border-white/5 rounded-xl p-3 flex items-center gap-3 backdrop-blur-sm">
                      <div className="w-2 h-2 rounded-full bg-blue-400/50" />
                      <span className="text-sm font-medium text-slate-300">{item}</span>
                    </div>
                  ))}
                </div>
                <div className="absolute -top-3 -right-3 bg-white/10 backdrop-blur-md border border-white/20 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg">Authenticated</div>
              </div>

              {/* Platform API Module (Centerpiece) */}
              <div className="bg-[#00c853]/10 backdrop-blur-2xl border border-[#00c853]/30 p-8 rounded-3xl shadow-[0_8px_40px_rgba(0,200,83,0.15)] md:scale-105 transform-gpu hover:scale-110 transition-transform duration-500 relative z-20">
                <div className="absolute inset-0 rounded-3xl border-[2px] border-[#00c853]/10 pointer-events-none" />
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-[#00c853]/20 rounded-lg border border-[#00c853]/30"><Server className="w-5 h-5 text-[#00c853]" /></div>
                  <h3 className="text-xl font-bold text-white tracking-wide">PLATFORM API</h3>
                </div>
                <div className="space-y-3">
                  {['API Layer', 'Driver Records', 'Document Processing', 'Verification Workflow', 'Status Management'].map((item, i) => (
                    <div key={i} className="bg-black/20 border border-[#00c853]/20 rounded-xl p-3 flex items-center gap-3 backdrop-blur-sm">
                      <ShieldCheck className="w-4 h-4 text-[#00c853]" />
                      <span className="text-sm font-medium text-slate-200">{item}</span>
                    </div>
                  ))}
                </div>
                <div className="absolute -top-3 -right-3 bg-[#00c853]/20 backdrop-blur-md border border-[#00c853]/40 text-[#00c853] text-[10px] font-bold px-3 py-1 rounded-full shadow-lg">Verification</div>
              </div>

              {/* Dashboard Module */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] md:rotate-y-12 md:-translate-x-4 md:translate-z-[-20px] transform-gpu hover:rotate-0 hover:translate-x-0 transition-transform duration-500 relative z-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-purple-500/20 rounded-lg border border-purple-400/20"><LayoutDashboard className="w-5 h-5 text-purple-400" /></div>
                  <h3 className="text-xl font-bold text-white tracking-wide">DASHBOARD</h3>
                </div>
                <div className="space-y-3">
                  {['Driver Management', 'Driver Details', 'Documents', 'Verification Status', 'Approval Workflow'].map((item, i) => (
                    <div key={i} className="bg-black/20 border border-white/5 rounded-xl p-3 flex items-center gap-3 backdrop-blur-sm">
                      <div className="w-2 h-2 rounded-full bg-purple-400/50" />
                      <span className="text-sm font-medium text-slate-300">{item}</span>
                    </div>
                  ))}
                </div>
                <div className="absolute -top-3 -right-3 bg-white/10 backdrop-blur-md border border-white/20 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg">Ready for Review</div>
              </div>

            </div>
          </div>
        </motion.div>
      </section>

      {/* 6. DRIVER APP (Glass Mockup) */}
      <section className="py-32 bg-slate-50 px-6 relative" id="driver-app">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
            className="lg:w-1/2"
          >
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 mb-6 tracking-tight">Built for Drivers.</h2>
            <p className="text-lg text-slate-600 mb-10 font-medium leading-relaxed">Give drivers a straightforward way to onboard, manage their information, and submit required documents.</p>
            
            <div className="grid gap-6">
              {[
                { title: 'Secure OTP Login', desc: 'Fast, secure access using mobile number and one-time password.' },
                { title: 'Profile & Onboarding', desc: 'Easy capture of essential driver details during registration.' },
                { title: 'Document Upload', desc: 'Direct camera integration for clear document submission.' },
                { title: 'Status Tracking', desc: 'Real-time visibility into document verification status.' }
              ].map((f, i) => (
                <div key={i} className="flex gap-4 p-4 rounded-2xl bg-white/40 backdrop-blur-md border border-white/60 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                  <div className="mt-0.5 w-8 h-8 rounded-full bg-[#00c853]/10 flex items-center justify-center shrink-0 border border-[#00c853]/20">
                    <CheckCircle className="w-4 h-4 text-[#00c853]" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">{f.title}</h4>
                    <p className="text-sm text-slate-600 font-medium">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 50 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, margin: "-100px" }} transition={{ duration: 0.8 }}
            className="lg:w-1/2 relative flex justify-center"
          >
            {/* Ambient glow behind phone */}
            <div className="absolute inset-0 bg-[#00c853]/10 blur-[80px] rounded-full -z-10" />

            {/* Premium Glass Phone Mockup */}
            <div className="relative w-[300px] h-[620px] bg-slate-900 rounded-[44px] border-[10px] border-slate-800 shadow-2xl overflow-hidden flex flex-col ring-1 ring-white/10 ring-inset">
              
              {/* Screen Reflection overlay */}
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent pointer-events-none z-50" />

              {/* Status Bar */}
              <div className="h-7 w-full bg-slate-900 flex justify-between items-center px-6 pt-1 z-40 text-white/90">
                <span className="text-[11px] font-semibold tracking-wider">9:41</span>
                <div className="flex gap-1.5 opacity-80">
                   <div className="w-3.5 h-3 bg-white rounded-sm" />
                   <div className="w-3.5 h-3 bg-white rounded-sm" />
                </div>
              </div>
              
              {/* Phone Content (Glass UI) */}
              <div className="flex-1 bg-slate-50 flex flex-col relative">
                {/* Header Graphic */}
                <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-[#00c853]/20 to-transparent pointer-events-none" />

                <div className="p-5 pt-8 z-10">
                   <h3 className="font-extrabold text-2xl text-slate-900 mb-1">Hello, Driver</h3>
                   <div className="inline-block bg-white/60 backdrop-blur-md border border-white/80 rounded-full px-3 py-1 shadow-sm text-xs font-bold text-slate-700">Profile 80% Complete</div>
                </div>
                
                <div className="p-5 flex-1 z-10 flex flex-col gap-4">
                  {/* Glass Card 1 */}
                  <div className="bg-white/60 backdrop-blur-lg p-4 rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.03)] border border-white/80">
                     <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center justify-between">
                       Required Documents
                       <span className="text-[9px] bg-yellow-500/10 text-yellow-700 border border-yellow-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Action Needed</span>
                     </h4>
                     
                     <div className="space-y-3">
                       <div className="flex items-center justify-between bg-white/50 p-2.5 rounded-xl border border-white/60">
                         <div className="flex items-center gap-2.5">
                           <div className="p-1.5 bg-[#00c853]/10 rounded-lg"><FileCheck2 className="w-4 h-4 text-[#00c853]" /></div>
                           <span className="text-xs font-bold text-slate-800">Driving License</span>
                         </div>
                         <span className="text-[10px] text-[#00c853] font-bold bg-[#00c853]/10 px-2 py-0.5 rounded-full">Verified</span>
                       </div>
                       
                       <div className="flex items-center justify-between bg-white/50 p-2.5 rounded-xl border border-white/60">
                         <div className="flex items-center gap-2.5">
                           <div className="p-1.5 bg-slate-200/50 rounded-lg"><UploadCloud className="w-4 h-4 text-slate-500" /></div>
                           <span className="text-xs font-bold text-slate-800">Aadhar Card</span>
                         </div>
                         <button className="text-[10px] bg-slate-900 text-white px-3 py-1.5 rounded-lg font-bold shadow-md">Upload</button>
                       </div>
                     </div>
                  </div>
                  
                  {/* Glass Card 2 */}
                  <div className="bg-white/60 backdrop-blur-lg p-4 rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.03)] border border-white/80">
                    <h4 className="text-sm font-bold text-slate-900 mb-3">Verification Status</h4>
                    <div className="flex items-center gap-3 bg-white/50 p-3 rounded-xl border border-white/60">
                      <div className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] animate-pulse" />
                      <span className="text-xs font-bold text-slate-700">Pending Fleet Approval</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Home indicator */}
              <div className="h-1.5 w-1/3 bg-slate-800 mx-auto rounded-full mb-3 z-40" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* 7. FLEET DASHBOARD (Premium Glass Application) */}
      <section className="py-32 px-6 relative overflow-hidden" id="dashboard">
        <div className="absolute inset-0 bg-slate-100/50 -z-20" />
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[#00c853]/5 blur-[120px] rounded-full -z-10" />

        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 mb-4 tracking-tight">Designed for Fleet Teams.</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto font-medium">Manage drivers, review submitted information, and make approval decisions from one centralized dashboard.</p>
          </motion.div>

          {/* Glass Desktop Dashboard Mockup */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-100px" }} transition={{ duration: 0.8 }}
            className="w-full rounded-3xl border border-white shadow-[0_20px_60px_rgba(0,0,0,0.08)] bg-white/40 backdrop-blur-2xl overflow-hidden relative"
          >
            {/* Header / Chrome */}
            <div className="h-16 border-b border-white/50 flex items-center px-6 justify-between bg-white/60 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5 mr-4">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center shadow-sm">
                  <ShieldCheck className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold text-slate-800">FleetGuard Dashboard</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-64 h-9 bg-white/50 border border-white/80 rounded-xl shadow-inner" />
                <div className="w-9 h-9 rounded-full bg-slate-200 border-2 border-white shadow-sm" />
              </div>
            </div>
            
            <div className="flex h-[550px]">
              {/* Translucent Sidebar */}
              <div className="w-64 border-r border-white/50 p-4 space-y-2 hidden md:block bg-white/30">
                <div className="p-3 text-sm font-bold text-[#00c853] bg-white/60 border border-white/80 shadow-sm rounded-xl flex items-center gap-3">
                  <Users className="w-5 h-5" /> Drivers
                </div>
                <div className="p-3 text-sm font-semibold text-slate-600 hover:bg-white/40 rounded-xl flex items-center gap-3 transition-colors">
                  <FileSignature className="w-5 h-5" /> Approvals
                </div>
                <div className="p-3 text-sm font-semibold text-slate-600 hover:bg-white/40 rounded-xl flex items-center gap-3 transition-colors">
                  <FileText className="w-5 h-5" /> Documents
                </div>
              </div>
              
              {/* Inner Panels */}
              <div className="flex-1 p-8 bg-transparent overflow-hidden">
                <div className="flex justify-between items-center mb-8">
                   <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">Driver Management</h3>
                   <div className="px-4 py-2 bg-white/60 border border-white/80 rounded-lg text-sm font-bold text-slate-700 shadow-sm">Export List</div>
                </div>
                
                {/* Stats row */}
                <div className="grid grid-cols-3 gap-6 mb-8">
                  {['Total Drivers', 'Pending Review', 'Approved'].map((stat, i) => (
                    <div key={i} className="bg-white/60 backdrop-blur-md border border-white/80 p-5 rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
                      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">{stat}</div>
                      <div className="text-3xl font-black text-slate-900">{i === 0 ? '142' : i === 1 ? '12' : '130'}</div>
                    </div>
                  ))}
                </div>

                <div className="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl overflow-hidden shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-white/40 border-b border-white/60 text-slate-500">
                      <tr>
                        <th className="p-4 font-bold tracking-wide">Driver Name</th>
                        <th className="p-4 font-bold tracking-wide">Status</th>
                        <th className="p-4 font-bold tracking-wide">Documents</th>
                        <th className="p-4 font-bold tracking-wide">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/40">
                      {[
                        { name: 'Raj Kumar', status: 'Pending Review', docs: '2/2 Uploaded', color: 'bg-yellow-500/10 text-yellow-700 border-yellow-500/20' },
                        { name: 'Amit Singh', status: 'Approved', docs: 'Verified', color: 'bg-[#00c853]/10 text-[#00c853] border-[#00c853]/20' },
                        { name: 'Vikram Sharma', status: 'Missing Docs', docs: '1/2 Uploaded', color: 'bg-red-500/10 text-red-700 border-red-500/20' },
                        { name: 'Sanjay Verma', status: 'Approved', docs: 'Verified', color: 'bg-[#00c853]/10 text-[#00c853] border-[#00c853]/20' },
                      ].map((row, i) => (
                        <tr key={i} className="hover:bg-white/50 transition-colors">
                          <td className="p-4 font-bold text-slate-800">{row.name}</td>
                          <td className="p-4">
                            <span className={`px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider border ${row.color}`}>
                              {row.status}
                            </span>
                          </td>
                          <td className="p-4 text-slate-600 font-medium text-xs">{row.docs}</td>
                          <td className="p-4">
                            <button className="text-xs font-bold text-blue-600 hover:text-blue-800 bg-blue-50/50 px-3 py-1.5 rounded-lg border border-blue-100">Review</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 8. VERIFICATION WORKFLOW (Layered Pipeline) */}
      <section className="py-24 px-6 relative">
        <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-transparent via-[#00c853]/20 to-transparent -z-10" />
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto text-center"
        >
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-16 tracking-tight">From Document Submission to Verified Driver</h2>
          
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 max-w-5xl mx-auto relative">
            {/* Desktop connecting line */}
            <div className="hidden md:block absolute top-1/2 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-[#00c853]/10 via-[#00c853]/40 to-[#00c853]/10 -z-10" />

            {['Document Upload', 'Processing', 'Verification', 'Fleet Review', 'Approved'].map((step, i) => (
              <React.Fragment key={i}>
                <div className="bg-white/70 backdrop-blur-md border border-white shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_24px_rgba(0,200,83,0.08)] px-5 py-4 rounded-2xl font-bold text-slate-800 text-sm w-44 hover:-translate-y-1 transition-all duration-300 relative group cursor-default">
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/50 to-transparent pointer-events-none" />
                  {step}
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full bg-[#00c853] opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                {i < 4 && <ArrowRight className="w-5 h-5 text-slate-300 rotate-90 md:hidden my-2" />}
              </React.Fragment>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 9. FEATURES (Glass Cards) */}
      <section className="py-32 bg-slate-50/50 px-6 relative">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 mb-4 tracking-tight">Everything You Need</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto font-medium">Manage driver verification and fleet operations securely.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: 'Driver Onboarding', desc: 'Bring new drivers into a structured workflow effortlessly.' },
              { title: 'Secure Authentication', desc: 'Authenticate via secure login and OTP.' },
              { title: 'Document Upload', desc: 'Submit required documents through the App.' },
              { title: 'Document Processing', desc: 'Process documents through the backend pipeline.' },
              { title: 'Driver Verification', desc: 'Track verification status in real-time.' },
              { title: 'Approval Management', desc: 'Review information and take swift actions.' },
              { title: 'Fleet Dashboard', desc: 'Manage operations from a clear interface.' },
              { title: 'Driver Records', desc: 'View and manage comprehensive driver status.' }
            ].map((feature, i) => (
              <div key={i} className="bg-white/50 backdrop-blur-lg p-6 rounded-2xl border border-white/80 shadow-[0_4px_16px_rgba(0,0,0,0.02)] hover:shadow-[0_12px_32px_rgba(0,200,83,0.06)] hover:-translate-y-1 hover:bg-white/70 transition-all duration-300 group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent pointer-events-none" />
                <div className="absolute -inset-x-4 -top-4 h-16 bg-gradient-to-b from-[#00c853]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                
                <CheckCircle className="w-6 h-6 text-slate-400 group-hover:text-[#00c853] mb-4 transition-colors relative z-10" />
                <h3 className="font-bold text-slate-900 text-lg mb-2 tracking-tight relative z-10">{feature.title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed font-medium relative z-10">{feature.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 10. TRUST / SECURITY (Frosted Panel) */}
      <section className="py-32 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-slate-100/30 -z-20" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-100/40 blur-[100px] rounded-[100%] -z-10 pointer-events-none" />

        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-4xl mx-auto text-center bg-white/40 backdrop-blur-2xl border border-white/60 p-12 md:p-16 rounded-[40px] shadow-[0_8px_32px_rgba(0,0,0,0.03)] relative"
        >
          <div className="absolute inset-0 rounded-[40px] border-[2px] border-white/50 pointer-events-none" />
          <ShieldCheck className="w-14 h-14 text-[#00c853] mx-auto mb-6 drop-shadow-sm" />
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-6 tracking-tight">Controlled Workflows.<br/>Clear Visibility.</h2>
          <p className="text-slate-600 text-lg font-medium max-w-2xl mx-auto leading-relaxed">
            FleetGuard uses authenticated workflows and controlled dashboard access to keep driver and fleet operations organized and easily accessible to authorized personnel.
          </p>
        </motion.div>
      </section>

      {/* 11. FINAL CTA (Premium Glass Container) */}
      <section className="py-32 px-6 relative overflow-hidden">
        {/* Soft Ambient Glow Behind CTA */}
        <div className="absolute inset-0 flex items-center justify-center -z-10 pointer-events-none">
           <div className="w-[800px] h-[500px] bg-[#00c853]/15 blur-[120px] rounded-full" />
        </div>

        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-5xl mx-auto text-center bg-white/60 backdrop-blur-2xl border border-white shadow-[0_20px_60px_rgba(0,200,83,0.1)] p-16 md:p-24 rounded-[48px] relative"
        >
          <div className="absolute inset-0 rounded-[48px] bg-gradient-to-br from-white/40 to-transparent pointer-events-none" />
          
          <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 tracking-tight relative z-10 drop-shadow-sm">
            Bring Your Drivers and Fleet Operations Into One Platform
          </h2>
          <p className="text-lg md:text-xl font-medium text-slate-600 mb-12 max-w-2xl mx-auto relative z-10 leading-relaxed">
            See how FleetGuard connects driver onboarding, document verification, and fleet management.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-5 relative z-10">
            <Link to="/login" className="w-full sm:w-auto bg-gradient-to-b from-[#00c853] to-[#00b048] hover:to-[#00a040] text-white text-base font-bold px-10 py-4 rounded-2xl transition-all shadow-[0_8px_25px_rgba(0,200,83,0.3)] hover:shadow-[0_12px_30px_rgba(0,200,83,0.4)] border border-[#00e05d]/30 relative overflow-hidden group">
              <div className="absolute inset-0 bg-white/20 translate-y-[-100%] group-hover:translate-y-[100%] transition-transform duration-500 blur-sm" />
              Book a Demo
            </Link>
            <Link to="/login" className="w-full sm:w-auto bg-white/70 backdrop-blur-md hover:bg-white text-slate-900 text-base font-bold px-10 py-4 rounded-2xl transition-all shadow-[0_4px_16px_rgba(0,0,0,0.05)] border border-white">
              Open Dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      {/* 12. FOOTER */}
      <footer className="bg-slate-950 text-slate-400 py-20 px-6 relative z-10 border-t border-slate-900">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 border-b border-slate-800/50 pb-16 mb-8">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center border border-white/10 shadow-sm">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">Fleet<span className="text-[#00c853]">Guard</span></span>
            </div>
            <p className="text-sm font-medium leading-relaxed text-slate-500">
              The connected fleet management and driver verification ecosystem.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-6 tracking-wide text-sm">PRODUCT</h4>
            <ul className="space-y-3 text-sm font-medium">
              <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
              <li><a href="#driver-app" className="hover:text-white transition-colors">Driver App</a></li>
              <li><a href="#dashboard" className="hover:text-white transition-colors">Fleet Dashboard</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-6 tracking-wide text-sm">COMPANY</h4>
            <ul className="space-y-3 text-sm font-medium">
              <li><a href="#" className="hover:text-white transition-colors">About</a></li>
              <li><a href="mailto:contact@fleetguard.com" className="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-6 tracking-wide text-sm">ACCESS</h4>
            <ul className="space-y-3 text-sm font-medium">
              <li><Link to="/login" className="hover:text-white transition-colors">Dashboard Login</Link></li>
              <li><Link to="/downloads" className="hover:text-white transition-colors">Get Driver App</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-semibold text-slate-600">
          <p>© {new Date().getFullYear()} FleetGuard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
