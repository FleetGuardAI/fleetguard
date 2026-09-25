import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, FileSignature, FileText, Download, Search, 
  ShieldCheck, CheckCircle, XCircle, Eye, ChevronRight, X, Clock
} from 'lucide-react';

const INITIAL_DRIVERS = [
  {
    id: 'FG-8821',
    name: 'Rajesh Kumar',
    phone: '+91 98765 43210',
    status: 'active',
    verification_status: 'PENDING_APPROVAL',
    documents: [
      { id: 'd1', type: 'Driving License', status: 'VERIFIED' },
      { id: 'd2', type: 'Aadhaar Card', status: 'VERIFIED' },
    ],
    date: '2023-10-24'
  },
  {
    id: 'FG-8822',
    name: 'Amit Singh',
    phone: '+91 91234 56789',
    status: 'active',
    verification_status: 'APPROVED',
    documents: [
      { id: 'd3', type: 'Driving License', status: 'VERIFIED' },
      { id: 'd4', type: 'Aadhaar Card', status: 'VERIFIED' },
    ],
    date: '2023-10-22'
  },
  {
    id: 'FG-8823',
    name: 'Vikram Sharma',
    phone: '+91 99887 76655',
    status: 'inactive',
    verification_status: 'PENDING_DOCUMENTS',
    documents: [
      { id: 'd5', type: 'Driving License', status: 'VERIFIED' },
      { id: 'd6', type: 'Aadhaar Card', status: 'PENDING' },
    ],
    date: '2023-10-25'
  },
  {
    id: 'FG-8824',
    name: 'Sanjay Verma',
    phone: '+91 98712 34567',
    status: 'active',
    verification_status: 'APPROVED',
    documents: [
      { id: 'd7', type: 'Driving License', status: 'VERIFIED' },
      { id: 'd8', type: 'Aadhaar Card', status: 'VERIFIED' },
    ],
    date: '2023-10-20'
  },
  {
    id: 'FG-8825',
    name: 'Manoj Tiwari',
    phone: '+91 98989 89898',
    status: 'active',
    verification_status: 'PENDING_APPROVAL',
    documents: [
      { id: 'd9', type: 'Driving License', status: 'VERIFIED' },
      { id: 'd10', type: 'Aadhaar Card', status: 'VERIFIED' },
    ],
    date: '2023-10-26'
  }
];

export default function DemoDashboard() {
  const [drivers, setDrivers] = useState(INITIAL_DRIVERS);
  const [activeTab, setActiveTab] = useState('drivers');
  
  // Filtering
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedDocument(null);
        setSelectedDriver(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  // Loading states for interactions
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // ─── DERIVED DATA ─────────────────────────────────────────────────────────────
  
  const filteredDrivers = useMemo(() => {
    return drivers.filter(d => {
      const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            d.id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'ALL' || d.verification_status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [drivers, searchQuery, statusFilter]);

  const pendingApprovals = useMemo(() => {
    return drivers.filter(d => d.verification_status === 'PENDING_APPROVAL');
  }, [drivers]);

  const allDocuments = useMemo(() => {
    const docs = [];
    drivers.forEach(d => {
      d.documents.forEach(doc => {
        docs.push({ ...doc, driverName: d.name, driverId: d.id, date: d.date });
      });
    });
    return docs;
  }, [drivers]);

  const totalEnrolled = drivers.length;
  const totalApproved = drivers.filter(d => d.verification_status === 'APPROVED').length;

  // ─── ACTIONS ──────────────────────────────────────────────────────────────────

  const handleApprove = async (driverId) => {
    setIsActionLoading(true);
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 600));
    setDrivers(prev => prev.map(d => 
      d.id === driverId ? { ...d, verification_status: 'APPROVED' } : d
    ));
    setIsActionLoading(false);
    setSelectedDriver(null);
    showToast(`Driver ${driverId} approved successfully.`);
  };

  const handleReject = async (driverId) => {
    setIsActionLoading(true);
    await new Promise(resolve => setTimeout(resolve, 600));
    setDrivers(prev => prev.map(d => 
      d.id === driverId ? { ...d, verification_status: 'REJECTED' } : d
    ));
    setIsActionLoading(false);
    setSelectedDriver(null);
    showToast(`Driver ${driverId} rejected.`);
  };

  const handleExport = async () => {
    setIsActionLoading(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Generate real CSV
    const headers = ['Driver ID', 'Name', 'Phone', 'Status', 'Verification Status'];
    const rows = filteredDrivers.map(d => 
      `${d.id},${d.name},${d.phone},${d.status},${d.verification_status}`
    );
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "fleetguard_drivers_demo.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setIsActionLoading(false);
    showToast('Export successful.');
  };

  // ─── RENDERERS ────────────────────────────────────────────────────────────────

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return <span className="bg-[#00c853]/10 text-[#00c853] border border-[#00c853]/20 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide uppercase">Approved</span>;
      case 'PENDING_APPROVAL':
        return <span className="bg-yellow-500/10 text-yellow-700 border border-yellow-500/20 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide uppercase">Pending Review</span>;
      case 'PENDING_DOCUMENTS':
        return <span className="bg-blue-500/10 text-blue-700 border border-blue-500/20 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide uppercase">Missing Docs</span>;
      case 'REJECTED':
        return <span className="bg-red-500/10 text-red-700 border border-red-500/20 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide uppercase">Rejected</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide uppercase">{status}</span>;
    }
  };

  return (
    <div className="w-full rounded-2xl border border-white/60 shadow-[0_20px_60px_rgba(0,0,0,0.06)] bg-white/40 backdrop-blur-2xl overflow-hidden relative flex flex-col font-sans">
      
      {/* Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 z-[100] bg-slate-900 text-white text-sm font-bold px-4 py-2 rounded-xl shadow-lg flex items-center gap-2"
          >
            <CheckCircle className="w-4 h-4 text-[#00c853]" />
            {toastMessage}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header / Chrome */}
      <div className="h-14 border-b border-white/50 flex items-center px-4 justify-between bg-white/50 backdrop-blur-md relative z-20">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5 mr-2">
            <div className="w-3 h-3 rounded-full bg-red-400" />
            <div className="w-3 h-3 rounded-full bg-yellow-400" />
            <div className="w-3 h-3 rounded-full bg-green-400" />
          </div>
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#00c853] to-[#00a040] flex items-center justify-center shadow-sm">
            <ShieldCheck className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-bold text-slate-800 text-sm flex items-center gap-2">
            Interactive Demo <span className="bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider">Read-Only</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-200 border-2 border-white shadow-sm overflow-hidden flex items-center justify-center">
             <Users className="w-4 h-4 text-slate-500" />
          </div>
        </div>
      </div>
      
      <div className="flex flex-col md:flex-row flex-1 h-auto md:h-[550px] relative z-10">
        
        {/* Mobile Nav Tabs */}
        <div className="flex md:hidden border-b border-white/50 bg-white/30 backdrop-blur-md overflow-x-auto p-2 gap-2">
           {[
             { id: 'drivers', label: 'Drivers', icon: Users },
             { id: 'approvals', label: 'Approvals', icon: FileSignature, badge: pendingApprovals.length },
             { id: 'documents', label: 'Documents', icon: FileText }
           ].map(tab => (
             <button
               key={tab.id}
               onClick={() => setActiveTab(tab.id)}
               className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold whitespace-nowrap transition-colors ${
                 activeTab === tab.id ? 'bg-white shadow-sm border border-white/60 text-[#00c853]' : 'text-slate-600 hover:bg-white/40'
               }`}
             >
               <tab.icon className="w-4 h-4" /> {tab.label}
               {tab.badge > 0 && <span className="ml-1 bg-red-500 text-white px-1.5 rounded-full text-[10px]">{tab.badge}</span>}
             </button>
           ))}
        </div>

        {/* Desktop Sidebar */}
        <div className="w-56 border-r border-white/50 p-3 space-y-1 hidden md:block bg-white/20 backdrop-blur-lg">
          {[
            { id: 'drivers', label: 'Drivers', icon: Users },
            { id: 'approvals', label: 'Approvals', icon: FileSignature, badge: pendingApprovals.length },
            { id: 'documents', label: 'Documents', icon: FileText }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center justify-between p-3 rounded-xl text-sm font-bold transition-all duration-200 ${
                activeTab === tab.id 
                  ? 'bg-white/70 shadow-sm border border-white/80 text-[#00c853]' 
                  : 'text-slate-600 hover:bg-white/40 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-2">
                <tab.icon className="w-4 h-4" /> {tab.label}
              </div>
              {tab.badge > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] ${activeTab === tab.id ? 'bg-[#00c853] text-white' : 'bg-red-500 text-white'}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
        
        {/* Main Panel */}
        <div className="flex-1 p-4 md:p-6 bg-white/30 overflow-y-auto">
          
          {/* DRIVERS VIEW */}
          {activeTab === 'drivers' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-4">
                 <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">Driver Management</h3>
                 <button 
                   onClick={handleExport}
                   disabled={isActionLoading}
                   className="px-4 py-2 bg-white/80 border border-white/90 rounded-lg text-sm font-bold text-slate-700 shadow-sm hover:shadow-md hover:bg-white transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                 >
                   {isActionLoading ? <Clock className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                   Export CSV
                 </button>
              </div>
              
              {/* KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                {[
                  { label: 'Total Enrolled', value: totalEnrolled },
                  { label: 'Pending Review', value: pendingApprovals.length, highlight: pendingApprovals.length > 0 },
                  { label: 'Approved', value: totalApproved }
                ].map((stat, i) => (
                  <div key={i} className="bg-white/60 backdrop-blur-md border border-white/80 p-4 rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">{stat.label}</div>
                    <div className={`text-2xl font-black ${stat.highlight ? 'text-yellow-600' : 'text-slate-900'}`}>{stat.value}</div>
                  </div>
                ))}
              </div>

              {/* Filters */}
              <div className="flex flex-col sm:flex-row gap-3 mb-4">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input 
                    type="text" 
                    placeholder="Search demo drivers..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 rounded-xl border border-white/60 bg-white/50 backdrop-blur-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#00c853]/50"
                  />
                </div>
                <select 
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 rounded-xl border border-white/60 bg-white/50 backdrop-blur-sm text-sm font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#00c853]/50 appearance-none outline-none"
                >
                  <option value="ALL">All Status</option>
                  <option value="APPROVED">Approved</option>
                  <option value="PENDING_APPROVAL">Pending Review</option>
                  <option value="PENDING_DOCUMENTS">Missing Docs</option>
                </select>
              </div>

              {/* Table / Cards */}
              <div className="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl overflow-hidden shadow-[0_4px_16px_rgba(0,0,0,0.02)] flex-1">
                {/* Desktop Table */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-white/40 border-b border-white/60 text-slate-500">
                      <tr>
                        <th className="p-4 font-bold tracking-wide">Driver</th>
                        <th className="p-4 font-bold tracking-wide">Status</th>
                        <th className="p-4 font-bold tracking-wide">Documents</th>
                        <th className="p-4 font-bold tracking-wide text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/40">
                      {filteredDrivers.length > 0 ? filteredDrivers.map((row) => (
                        <tr key={row.id} className="hover:bg-white/80 transition-colors cursor-pointer group" onClick={() => setSelectedDriver(row)}>
                          <td className="p-4">
                            <div className="font-bold text-slate-900 group-hover:text-[#00c853] transition-colors">{row.name}</div>
                            <div className="text-[10px] font-bold text-slate-500">{row.id}</div>
                          </td>
                          <td className="p-4">{getStatusBadge(row.verification_status)}</td>
                          <td className="p-4 text-slate-600 font-medium text-xs">
                            {row.documents.filter(d => d.status === 'VERIFIED').length}/{row.documents.length} Verified
                          </td>
                          <td className="p-4 text-right">
                            <button 
                              className="text-xs font-bold text-slate-600 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm"
                              onClick={(e) => { e.stopPropagation(); setSelectedDriver(row); }}
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      )) : (
                        <tr><td colSpan={4} className="p-8 text-center text-slate-500 font-bold">No drivers found matching criteria.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
                
                {/* Mobile Cards */}
                <div className="md:hidden flex flex-col divide-y divide-white/40">
                  {filteredDrivers.length > 0 ? filteredDrivers.map((row) => (
                    <div key={row.id} className="p-4 active:bg-white/80 transition-colors cursor-pointer" onClick={() => setSelectedDriver(row)}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-bold text-slate-900 text-sm">{row.name}</div>
                          <div className="text-[10px] font-bold text-slate-500">{row.id}</div>
                        </div>
                        {getStatusBadge(row.verification_status)}
                      </div>
                      <div className="flex justify-between items-center mt-3">
                         <div className="text-xs text-slate-600 font-medium">Docs: {row.documents.filter(d => d.status === 'VERIFIED').length}/{row.documents.length}</div>
                         <div className="text-xs font-bold text-[#00c853] flex items-center gap-1">Details <ChevronRight className="w-3 h-3" /></div>
                      </div>
                    </div>
                  )) : (
                    <div className="p-8 text-center text-slate-500 font-bold text-sm">No drivers found.</div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* APPROVALS VIEW */}
          {activeTab === 'approvals' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
               <div className="mb-6">
                 <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">Pending Approvals</h3>
                 <p className="text-sm text-slate-600 font-medium mt-1">Review driver profiles and verify submitted documents.</p>
               </div>

               <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                 {pendingApprovals.length > 0 ? pendingApprovals.map(driver => (
                   <div key={driver.id} className="bg-white/70 backdrop-blur-xl border border-white/80 p-5 rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow">
                     <div className="flex justify-between items-start mb-4">
                       <div>
                         <h4 className="font-bold text-slate-900">{driver.name}</h4>
                         <span className="text-xs text-slate-500 font-bold">{driver.id}</span>
                       </div>
                       {getStatusBadge(driver.verification_status)}
                     </div>
                     <div className="space-y-2 mb-4">
                       {driver.documents.map(doc => (
                         <div key={doc.id} className="flex items-center justify-between text-xs font-medium">
                           <span className="flex items-center gap-1.5 text-slate-600"><FileText className="w-3.5 h-3.5" /> {doc.type}</span>
                           {doc.status === 'VERIFIED' ? <CheckCircle className="w-3.5 h-3.5 text-[#00c853]" /> : <Clock className="w-3.5 h-3.5 text-yellow-500" />}
                         </div>
                       ))}
                     </div>
                     <button 
                       onClick={() => setSelectedDriver(driver)}
                       className="w-full bg-[#00c853]/10 hover:bg-[#00c853]/20 text-[#00c853] font-bold text-sm py-2 rounded-xl border border-[#00c853]/20 transition-colors"
                     >
                       Review Profile
                     </button>
                   </div>
                 )) : (
                   <div className="col-span-full py-12 text-center bg-white/40 rounded-2xl border border-white/60">
                     <CheckCircle className="w-8 h-8 text-[#00c853] mx-auto mb-3" />
                     <h4 className="font-bold text-slate-900">All caught up!</h4>
                     <p className="text-sm text-slate-500 font-medium">There are no pending driver approvals.</p>
                   </div>
                 )}
               </div>
            </motion.div>
          )}

          {/* DOCUMENTS VIEW */}
          {activeTab === 'documents' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
               <div className="mb-6">
                 <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">Document Repository</h3>
                 <p className="text-sm text-slate-600 font-medium mt-1">All submitted driver documents.</p>
               </div>

               <div className="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl overflow-hidden shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-white/40 border-b border-white/60 text-slate-500">
                        <tr>
                          <th className="p-4 font-bold tracking-wide">Document</th>
                          <th className="p-4 font-bold tracking-wide">Driver</th>
                          <th className="p-4 font-bold tracking-wide">Status</th>
                          <th className="p-4 font-bold tracking-wide text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/40">
                        {allDocuments.map((doc, i) => (
                          <tr key={i} className="hover:bg-white/80 transition-colors">
                            <td className="p-4">
                              <div className="font-bold text-slate-900 flex items-center gap-2"><FileText className="w-4 h-4 text-slate-400" /> {doc.type}</div>
                              <div className="text-[10px] font-bold text-slate-500 ml-6">Uploaded: {doc.date}</div>
                            </td>
                            <td className="p-4">
                              <div className="font-bold text-slate-800">{doc.driverName}</div>
                            </td>
                            <td className="p-4">
                               {doc.status === 'VERIFIED' ? 
                                 <span className="text-[#00c853] font-bold text-[10px] uppercase flex items-center gap-1"><CheckCircle className="w-3 h-3"/> Verified</span> : 
                                 <span className="text-yellow-600 font-bold text-[10px] uppercase flex items-center gap-1"><Clock className="w-3 h-3"/> Pending</span>
                               }
                            </td>
                            <td className="p-4 text-right">
                              <button 
                                onClick={() => setSelectedDocument(doc)}
                                className="text-xs font-bold text-blue-600 bg-blue-50/50 hover:bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 shadow-sm"
                              >
                                View
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
               </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* DRIVER DETAIL MODAL */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {selectedDriver && (
            <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 pointer-events-auto">
               <motion.div 
                 initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                 className="fixed inset-0 bg-[#0a141e]/30 backdrop-blur-[12px]"
                 onClick={() => !isActionLoading && setSelectedDriver(null)}
               />
               <motion.div 
                 initial={{ opacity: 0, scale: 0.95, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 10 }} transition={{ duration: 0.2 }}
                 className="bg-white/80 backdrop-blur-3xl border border-white/60 shadow-[0_20px_60px_rgba(0,0,0,0.1),_0_0_40px_rgba(0,200,83,0.05)] w-full max-w-[720px] max-h-[calc(100vh-20px)] sm:max-h-[calc(100vh-40px)] overflow-y-auto relative z-10 flex flex-col rounded-[20px] sm:rounded-[24px]"
               >
                  <div className="p-5 sm:p-6 border-b border-white/60 flex justify-between items-start sticky top-0 bg-white/70 backdrop-blur-2xl z-30">
                     <div>
                       <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900">{selectedDriver.name}</h2>
                       <p className="text-sm font-bold text-slate-500 mt-1">ID: {selectedDriver.id} • {selectedDriver.phone}</p>
                     </div>
                     <button onClick={() => !isActionLoading && setSelectedDriver(null)} className="w-9 h-9 flex items-center justify-center bg-white/80 hover:bg-white rounded-full transition-colors disabled:opacity-50 border border-slate-200/50 hover:border-slate-300 shadow-sm" disabled={isActionLoading}>
                       <X className="w-5 h-5 text-slate-600" />
                     </button>
                  </div>

                  <div className="p-5 sm:p-6 space-y-6 flex-1">
                     <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white/50 backdrop-blur-sm p-4 rounded-2xl border border-white shadow-sm">
                           <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Status</div>
                           <div>{getStatusBadge(selectedDriver.verification_status)}</div>
                        </div>
                        <div className="bg-white/50 backdrop-blur-sm p-4 rounded-2xl border border-white shadow-sm">
                           <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Onboarding Date</div>
                           <div className="font-bold text-slate-800 text-sm">{selectedDriver.date}</div>
                        </div>
                     </div>

                     <div>
                        <h4 className="text-xs font-bold text-slate-500 mb-3 uppercase tracking-wider">Submitted Documents</h4>
                        <div className="space-y-3">
                           {selectedDriver.documents.map(doc => (
                             <div key={doc.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-white/60 backdrop-blur-md border border-white/80 rounded-xl shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:shadow-md hover:border-[#00c853]/40 transition-all cursor-pointer group gap-3" onClick={() => setSelectedDocument({ ...doc, driverName: selectedDriver.name })}>
                                <div className="flex items-center gap-3">
                                   <div className="p-2.5 bg-white shadow-sm border border-slate-100 rounded-lg group-hover:bg-[#00c853]/10 group-hover:border-[#00c853]/20 transition-colors">
                                      <FileText className="w-5 h-5 text-slate-500 group-hover:text-[#00c853]" />
                                   </div>
                                   <span className="font-bold text-sm text-slate-800">{doc.type}</span>
                                </div>
                                <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto">
                                   {doc.status === 'VERIFIED' ? <span className="bg-[#00c853]/10 text-[#00c853] border border-[#00c853]/20 px-2.5 py-1 rounded-full text-[10px] font-black tracking-wide uppercase flex items-center gap-1.5"><CheckCircle className="w-3 h-3" /> Verified</span> : <span className="bg-yellow-500/10 text-yellow-700 border border-yellow-500/20 px-2.5 py-1 rounded-full text-[10px] font-black tracking-wide uppercase flex items-center gap-1.5"><Clock className="w-3 h-3" /> Pending</span>}
                                   <button className="flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white hover:text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition-colors group-hover:border-blue-200">
                                      <Eye className="w-4 h-4" /> View
                                   </button>
                                </div>
                             </div>
                           ))}
                        </div>
                     </div>
                  </div>

                  <div className="p-5 sm:p-6 border-t border-white/60 bg-white/70 backdrop-blur-2xl sticky bottom-0 flex flex-col-reverse sm:flex-row justify-end gap-3 z-30">
                     <button onClick={() => !isActionLoading && setSelectedDriver(null)} className="w-full sm:w-auto px-5 py-3 sm:py-2.5 rounded-xl font-bold text-slate-600 bg-white/80 border border-white hover:bg-white shadow-sm transition-colors disabled:opacity-50" disabled={isActionLoading}>
                       Cancel
                     </button>
                     {selectedDriver.verification_status !== 'REJECTED' && (
                       <button 
                         onClick={() => handleReject(selectedDriver.id)}
                         disabled={isActionLoading || selectedDriver.verification_status === 'APPROVED'}
                         className="w-full sm:w-auto px-5 py-3 sm:py-2.5 rounded-xl font-bold text-red-600 bg-red-50/80 border border-red-100 hover:bg-red-100 transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
                       >
                         {isActionLoading ? <Clock className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />} Reject
                       </button>
                     )}
                     {selectedDriver.verification_status !== 'APPROVED' && (
                       <button 
                         onClick={() => handleApprove(selectedDriver.id)}
                         disabled={isActionLoading || selectedDriver.verification_status === 'REJECTED'}
                         className="w-full sm:w-auto px-6 py-3 sm:py-2.5 rounded-xl font-bold text-white bg-gradient-to-b from-[#00c853] to-[#00b048] hover:to-[#00a040] border border-[#00e05d]/30 shadow-[0_4px_15px_rgba(0,200,83,0.3)] hover:shadow-[0_6px_20px_rgba(0,200,83,0.4)] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                       >
                         {isActionLoading ? <Clock className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />} Approve Driver
                       </button>
                     )}
                  </div>
               </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}

      {/* DOCUMENT VIEWER MODAL */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {selectedDocument && (
            <div className="fixed inset-0 z-[10000] flex items-center justify-center p-3 sm:p-8 pointer-events-auto">
               <motion.div 
                 initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}
                 className="fixed inset-0 bg-[#0a141e]/80 backdrop-blur-md"
                 onClick={() => setSelectedDocument(null)}
               />
               <motion.div 
                 initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.2 }}
                 className="bg-slate-900 border border-slate-700 shadow-2xl w-full max-w-2xl max-h-[calc(100vh-20px)] sm:max-h-[calc(100vh-40px)] overflow-hidden relative z-10 flex flex-col rounded-[20px] sm:rounded-[32px]"
               >
                  <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900 sticky top-0 z-20">
                     <div className="flex items-center gap-3 text-white">
                        <FileText className="w-5 h-5 text-slate-400" />
                        <div>
                          <h3 className="font-bold text-sm">{selectedDocument.type}</h3>
                          <p className="text-[10px] text-slate-400">Demo Asset • {selectedDocument.driverName}</p>
                        </div>
                     </div>
                     <button onClick={() => setSelectedDocument(null)} className="w-9 h-9 flex items-center justify-center bg-slate-800 hover:bg-slate-700 rounded-full transition-colors border border-slate-700">
                       <X className="w-5 h-5 text-slate-400" />
                     </button>
                  </div>
                  
                  {/* Safe Demo Asset Display */}
                  <div className="p-6 sm:p-8 bg-slate-950 flex flex-col items-center justify-center min-h-[300px] overflow-y-auto flex-1">
                     <div className="w-full max-w-sm aspect-[1.6/1] bg-slate-800 rounded-2xl border-2 border-dashed border-slate-700 flex flex-col items-center justify-center relative overflow-hidden">
                        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white to-transparent" />
                        <ShieldCheck className="w-12 h-12 text-slate-600 mb-3" />
                        <span className="text-slate-400 font-bold text-sm">Safe Demo Asset View</span>
                        <span className="text-slate-500 text-[10px] mt-1">Production documents are securely protected.</span>
                     </div>
                  </div>
               </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}

    </div>
  );
}
