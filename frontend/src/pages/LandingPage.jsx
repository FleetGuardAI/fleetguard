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
  ChevronDown,
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
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-[#00c853]/20">
      {/* 1. NAVBAR */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/90 backdrop-blur-md shadow-sm border-b border-slate-200' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-[#00c853] flex items-center justify-center shadow-lg shadow-[#00c853]/20 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">Fleet<span className="text-[#00c853]">Guard</span></span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#product" className="hover:text-slate-900 transition-colors">Product</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How It Works</a>
            <a href="#driver-app" className="hover:text-slate-900 transition-colors">Driver App</a>
            <a href="#dashboard" className="hover:text-slate-900 transition-colors">Fleet Dashboard</a>
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Link to="/login" className="text-sm font-bold text-slate-700 hover:text-slate-900 px-4 py-2 transition-colors">
              Dashboard
            </Link>
            <Link to="/login" className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold px-5 py-2.5 rounded-lg transition-all shadow-md">
              Book a Demo
            </Link>
          </div>

          <button className="md:hidden p-2 text-slate-600" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden bg-white border-b border-slate-200 px-6 py-4 overflow-hidden"
            >
              <div className="flex flex-col gap-4 text-sm font-medium text-slate-600">
                <a href="#product" onClick={() => setIsMobileMenuOpen(false)}>Product</a>
                <a href="#how-it-works" onClick={() => setIsMobileMenuOpen(false)}>How It Works</a>
                <a href="#driver-app" onClick={() => setIsMobileMenuOpen(false)}>Driver App</a>
                <a href="#dashboard" onClick={() => setIsMobileMenuOpen(false)}>Fleet Dashboard</a>
                <div className="h-px bg-slate-100 my-2" />
                <Link to="/login" className="text-slate-900 font-bold" onClick={() => setIsMobileMenuOpen(false)}>Dashboard Login</Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* 2. HERO */}
      <section className="pt-40 pb-20 px-6 overflow-hidden relative">
        {/* Subtle background element */}
        <div className="absolute top-0 inset-x-0 h-[500px] bg-gradient-to-b from-[#00c853]/5 to-transparent -z-10 pointer-events-none" />
        
        <div className="max-w-7xl mx-auto text-center">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight leading-[1.1] mb-6"
          >
            Manage Your Fleet.<br />
            <span className="text-[#00c853]">Verify Every Driver.</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed"
          >
            FleetGuard connects drivers, verification workflows, and fleet teams in one platform — from onboarding and document submission to verification and approval.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/login" className="w-full sm:w-auto bg-[#00c853] hover:bg-[#00b848] text-white text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-[#00c853]/20 flex items-center justify-center gap-2">
              Book a Demo <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="w-full sm:w-auto bg-white hover:bg-slate-50 text-slate-700 text-base font-bold px-8 py-3.5 rounded-xl transition-all shadow-sm border border-slate-200">
              Open Dashboard
            </Link>
          </motion.div>

          {/* HERO VISUAL - Ecosystem */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.4 }}
            className="mt-20 relative max-w-5xl mx-auto"
          >
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-4 p-8 bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100">
              
              <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-slate-50 rounded-2xl border border-slate-100 relative group">
                <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-4">
                  <Smartphone className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">Driver App</h3>
                <ul className="text-xs text-slate-500 font-medium space-y-1.5 text-center">
                  <li>Driver Onboarding</li>
                  <li>Document Upload</li>
                  <li>Profile Status</li>
                </ul>
                <div className="absolute -bottom-6 md:-right-6 md:top-1/2 md:-translate-y-1/2 md:bottom-auto text-slate-300 group-hover:text-[#00c853] transition-colors rotate-90 md:rotate-0 z-10 bg-white p-1 rounded-full">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>

              <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-[#00c853]/5 rounded-2xl border border-[#00c853]/20 relative group">
                <div className="w-12 h-12 bg-[#00c853]/10 text-[#00c853] rounded-xl flex items-center justify-center mb-4">
                  <Server className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">FleetGuard Core</h3>
                <ul className="text-xs text-slate-600 font-medium space-y-1.5 text-center">
                  <li>API Integration</li>
                  <li>Document Processing</li>
                  <li>Verification Engine</li>
                </ul>
                <div className="absolute -bottom-6 md:-right-6 md:top-1/2 md:-translate-y-1/2 md:bottom-auto text-slate-300 group-hover:text-[#00c853] transition-colors rotate-90 md:rotate-0 z-10 bg-white p-1 rounded-full">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>

              <div className="w-full md:w-1/3 flex flex-col items-center p-6 bg-slate-50 rounded-2xl border border-slate-100">
                <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-4">
                  <LayoutDashboard className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">Fleet Dashboard</h3>
                <ul className="text-xs text-slate-500 font-medium space-y-1.5 text-center">
                  <li>Driver Management</li>
                  <li>Document Review</li>
                  <li>Approvals</li>
                </ul>
              </div>

            </div>
          </motion.div>
        </div>
      </section>

      {/* 3. THE PROBLEM */}
      <section className="py-24 bg-white px-6" id="problem">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Fleet Operations Are Fragmented.</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">Driver information, documents, verification, and approvals often live across disconnected workflows.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: "Manual Onboarding", desc: "Collecting and managing driver information manually creates unnecessary operational work.", icon: Users },
              { title: "Scattered Documents", desc: "Driver documents are difficult to track when submissions and records are spread across different workflows.", icon: FileText },
              { title: "Slow Verification", desc: "Fleet teams need a clear way to review driver information and document status before approval.", icon: Clock },
              { title: "Disconnected Ops", desc: "Drivers and fleet managers need one connected workflow instead of separate processes.", icon: ShieldAlert },
            ].map((item, i) => (
              <div key={i} className="p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors">
                <item.icon className="w-8 h-8 text-slate-400 mb-4" />
                <h3 className="text-lg font-bold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 4. HOW IT WORKS */}
      <section className="py-24 bg-slate-50 px-6" id="how-it-works">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">From Driver Onboarding to Fleet Approval</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">A seamless workflow connecting drivers to fleet management.</p>
          </div>

          <div className="relative max-w-4xl mx-auto">
            {/* Connecting Line (Desktop) */}
            <div className="hidden md:block absolute top-[45px] left-[15%] right-[15%] h-0.5 bg-slate-200 -z-10" />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              {[
                { num: "01", title: "Driver Onboards", desc: "Drivers authenticate, provide their information, and complete the onboarding process." },
                { num: "02", title: "Documents Processed", desc: "Drivers submit required documents through the App and FleetGuard processes the information." },
                { num: "03", title: "Manager Approves", desc: "Fleet teams review driver information, documents, and verification status via the dashboard." }
              ].map((step, i) => (
                <div key={i} className="relative flex flex-col items-center text-center">
                  <div className="w-24 h-24 rounded-full bg-white border-4 border-slate-50 shadow-md flex items-center justify-center text-2xl font-black text-[#00c853] mb-6">
                    {step.num}
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-3">{step.title}</h3>
                  <p className="text-slate-600 text-sm leading-relaxed max-w-xs">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* 5. PRODUCT ECOSYSTEM */}
      <section className="py-24 bg-slate-900 text-white px-6 overflow-hidden" id="product">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4">One Connected Fleet Ecosystem</h2>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">FleetGuard connects the driver side and fleet-management side through our backend platform.</p>
          </div>

          <div className="flex flex-col md:flex-row justify-center items-stretch gap-4 md:gap-0 mt-12 relative max-w-6xl mx-auto">
            {/* Component 1 */}
            <div className="w-full md:w-1/3 bg-slate-800 rounded-2xl md:rounded-r-none border border-slate-700 p-8 z-10 shadow-2xl relative">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Smartphone className="text-blue-400" /> DRIVER APP</h3>
              <ul className="space-y-4">
                {['OTP Authentication', 'Driver Profile', 'Onboarding', 'Document Upload', 'Document Status'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-300 text-sm font-medium">
                    <CheckCircle className="w-4 h-4 text-blue-500" /> {item}
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Connecting Arrows - Vertical on Mobile, Horizontal on Desktop */}
            <div className="flex md:hidden justify-center py-2 text-slate-600">
               <ArrowRight className="w-6 h-6 rotate-90" />
            </div>

            {/* Component 2 */}
            <div className="w-full md:w-1/3 bg-[#00c853]/10 backdrop-blur-md rounded-2xl border border-[#00c853]/30 p-8 z-20 shadow-2xl md:-mx-4 md:scale-105 relative">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2 text-white"><Server className="text-[#00c853]" /> PLATFORM API</h3>
              <ul className="space-y-4">
                {['API Layer', 'Driver Records', 'Document Processing', 'Verification Workflow', 'Status Management'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-200 text-sm font-medium">
                    <ShieldCheck className="w-4 h-4 text-[#00c853]" /> {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Connecting Arrows */}
            <div className="flex md:hidden justify-center py-2 text-slate-600">
               <ArrowRight className="w-6 h-6 rotate-90" />
            </div>

            {/* Component 3 */}
            <div className="w-full md:w-1/3 bg-slate-800 rounded-2xl md:rounded-l-none border border-slate-700 p-8 z-10 shadow-2xl relative">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><LayoutDashboard className="text-purple-400" /> DASHBOARD</h3>
              <ul className="space-y-4">
                {['Driver Management', 'Driver Details', 'Documents', 'Verification Status', 'Approval Workflow'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-300 text-sm font-medium">
                    <ListTodo className="w-4 h-4 text-purple-500" /> {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      </section>

      {/* 6. DRIVER APP */}
      <section className="py-24 bg-white px-6 overflow-hidden" id="driver-app">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
            className="lg:w-1/2"
          >
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Built for Drivers.</h2>
            <p className="text-lg text-slate-600 mb-8">Give drivers a straightforward way to onboard, manage their information, and submit required documents.</p>
            
            <ul className="space-y-6">
              {[
                { title: 'Secure OTP Login', desc: 'Fast, secure access using mobile number and one-time password.' },
                { title: 'Profile & Onboarding', desc: 'Easy capture of essential driver details during registration.' },
                { title: 'Document Upload', desc: 'Direct camera integration for clear document submission.' },
                { title: 'Status Tracking', desc: 'Real-time visibility into document verification status.' }
              ].map((f, i) => (
                <li key={i} className="flex gap-4">
                  <div className="mt-1 w-6 h-6 rounded-full bg-[#00c853]/10 flex items-center justify-center shrink-0">
                    <CheckCircle className="w-3.5 h-3.5 text-[#00c853]" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900">{f.title}</h4>
                    <p className="text-sm text-slate-600">{f.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 50 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, margin: "-100px" }} transition={{ duration: 0.8 }}
            className="lg:w-1/2 relative flex justify-center"
          >
            {/* Mockup - Mobile Phone */}
            <div className="relative w-[280px] h-[580px] bg-white rounded-[40px] border-[8px] border-slate-900 shadow-2xl overflow-hidden flex flex-col">
              {/* Status Bar */}
              <div className="h-6 w-full bg-white flex justify-between items-center px-4 pt-1">
                <span className="text-[10px] font-medium">9:41</span>
                <div className="flex gap-1">
                   <div className="w-3 h-2.5 bg-slate-800 rounded-[2px]" />
                   <div className="w-3 h-2.5 bg-slate-800 rounded-[2px]" />
                </div>
              </div>
              
              {/* App Content Fake UI */}
              <div className="flex-1 bg-slate-50 flex flex-col">
                <div className="bg-[#00c853] text-white p-5 pb-6 rounded-b-3xl">
                   <h3 className="font-bold text-lg mb-1">Hello, Driver</h3>
                   <p className="text-xs opacity-90">Your profile is 80% complete</p>
                </div>
                
                <div className="p-4 flex-1">
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 mb-4">
                     <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center justify-between">
                       Required Documents
                       <span className="text-[10px] bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full font-bold">Action Needed</span>
                     </h4>
                     
                     <div className="space-y-3">
                       <div className="flex items-center justify-between">
                         <div className="flex items-center gap-2">
                           <FileCheck2 className="w-4 h-4 text-[#00c853]" />
                           <span className="text-xs font-medium text-slate-700">Driving License</span>
                         </div>
                         <span className="text-[10px] text-[#00c853] font-bold">Verified</span>
                       </div>
                       
                       <div className="flex items-center justify-between">
                         <div className="flex items-center gap-2">
                           <UploadCloud className="w-4 h-4 text-slate-400" />
                           <span className="text-xs font-medium text-slate-700">Aadhar Card</span>
                         </div>
                         <button className="text-[10px] bg-slate-900 text-white px-2 py-1 rounded font-medium">Upload</button>
                       </div>
                     </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
                    <h4 className="text-sm font-bold text-slate-900 mb-2">Verification Status</h4>
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                      <span className="text-xs text-slate-600">Pending Fleet Approval</span>
                    </div>
                  </div>
                </div>
              </div>
              {/* Home indicator */}
              <div className="h-1 w-1/3 bg-slate-300 mx-auto rounded-full mb-2" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* 7. FLEET DASHBOARD */}
      <section className="py-24 bg-slate-50 px-6 border-y border-slate-200" id="dashboard">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Designed for Fleet Teams.</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">Manage drivers, review submitted information, and make approval decisions from one centralized dashboard.</p>
          </motion.div>

          {/* Desktop Dashboard Mockup */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-100px" }} transition={{ duration: 0.8 }}
            className="w-full rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="h-14 border-b border-slate-100 flex items-center px-6 justify-between bg-white">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-[#00c853] flex items-center justify-center"><ShieldCheck className="w-3 h-3 text-white" /></div>
                <span className="font-bold text-sm">Dashboard</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-64 h-8 bg-slate-100 rounded-md" />
                <div className="w-8 h-8 rounded-full bg-slate-200" />
              </div>
            </div>
            
            <div className="flex h-[500px]">
              {/* Sidebar */}
              <div className="w-64 border-r border-slate-100 p-4 space-y-2 hidden md:block">
                <div className="p-2 text-sm font-bold text-[#00c853] bg-[#00c853]/10 rounded-lg flex items-center gap-2">
                  <Users className="w-4 h-4" /> Drivers
                </div>
                <div className="p-2 text-sm font-medium text-slate-500 hover:bg-slate-50 rounded-lg flex items-center gap-2">
                  <FileSignature className="w-4 h-4" /> Approvals
                </div>
                <div className="p-2 text-sm font-medium text-slate-500 hover:bg-slate-50 rounded-lg flex items-center gap-2">
                  <FileText className="w-4 h-4" /> Documents
                </div>
              </div>
              
              {/* Content */}
              <div className="flex-1 p-6 bg-slate-50/50 overflow-hidden">
                <h3 className="text-xl font-bold text-slate-900 mb-6">Driver Management</h3>
                
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 border-b border-slate-100 text-slate-500">
                      <tr>
                        <th className="p-4 font-semibold">Driver Name</th>
                        <th className="p-4 font-semibold">Status</th>
                        <th className="p-4 font-semibold">Documents</th>
                        <th className="p-4 font-semibold">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        { name: 'Raj Kumar', status: 'Pending Review', docs: '2/2 Uploaded', color: 'bg-yellow-100 text-yellow-700' },
                        { name: 'Amit Singh', status: 'Approved', docs: 'Verified', color: 'bg-green-100 text-green-700' },
                        { name: 'Vikram Sharma', status: 'Missing Docs', docs: '1/2 Uploaded', color: 'bg-red-100 text-red-700' },
                        { name: 'Sanjay Verma', status: 'Approved', docs: 'Verified', color: 'bg-green-100 text-green-700' },
                      ].map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="p-4 font-medium text-slate-900">{row.name}</td>
                          <td className="p-4">
                            <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${row.color}`}>
                              {row.status}
                            </span>
                          </td>
                          <td className="p-4 text-slate-600 text-xs">{row.docs}</td>
                          <td className="p-4">
                            <button className="text-xs font-bold text-blue-600 hover:text-blue-800">View Details</button>
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

      {/* 8. VERIFICATION WORKFLOW */}
      <section className="py-20 bg-white px-6">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto text-center"
        >
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-12">From Document Submission to Verified Driver</h2>
          
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 max-w-5xl mx-auto">
            {['Driver Upload', 'Platform Processing', 'Verification Status', 'Fleet Review'].map((step, i) => (
              <React.Fragment key={i}>
                <div className="bg-slate-50 border border-slate-200 px-4 py-3 rounded-xl font-bold text-slate-700 text-sm w-48 shadow-sm">
                  {step}
                </div>
                {i < 3 && <ArrowRight className="w-5 h-5 text-slate-300 hidden md:block" />}
                {i < 3 && <ArrowRight className="w-5 h-5 text-slate-300 rotate-90 md:hidden my-2" />}
              </React.Fragment>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 9. FEATURES */}
      <section className="py-24 bg-slate-50 px-6">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Everything You Need to Manage Driver Verification</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { title: 'Driver Onboarding', desc: 'Bring new drivers into a structured onboarding workflow effortlessly.' },
              { title: 'Secure Authentication', desc: 'Authenticate drivers through the existing secure login and OTP flow.' },
              { title: 'Document Upload', desc: 'Allow drivers to submit required documents through the dedicated Driver App.' },
              { title: 'Document Processing', desc: 'Process submitted driver documents through FleetGuard\'s robust backend pipeline.' },
              { title: 'Driver Verification', desc: 'Track document and driver verification status in real-time.' },
              { title: 'Approval Management', desc: 'Review driver information and take approval or rejection actions swiftly.' },
              { title: 'Fleet Dashboard', desc: 'Manage driver operations from a centralized, clear management interface.' },
              { title: 'Driver Management', desc: 'View and manage comprehensive driver records and their current status.' }
            ].map((feature, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                <CheckCircle className="w-6 h-6 text-[#00c853] mb-4" />
                <h3 className="font-bold text-slate-900 text-lg mb-2">{feature.title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 10. TRUST / SECURITY */}
      <section className="py-20 bg-white px-6 border-t border-slate-100">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-3xl mx-auto text-center"
        >
          <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-6" />
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mb-4">Controlled Workflows. Clear Visibility.</h2>
          <p className="text-slate-600 text-lg">
            FleetGuard uses authenticated workflows and controlled dashboard access to keep driver and fleet operations organized and easily accessible to authorized personnel.
          </p>
        </motion.div>
      </section>

      {/* 11. FINAL CTA */}
      <section className="py-24 bg-[#00c853] px-6 text-white text-center">
        <motion.div 
          initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={sectionVariants}
          className="max-w-4xl mx-auto"
        >
          <h2 className="text-3xl md:text-5xl font-extrabold mb-6">Bring Your Drivers and Fleet Operations Into One Platform</h2>
          <p className="text-lg md:text-xl font-medium text-white/90 mb-10 max-w-2xl mx-auto">
            See how FleetGuard connects driver onboarding, document verification, and fleet management.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/login" className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-white text-base font-bold px-8 py-4 rounded-xl transition-all shadow-lg">
              Book a Demo
            </Link>
            <Link to="/login" className="w-full sm:w-auto bg-white hover:bg-slate-50 text-slate-900 text-base font-bold px-8 py-4 rounded-xl transition-all shadow-lg">
              Open Dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      {/* 12. FOOTER */}
      <footer className="bg-slate-950 text-slate-400 py-16 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 border-b border-slate-800 pb-12 mb-8">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded bg-[#00c853] flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight text-white">Fleet<span className="text-[#00c853]">Guard</span></span>
            </div>
            <p className="text-sm">
              The connected fleet management and driver verification ecosystem.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4">PRODUCT</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
              <li><a href="#driver-app" className="hover:text-white transition-colors">Driver App</a></li>
              <li><a href="#dashboard" className="hover:text-white transition-colors">Fleet Dashboard</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4">COMPANY</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">About</a></li>
              <li><a href="mailto:contact@fleetguard.com" className="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-4">ACCESS</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/login" className="hover:text-white transition-colors">Dashboard Login</Link></li>
              <li><Link to="/downloads" className="hover:text-white transition-colors">Get Driver App</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-xs">
          <p>© {new Date().getFullYear()} FleetGuard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
