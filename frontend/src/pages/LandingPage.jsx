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
  Clock,
  ShieldAlert,
  UploadCloud,
  ChevronRight,
  ArrowDown
} from 'lucide-react';
import DemoDashboard from '@/components/home/DemoDashboard';

export default function LandingPage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const sectionVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
  };

  return (
    <div className="min-h-screen bg-[#f5f8f8] text-slate-900 font-sans selection:bg-[#00c853]/20 relative overflow-x-hidden">
      
      {/* 1. NAVBAR (Floating Glass) */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 pt-4 px-4 md:px-8 pointer-events-none`}>
        <div className={`max-w-7xl mx-auto flex items-center justify-between rounded-2xl pointer-events-auto transition-all duration-300 ${scrolled ? 'bg-white/80 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.06)] border border-white/60 px-4 py-3' : 'bg-white/50 backdrop-blur-md shadow-sm border border-white/30 px-4 py-4'}`}>
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform border border-white/20">
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
            <Link to="/login" className="bg-slate-900/90 backdrop-blur-md hover:bg-slate-900 text-white text-sm font-bold px-5 py-2.5 rounded-xl transition-all shadow-md border border-slate-700/50">
              Book a Demo
            </Link>
          </div>

          <button className="md:hidden p-2 text-slate-600 hover:bg-white/50 rounded-lg transition-colors pointer-events-auto" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="md:hidden bg-white/90 backdrop-blur-xl border border-white/60 shadow-xl rounded-2xl mx-auto mt-2 p-4 max-w-7xl pointer-events-auto"
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

      {/* 2. HERO (Primary Glass, 2-Column) */}
      <section className="pt-32 pb-16 px-6 relative overflow-hidden">
        {/* Ambient Hero Glow */}
        <div className="absolute top-0 right-0 w-[60%] h-[800px] bg-gradient-to-bl from-[#00c853]/10 via-[#00c853]/5 to-transparent blur-[80px] -z-10 rounded-full" />
        
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 relative z-10 mt-8 md:mt-16">
          
          {/* Left: Text */}
          <motion.div 
            initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7 }}
            className="w-full lg:w-5/12 text-center lg:text-left pt-10"
          >
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.1] mb-6 drop-shadow-sm">
              Manage Your Fleet.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00c853] to-[#009040]">Verify Every Driver.</span>
            </h1>
            
            <p className="text-base md:text-lg text-slate-600 mb-8 leading-relaxed font-medium max-w-xl mx-auto lg:mx-0">
              FleetGuard connects drivers, verification workflows, and fleet teams in one platform — from onboarding and document submission to verification and approval.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link to="/login" className="w-full sm:w-auto bg-gradient-to-b from-[#00c853] to-[#00b048] hover:to-[#00a040] text-white text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-[0_4px_15px_rgba(0,200,83,0.3)] hover:shadow-[0_6px_20px_rgba(0,200,83,0.4)] border border-[#00e05d]/30 flex items-center justify-center gap-2 relative overflow-hidden group">
                Book a Demo <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login" className="w-full sm:w-auto bg-white/70 backdrop-blur-md hover:bg-white/90 text-slate-800 text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-sm border border-white/70 flex items-center justify-center">
                Open Dashboard
              </Link>
            </div>
          </motion.div>

          {/* Right: Ecosystem Visualization */}
          <motion.div 
            initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.2 }}
            className="w-full lg:w-7/12 relative flex justify-center"
          >
             <div className="relative p-2 rounded-[2rem] bg-white/40 backdrop-blur-xl border border-white/60 shadow-[0_8px_32px_rgba(0,0,0,0.05)] w-full max-w-2xl">
               <div className="bg-white/50 rounded-[1.5rem] p-6 border border-white/70 flex flex-col items-center gap-4 relative overflow-hidden shadow-inner">
                  
                  {/* Driver App Layer */}
                  <div className="w-full max-w-md bg-white/80 backdrop-blur-md rounded-2xl border border-white shadow-sm p-4 relative flex items-center gap-4">
                    <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center shrink-0 border border-blue-100">
                      <Smartphone className="w-5 h-5" />
                    </div>
                    <div>
                       <h3 className="font-bold text-slate-900 text-sm">Driver App</h3>
                       <div className="flex gap-2 mt-1">
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">OTP</span>
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">Profile</span>
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">Documents</span>
                       </div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  <div className="h-4 w-px bg-slate-300 relative">
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-[#00c853] rounded-full shadow-[0_0_4px_#00c853]" />
                  </div>

                  {/* Platform Layer */}
                  <div className="w-full max-w-sm bg-[#00c853]/10 backdrop-blur-md rounded-2xl border border-[#00c853]/20 shadow-[0_4px_16px_rgba(0,200,83,0.05)] p-4 relative flex items-center gap-4 z-10 transform md:scale-105">
                    <div className="w-10 h-10 bg-[#00c853]/10 text-[#00c853] rounded-lg flex items-center justify-center shrink-0 border border-[#00c853]/20">
                      <Server className="w-5 h-5" />
                    </div>
                    <div>
                       <h3 className="font-bold text-slate-900 text-sm">FleetGuard Platform</h3>
                       <div className="flex flex-wrap gap-2 mt-1">
                          <span className="text-[10px] font-bold text-[#00a040] bg-white/60 px-2 py-0.5 rounded shadow-sm border border-white/80">Verification</span>
                          <span className="text-[10px] font-bold text-[#00a040] bg-white/60 px-2 py-0.5 rounded shadow-sm border border-white/80">Processing</span>
                       </div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  <div className="h-4 w-px bg-slate-300 relative">
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-[#00c853] rounded-full shadow-[0_0_4px_#00c853]" />
                  </div>

                  {/* Dashboard Layer */}
                  <div className="w-full max-w-md bg-white/80 backdrop-blur-md rounded-2xl border border-white shadow-sm p-4 relative flex items-center gap-4">
                    <div className="w-10 h-10 bg-purple-50 text-purple-600 rounded-lg flex items-center justify-center shrink-0 border border-purple-100">
                      <LayoutDashboard className="w-5 h-5" />
                    </div>
                    <div>
                       <h3 className="font-bold text-slate-900 text-sm">Fleet Dashboard</h3>
                       <div className="flex gap-2 mt-1">
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">Drivers</span>
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">Documents</span>
                          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100/50 px-2 py-0.5 rounded border border-slate-200">Approvals</span>
                       </div>
                    </div>
                  </div>

               </div>
             </div>
          </motion.div>
        </div>
      </section>

      {/* 3. THE PROBLEM (Lighter padding) */}
      <section className="py-16 px-6 relative bg-white/40 border-y border-slate-200/50">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-3 tracking-tight">Fleet Operations Are Fragmented.</h2>
            <p className="text-base text-slate-600 max-w-2xl mx-auto font-medium">Driver information, documents, verification, and approvals often live across disconnected workflows.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: "Manual Onboarding", desc: "Collecting driver info manually creates unnecessary work.", icon: Users },
              { title: "Scattered Documents", desc: "Records spread across separate, disconnected systems.", icon: FileText },
              { title: "Slow Verification", desc: "Missing clear ways to review driver status quickly.", icon: Clock },
              { title: "Disconnected Ops", desc: "Drivers and fleet managers lack a single unified workflow.", icon: ShieldAlert },
            ].map((item, i) => (
              <div key={i} className="p-5 rounded-2xl bg-white/70 border border-white shadow-sm flex flex-col items-start hover:shadow-md transition-shadow">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
                  <item.icon className="w-5 h-5 text-slate-600" />
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1">{item.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 4. HOW IT WORKS (Glass Timeline, tighter layout) */}
      <section className="py-20 px-6 relative scroll-mt-24" id="how-it-works">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-6xl mx-auto"
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-slate-900 mb-3 tracking-tight">From Onboarding to Approval</h2>
            <p className="text-base text-slate-600 max-w-2xl mx-auto font-medium">A seamless workflow connecting drivers directly to fleet management.</p>
          </div>

          <div className="relative max-w-4xl mx-auto">
            {/* Glowing Glass Line (Desktop) */}
            <div className="hidden md:block absolute top-[28px] left-[15%] right-[15%] h-1 bg-[#00c853]/20 rounded-full" />

            <div className="flex flex-col md:flex-row gap-6 md:gap-4 justify-between">
              {[
                { num: "01", title: "Driver Onboards", desc: "Authenticate and provide essential info via mobile." },
                { num: "02", title: "Documents Processed", desc: "Submit required documents for backend verification." },
                { num: "03", title: "Manager Approves", desc: "Review complete profiles and decide via dashboard." }
              ].map((step, i) => (
                <div key={i} className="relative flex flex-col items-center text-center w-full md:w-1/3">
                  <div className="w-14 h-14 rounded-full bg-white/90 backdrop-blur-md border-2 border-[#00c853]/30 shadow-sm flex items-center justify-center text-lg font-black text-[#00c853] mb-4 z-10">
                    {step.num}
                  </div>
                  <div className="bg-white/60 backdrop-blur-md border border-white p-4 rounded-2xl shadow-sm w-full h-full">
                    <h3 className="text-base font-bold text-slate-900 mb-1">{step.title}</h3>
                    <p className="text-slate-600 text-sm leading-relaxed font-medium">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* 5. PRODUCT ECOSYSTEM (Connected Architecture, Clear Contrast) */}
      <section className="py-20 px-6 relative bg-slate-50 border-y border-slate-200/50 scroll-mt-24" id="product">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-[#00c853]/5 blur-[100px] rounded-full pointer-events-none -z-10" />

        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-6xl mx-auto relative z-10"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">One Connected Fleet Ecosystem</h2>
            <p className="text-base text-slate-600 max-w-2xl mx-auto font-medium">Data flows seamlessly from the driver to the platform, and into the fleet dashboard.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6 relative">
            
            {/* Desktop Connectors */}
            <div className="hidden md:block absolute top-[40%] left-[25%] right-[25%] h-0.5 bg-gradient-to-r from-slate-300 via-[#00c853] to-slate-300 opacity-50 z-0" />

            {/* Driver App */}
            <div className="bg-white/70 backdrop-blur-xl border border-white shadow-md p-6 rounded-3xl relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-5 border-b border-slate-100 pb-4">
                <div className="p-2 bg-slate-100 rounded-lg"><Smartphone className="w-5 h-5 text-slate-700" /></div>
                <h3 className="text-lg font-bold text-slate-900">DRIVER APP</h3>
              </div>
              <div className="space-y-2.5 flex-1">
                {['OTP Authentication', 'Driver Profile', 'Onboarding', 'Document Upload', 'Document Status'].map((item, i) => (
                  <div key={i} className="bg-slate-50/80 border border-slate-200 rounded-lg p-2.5 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#00c853]" />
                    <span className="text-sm font-medium text-slate-700">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Platform API */}
            <div className="bg-white/80 backdrop-blur-xl border-2 border-[#00c853]/20 shadow-[0_8px_30px_rgba(0,200,83,0.06)] p-6 rounded-3xl relative z-20 transform md:-translate-y-2 flex flex-col h-full">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#00c853]/10 text-[#00c853] text-[10px] font-bold px-3 py-1 rounded-full border border-[#00c853]/20 backdrop-blur-md">Core Platform</div>
              <div className="flex items-center gap-3 mb-5 border-b border-slate-100 pb-4 mt-2">
                <div className="p-2 bg-[#00c853]/10 rounded-lg"><Server className="w-5 h-5 text-[#00c853]" /></div>
                <h3 className="text-lg font-bold text-slate-900">PLATFORM API</h3>
              </div>
              <div className="space-y-2.5 flex-1">
                {['API Layer', 'Driver Records', 'Document Processing', 'Verification Workflow', 'Status Management'].map((item, i) => (
                  <div key={i} className="bg-slate-50/80 border border-slate-200 rounded-lg p-2.5 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-slate-500" />
                    <span className="text-sm font-medium text-slate-700">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Dashboard */}
            <div className="bg-white/70 backdrop-blur-xl border border-white shadow-md p-6 rounded-3xl relative z-10 flex flex-col h-full">
              <div className="flex items-center gap-3 mb-5 border-b border-slate-100 pb-4">
                <div className="p-2 bg-slate-100 rounded-lg"><LayoutDashboard className="w-5 h-5 text-slate-700" /></div>
                <h3 className="text-lg font-bold text-slate-900">DASHBOARD</h3>
              </div>
              <div className="space-y-2.5 flex-1">
                {['Driver Management', 'Driver Details', 'Documents', 'Verification Status', 'Approval Workflow'].map((item, i) => (
                  <div key={i} className="bg-slate-50/80 border border-slate-200 rounded-lg p-2.5 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#00c853]" />
                    <span className="text-sm font-medium text-slate-700">{item}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </motion.div>
      </section>

      {/* 6. VERIFICATION WORKFLOW (Pipeline) */}
      <section className="py-20 px-6 relative">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-6xl mx-auto"
        >
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-10 text-center tracking-tight">Verification Pipeline</h2>
          
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 max-w-5xl mx-auto relative">
            
            {/* Desktop Line */}
            <div className="hidden md:block absolute top-[40%] left-[10%] right-[10%] h-0.5 bg-slate-300 -z-10" />
            
            {/* Mobile Line */}
            <div className="block md:hidden absolute top-[10%] bottom-[10%] left-1/2 w-0.5 bg-slate-300 -translate-x-1/2 -z-10" />

            {[
              { title: 'Upload', desc: 'Driver submits docs', icon: UploadCloud },
              { title: 'Process', desc: 'System parses data', icon: Server },
              { title: 'Verify', desc: 'Status updated', icon: ShieldCheck },
              { title: 'Review', desc: 'Manager checks', icon: Users },
              { title: 'Decision', desc: 'Approved/Rejected', icon: CheckCircle }
            ].map((step, i) => (
              <div key={i} className="bg-white/90 backdrop-blur-sm border border-slate-200 shadow-sm p-4 rounded-xl flex flex-col items-center text-center w-40 z-10">
                <div className="bg-slate-50 p-2 rounded-full border border-slate-200 mb-2">
                  <step.icon className="w-4 h-4 text-slate-600" />
                </div>
                <h4 className="font-bold text-slate-900 text-sm mb-1">{step.title}</h4>
                <p className="text-[11px] text-slate-500 font-medium">{step.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 7. DRIVER APP MOCKUP */}
      <section className="py-20 bg-slate-100/50 px-6 relative border-t border-slate-200/50 scroll-mt-24" id="driver-app">
        <div className="max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-12">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
            className="lg:w-1/2 lg:pr-8"
          >
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">Built for Drivers.</h2>
            <p className="text-base text-slate-600 mb-8 font-medium leading-relaxed">Give drivers a straightforward way to onboard, manage their information, and submit required documents.</p>
            
            <div className="grid gap-4">
              {[
                { title: 'Secure OTP Login', desc: 'Access via mobile number and one-time password.' },
                { title: 'Profile & Onboarding', desc: 'Capture essential details during registration.' },
                { title: 'Document Upload', desc: 'Direct camera integration for document submission.' },
                { title: 'Status Tracking', desc: 'Visibility into document verification status.' }
              ].map((f, i) => (
                <div key={i} className="flex gap-4 p-4 rounded-xl bg-white/60 border border-white shadow-sm">
                  <CheckCircle className="w-5 h-5 text-[#00c853] shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm mb-0.5">{f.title}</h4>
                    <p className="text-sm text-slate-600">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true, margin: "-50px" }} transition={{ duration: 0.6 }}
            className="lg:w-1/2 flex justify-center relative"
          >
            {/* Phone Container */}
            <div className="relative w-[300px] h-[600px] bg-white rounded-[40px] border-8 border-slate-800 shadow-[0_20px_50px_rgba(0,0,0,0.1)] overflow-hidden flex flex-col">
              <div className="h-6 w-full bg-white flex justify-between items-center px-6 pt-2 z-40 text-slate-900">
                <span className="text-[10px] font-bold">9:41</span>
                <div className="flex gap-1">
                   <div className="w-3 h-2.5 bg-slate-800 rounded-sm" />
                   <div className="w-3 h-2.5 bg-slate-800 rounded-sm" />
                </div>
              </div>
              
              <div className="flex-1 bg-slate-50 flex flex-col relative px-4 pt-6 pb-4">
                <h3 className="font-extrabold text-xl text-slate-900 mb-1">My Profile</h3>
                <span className="text-[10px] font-bold text-slate-500 mb-6 uppercase">Driver ID: FG-8821</span>
                
                <div className="space-y-3">
                  <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                     <h4 className="text-[11px] font-bold text-slate-500 uppercase mb-2">Required Documents</h4>
                     
                     <div className="space-y-2">
                       <div className="flex items-center justify-between">
                         <div className="flex items-center gap-2">
                           <FileCheck2 className="w-4 h-4 text-[#00c853]" />
                           <span className="text-xs font-bold text-slate-800">Driving License</span>
                         </div>
                         <span className="text-[9px] text-[#00c853] font-bold bg-[#00c853]/10 px-2 py-0.5 rounded">Verified</span>
                       </div>
                       
                       <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                         <div className="flex items-center gap-2">
                           <UploadCloud className="w-4 h-4 text-slate-400" />
                           <span className="text-xs font-bold text-slate-800">Aadhar Card</span>
                         </div>
                         <span className="text-[9px] text-yellow-600 font-bold bg-yellow-50 px-2 py-0.5 rounded border border-yellow-200">Pending</span>
                       </div>
                     </div>
                  </div>
                  
                  <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                    <h4 className="text-[11px] font-bold text-slate-500 uppercase mb-2">Status</h4>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500" />
                      <span className="text-xs font-bold text-slate-700">Awaiting Fleet Approval</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="h-1 w-1/3 bg-slate-300 mx-auto rounded-full mb-2" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* 8. FLEET DASHBOARD MOCKUP */}
      <section className="py-20 px-6 relative scroll-mt-24" id="dashboard">
        <div className="absolute inset-0 bg-[#f8fafc] -z-20" />
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">Designed for Fleet Teams.</h2>
            <p className="text-base text-slate-600 max-w-2xl mx-auto font-medium">Manage drivers, review submitted information, and make approval decisions from one dashboard.</p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-50px" }} transition={{ duration: 0.6 }}
            className="w-full relative"
          >
             <DemoDashboard />
          </motion.div>
        </div>
      </section>

      {/* 9. FEATURES */}
      <section className="py-20 bg-white border-y border-slate-200/50 px-6 relative">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-6xl mx-auto"
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-slate-900 mb-3 tracking-tight">Everything You Need to Manage Your Drivers</h2>
            <p className="text-base text-slate-600 max-w-2xl mx-auto font-medium">A complete feature set for driver verification and fleet operations.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: 'Driver Onboarding', desc: 'Bring new drivers into a structured workflow effortlessly.' },
              { title: 'Secure Auth', desc: 'Authenticate via secure login and mobile OTP.' },
              { title: 'Document Upload', desc: 'Submit required documents directly through the App.' },
              { title: 'Data Processing', desc: 'Process submissions through the backend pipeline.' },
              { title: 'Verification', desc: 'Track verification status in real-time accurately.' },
              { title: 'Approvals', desc: 'Review information and make swift operational decisions.' },
              { title: 'Fleet Dashboard', desc: 'Manage everything from a clear, centralized interface.' },
              { title: 'Driver Records', desc: 'View and manage comprehensive driver status easily.' }
            ].map((feature, i) => (
              <div key={i} className="p-5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-[#00c853]/30 hover:shadow-md transition-all duration-200 group">
                <CheckCircle className="w-5 h-5 text-slate-400 group-hover:text-[#00c853] mb-3 transition-colors" />
                <h3 className="font-bold text-slate-900 text-sm mb-1">{feature.title}</h3>
                <p className="text-slate-600 text-xs leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 10. TRUST / SECURITY */}
      <section className="py-20 px-6 relative bg-slate-50">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-5xl mx-auto bg-white border border-slate-200 p-8 md:p-12 rounded-3xl shadow-sm flex flex-col md:flex-row items-center gap-10"
        >
          <div className="md:w-1/2 text-center md:text-left">
            <ShieldCheck className="w-10 h-10 text-[#00c853] mb-4 mx-auto md:mx-0" />
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-4 tracking-tight">Controlled Workflows. Clear Visibility.</h2>
            <p className="text-slate-600 text-sm font-medium leading-relaxed">
              FleetGuard uses authenticated workflows and controlled dashboard access to keep driver operations organized and easily accessible to authorized personnel.
            </p>
          </div>
          
          <div className="md:w-1/2 w-full flex flex-col gap-3">
             <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-[#00c853]" />
                <span className="text-sm font-bold text-slate-800">Authenticated Access</span>
             </div>
             <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-[#00c853]" />
                <span className="text-sm font-bold text-slate-800">Controlled Dashboard</span>
             </div>
             <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-[#00c853]" />
                <span className="text-sm font-bold text-slate-800">Structured Verification</span>
             </div>
          </div>
        </motion.div>
      </section>

      {/* 11. FINAL CTA */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#00c853]/10 blur-[80px] rounded-full -z-10 pointer-events-none" />

        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={sectionVariants}
          className="max-w-4xl mx-auto text-center bg-white/70 backdrop-blur-xl border border-white shadow-lg p-10 md:p-16 rounded-[2rem]"
        >
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">
            Bring Your Drivers and Fleet Operations Into One Platform
          </h2>
          <p className="text-base text-slate-600 mb-8 max-w-xl mx-auto font-medium">
            See how FleetGuard connects driver onboarding, document verification, and fleet management.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/login" className="w-full sm:w-auto bg-gradient-to-b from-[#00c853] to-[#00b048] hover:to-[#00a040] text-white text-sm font-bold px-8 py-3.5 rounded-xl transition-all shadow-[0_4px_15px_rgba(0,200,83,0.3)] hover:shadow-[0_6px_20px_rgba(0,200,83,0.4)] border border-[#00e05d]/30">
              Book a Demo
            </Link>
            <Link to="/login" className="w-full sm:w-auto bg-white hover:bg-slate-50 text-slate-900 text-sm font-bold px-8 py-3.5 rounded-xl transition-all shadow-sm border border-slate-200">
              Open Dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      {/* 12. FOOTER */}
      <footer className="bg-slate-950 text-slate-400 py-16 px-6 relative z-10 border-t border-slate-900">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 border-b border-slate-800/50 pb-12 mb-8">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight text-white">Fleet<span className="text-[#00c853]">Guard</span></span>
            </div>
            <p className="text-xs font-medium leading-relaxed text-slate-500">
              The connected fleet management and driver verification ecosystem.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4 tracking-wide text-xs">PRODUCT</h4>
            <ul className="space-y-2 text-xs font-medium">
              <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
              <li><a href="#driver-app" className="hover:text-white transition-colors">Driver App</a></li>
              <li><a href="#dashboard" className="hover:text-white transition-colors">Fleet Dashboard</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4 tracking-wide text-xs">COMPANY</h4>
            <ul className="space-y-2 text-xs font-medium">
              <li><a href="#" className="hover:text-white transition-colors">About</a></li>
              <li><a href="mailto:contact@fleetguard.com" className="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4 tracking-wide text-xs">ACCESS</h4>
            <ul className="space-y-2 text-xs font-medium">
              <li><Link to="/login" className="hover:text-white transition-colors">Dashboard Login</Link></li>
              <li><Link to="/downloads" className="hover:text-white transition-colors">Get Driver App</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-6xl mx-auto flex justify-between items-center text-[10px] font-semibold text-slate-600">
          <p>© {new Date().getFullYear()} FleetGuard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
