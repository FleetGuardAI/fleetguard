import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Paperclip, Mic, Send, Sparkles, MessageSquare, Plus, Trash2,
  History, PanelLeftClose, PanelLeft, Clock, Calendar,
  CheckCircle2, XCircle, Truck, MapPin, User, ChevronRight,
  X, AlertTriangle, Loader2
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import MarkdownMessage from '@/components/shared/MarkdownMessage';
import IntelligenceFindingCard from '@/components/shared/IntelligenceFindingCard';
import { useCopilotConversation } from '@/hooks/useCopilotConversation';

const SUGGESTED_PROMPTS = [
  "Show me the fleet health overview",
  "Where are both my trucks?",
  "Schedule a trip for Truck 02 tomorrow",
  "Which vehicles need maintenance?",
  "Show me yesterday's fuel anomalies"
];

function formatRelativeTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now - d;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay === 1) return 'Yesterday';
  if (diffDay < 7) return `${diffDay}d ago`;
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// ── Message Types ──
function ChatMessageBubble({ message, onAction }) {
  const isUser = message.role === 'user';
  const metadata = message.metadata || {};
  const proposals = metadata.proposals || [];
  const locations = metadata.locations || [];
  const drivers = metadata.drivers || [];
  const verifiedTrip = metadata.verified_trip;
  const findings = metadata.intelligence_findings || [];

  const textContent = typeof message.content === 'object' ? message.content?.text : message.content;
  const hasStructuredCards = locations.length > 0 || proposals.length > 0 || drivers.length > 0 || findings.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
      className={cn('flex gap-3 max-w-[88%]', isUser ? 'ml-auto flex-row-reverse' : '')}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-fg-green-deep flex items-center justify-center flex-shrink-0 mt-1 border border-fg-green/20">
          <Sparkles className="w-4 h-4 text-fg-green" />
        </div>
      )}

      {/* Bubble */}
      <div className={cn(
        'px-4 py-3 max-w-full rounded-2xl shadow-sm border backdrop-blur-md space-y-2.5',
        isUser
          ? 'bg-fg-green/10 border-fg-green/20 text-content rounded-br-sm'
          : 'bg-surface/50 border-border text-content rounded-bl-sm'
      )}>
        {/* Message content */}
        {textContent && (
          isUser ? (
            <div className="text-sm leading-relaxed whitespace-pre-wrap font-light">
              {textContent}
            </div>
          ) : (
            <MarkdownMessage content={textContent} suppressTables={hasStructuredCards} />
          )
        )}

        {/* ── Interactive GPS Location Cards ── */}
        {locations.length > 0 && (
          <div className="space-y-2 pt-1">
            {locations.map((loc, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-border/80 bg-white shadow-xs text-content"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Truck className="w-4 h-4 text-brand-500" />
                    <span className="text-xs font-bold font-mono text-content">{loc.registration_number}</span>
                    {loc.make_model && (
                      <span className="text-[11px] text-content-secondary">({loc.make_model})</span>
                    )}
                  </div>
                  <span className={cn(
                    "text-[10px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1",
                    loc.freshness === "FRESH"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : loc.freshness === "STALE"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : loc.freshness === "VERY_STALE"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : loc.freshness === "FUTURE_TIMESTAMP"
                      ? "bg-purple-50 text-purple-700 border-purple-200"
                      : "bg-slate-100 text-slate-600 border-slate-200"
                  )}>
                    <span className={cn(
                      "w-1.5 h-1.5 rounded-full",
                      loc.freshness === "FRESH" ? "bg-emerald-500 animate-pulse" :
                      loc.freshness === "STALE" ? "bg-amber-500" :
                      loc.freshness === "VERY_STALE" ? "bg-rose-500" :
                      loc.freshness === "FUTURE_TIMESTAMP" ? "bg-purple-500" : "bg-slate-400"
                    )} />
                    {loc.freshness_label || (
                      loc.freshness === "FRESH" ? "Live GPS" :
                      loc.freshness === "STALE" ? "Last-Known (Stale)" :
                      loc.freshness === "VERY_STALE" ? "Last-Known (Very Stale)" :
                      loc.freshness === "FUTURE_TIMESTAMP" ? "Invalid Timestamp" : "Unavailable"
                    )}
                  </span>
                </div>

                {loc.has_location ? (
                  <div className="space-y-1.5 text-xs text-content-secondary">
                    <div className="flex items-center gap-1.5 text-content">
                      <MapPin className={cn(
                        "w-3.5 h-3.5 flex-shrink-0",
                        loc.freshness === "FRESH" ? "text-emerald-500" : "text-amber-500"
                      )} />
                      <span className="text-[11px] font-medium text-content-secondary">
                        {loc.freshness === "FRESH" ? "Current Position:" : "Last-Known Position:"}
                      </span>
                      <span className="font-mono text-[11px] font-medium">{loc.latitude?.toFixed(4)}, {loc.longitude?.toFixed(4)}</span>
                    </div>
                    {loc.timestamp && (
                      <div className="flex items-center gap-1.5 text-[11px]">
                        <Clock className="w-3 h-3 text-content-muted" />
                        <span>
                          Recorded: {loc.freshness === "FRESH"
                            ? new Date(loc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                            : `${new Date(loc.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })} at ${new Date(loc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                          } ({loc.source})
                        </span>
                      </div>
                    )}
                    {loc.assigned_driver && (
                      <div className="flex items-center gap-1.5 text-[11px]">
                        <User className="w-3 h-3 text-content-muted" />
                        <span>Driver: {loc.assigned_driver}</span>
                      </div>
                    )}
                    {loc.freshness === "VERY_STALE" && (
                      <div className="flex items-center gap-1.5 text-[11px] text-rose-700 bg-rose-50/80 px-2.5 py-1 rounded-lg border border-rose-200/60 mt-1">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-rose-600" />
                        <span>Device inactive or offline. Displaying last-known historical position from {loc.age_seconds ? `${Math.round(loc.age_seconds / 3600)}h ago` : 'past records'}.</span>
                      </div>
                    )}
                    {loc.freshness === "STALE" && (
                      <div className="flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50/80 px-2.5 py-1 rounded-lg border border-amber-200/60 mt-1">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-amber-600" />
                        <span>Last-known position. Telemetry delayed ({loc.age_seconds ? `${Math.round(loc.age_seconds / 60)} min ago` : 'stale'}).</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-content-muted italic">
                    {loc.message || "Location Unavailable: No GPS telemetry recorded for this vehicle."}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── Structured Driver Availability Cards ── */}
        {drivers.length > 0 && (
          <div className="space-y-2 pt-1">
            {drivers.map((drv, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-border/80 bg-white shadow-xs text-content">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4 text-brand-500" />
                    <span className="text-xs font-bold text-content">{drv.name}</span>
                    {drv.employee_id && (
                      <span className="text-[10px] font-mono text-content-secondary">({drv.employee_id})</span>
                    )}
                  </div>
                  <span className={cn(
                    "text-[10px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1",
                    drv.is_available
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : drv.availability_status === "BUSY_ON_TRIP"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : "bg-slate-100 text-slate-600 border-slate-200"
                  )}>
                    <span className={cn(
                      "w-1.5 h-1.5 rounded-full",
                      drv.is_available ? "bg-emerald-500" : drv.availability_status === "BUSY_ON_TRIP" ? "bg-amber-500" : "bg-slate-400"
                    )} />
                    {drv.is_available ? "Available" : drv.availability_status === "BUSY_ON_TRIP" ? "On Trip" : "Inactive"}
                  </span>
                </div>
                {drv.active_trip && (
                  <div className="text-[11px] text-content-secondary flex items-center gap-1.5 mt-1">
                    <Truck className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                    <span>Active Route: <strong className="font-mono text-content">{drv.active_trip.business_id}</strong> ({drv.active_trip.route})</span>
                  </div>
                )}
                {drv.phone_number && (
                  <div className="text-[11px] text-content-secondary mt-0.5">
                    Contact: <span className="font-mono">{drv.phone_number}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}


        {/* ── Structured Trip Proposal Card (Pending Confirmation) ── */}
        {proposals.map((prop, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl border border-brand-200 bg-brand-50/40 text-content space-y-2.5 mt-2"
          >
            <div className="flex items-center justify-between pb-2 border-b border-brand-100">
              <span className="text-xs font-semibold text-brand-700 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-brand-600" /> Trip Proposal
              </span>
              <span className="text-[10px] font-mono bg-brand-100 text-brand-800 px-2 py-0.5 rounded font-bold">
                {prop.proposal_id}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[10px] text-content-secondary uppercase block">Route</span>
                <span className="font-medium text-content">{prop.summary?.origin} → {prop.summary?.destination}</span>
              </div>
              <div>
                <span className="text-[10px] text-content-secondary uppercase block">Vehicle</span>
                <span className="font-medium text-content">{prop.summary?.vehicle}</span>
              </div>
              <div>
                <span className="text-[10px] text-content-secondary uppercase block">Driver</span>
                <span className="font-medium text-content">{prop.summary?.driver || 'Unassigned'}</span>
              </div>
              <div>
                <span className="text-[10px] text-content-secondary uppercase block">Departure</span>
                <span className="font-medium text-content">
                  {prop.summary?.planned_departure ? new Date(prop.summary.planned_departure).toLocaleString() : 'Pending'}
                </span>
              </div>
            </div>

            {/* Explicit Confirmation / Cancellation Actions */}
            <div className="flex items-center gap-2 pt-2 border-t border-brand-100">
              <button
                onClick={() => onAction && onAction(`Confirm trip ${prop.proposal_id}`)}
                className="flex-1 py-1.5 px-3 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-sm cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> Confirm & Schedule Trip
              </button>
              <button
                onClick={() => onAction && onAction(`Cancel trip proposal ${prop.proposal_id}`)}
                className="py-1.5 px-3 bg-white hover:bg-surface-secondary border border-border text-content-secondary rounded-lg text-xs font-medium transition-colors cursor-pointer"
              >
                <XCircle className="w-3.5 h-3.5" /> Cancel
              </button>
            </div>
          </div>
        ))}

        {/* ── Verified Action State ── */}
        {verifiedTrip && (
          <div className="p-3.5 rounded-xl border border-emerald-300 bg-emerald-50/50 text-content space-y-1.5 mt-2">
            <div className="flex items-center gap-2 text-emerald-800 font-semibold text-xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Verified Database Trip Scheduled: {verifiedTrip.business_id}
            </div>
            <div className="text-xs text-emerald-950/80 space-y-0.5">
              <p><span className="font-medium">Route:</span> {verifiedTrip.origin} → {verifiedTrip.destination}</p>
              <p><span className="font-medium">Vehicle:</span> {verifiedTrip.vehicle}</p>
              <p><span className="font-medium">Status:</span> <span className="font-mono bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded text-[10px] font-bold">{verifiedTrip.operational_status}</span></p>
            </div>
          </div>
        )}

        {/* ── Evidence-Grounded Fleet Intelligence Findings ── */}
        {findings.length > 0 && (
          <div className="space-y-2 pt-1">
            {findings.map((f, idx) => (
              <IntelligenceFindingCard
                key={f.finding_id || idx}
                finding={f}
                onAction={(fnd) => onAction && onAction(`Inspect ${fnd.title}`)}
              />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ── Typing Indicator ──
function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex gap-3 max-w-[85%]"
    >
      <div className="w-8 h-8 rounded-full bg-fg-green-deep flex items-center justify-center flex-shrink-0 mt-1 border border-fg-green/20">
        <Sparkles className="w-4 h-4 text-fg-green" />
      </div>
      <div className="fg-chat-ai px-4 py-3.5 flex items-center gap-1.5">
        <div className="fg-typing-dot" />
        <div className="fg-typing-dot" />
        <div className="fg-typing-dot" />
      </div>
    </motion.div>
  );
}

// ── Main ChatBox Page ──
export default function ChatBox() {
  const { t } = useLanguage();
  const location = useLocation();
  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [convToDelete, setConvToDelete] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const {
    conversations,
    activeConversationId,
    messages,
    isLoading,
    isLoadingHistory,
    isTyping,
    selectConversation,
    startNewChat,
    sendMessage,
    deleteConversation,
    clearAllConversations,
  } = useCopilotConversation();

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const [user, setUser] = useState(null);
  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
    if (cached) setUser(JSON.parse(cached));
  }, []);

  const handleSend = useCallback(async (text) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    setInput('');
    const context = location.state?.context || null;
    await sendMessage(messageText, context);
  }, [input, location.state, sendMessage]);

  // Handle initial message from search bar navigation
  const initialMessageSent = useRef(false);
  useEffect(() => {
    if (location.state?.initialMessage && !initialMessageSent.current) {
      initialMessageSent.current = true;
      handleSend(location.state.initialMessage);
      window.history.replaceState({}, document.title);
    }
  }, [location.state, handleSend]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePromptClick = (prompt) => {
    setInput(prompt);
    setTimeout(() => handleSend(prompt), 150);
  };

  const handleDeleteConfirm = async () => {
    if (!convToDelete) return;
    try {
      await deleteConversation(convToDelete.id);
    } catch (err) {
      console.error(err);
    } finally {
      setConvToDelete(null);
    }
  };

  const handleClearAllConfirm = async () => {
    try {
      await clearAllConversations();
    } catch (err) {
      console.error(err);
    } finally {
      setShowClearConfirm(false);
    }
  };

  const userName = user?.name || 'Owner';
  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-80px)] w-full max-w-7xl mx-auto overflow-hidden rounded-2xl border border-border/50 shadow-sm bg-surface/20 backdrop-blur-md">
      {/* ═══════════ HISTORY SIDEBAR ═══════════ */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="h-full flex flex-col border-r border-border/60 bg-surface/60 backdrop-blur-xl flex-shrink-0 overflow-hidden"
          >
            {/* Sidebar Header */}
            <div className="p-3.5 border-b border-border/40 flex items-center justify-between gap-2">
              <button
                onClick={startNewChat}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                {t("New Chat")}
              </button>
              <button
                onClick={() => setSidebarOpen(false)}
                title="Collapse History"
                className="p-2 rounded-xl text-content-secondary hover:bg-surface-secondary hover:text-content transition-colors cursor-pointer"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto fg-scrollbar p-2 space-y-1">
              <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-content-muted flex items-center gap-1.5">
                <History className="w-3.5 h-3.5" />
                {t("Past Conversations")}
              </div>

              {isLoadingHistory ? (
                <div className="flex items-center justify-center py-8 text-content-muted text-xs gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                  <span>Loading history...</span>
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 px-3 text-content-muted text-xs space-y-1">
                  <MessageSquare className="w-6 h-6 mx-auto opacity-30" />
                  <p>No past conversations</p>
                  <p className="text-[10px]">Start a conversation to see it saved here.</p>
                </div>
              ) : (
                conversations.map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <div
                      key={conv.id}
                      className={cn(
                        "group relative flex items-center justify-between rounded-xl px-2.5 py-2 text-xs transition-all cursor-pointer",
                        isActive
                          ? "bg-brand-500/10 border border-brand-500/30 text-brand-700 font-medium shadow-xs"
                          : "hover:bg-surface-secondary/80 text-content border border-transparent"
                      )}
                      onClick={() => selectConversation(conv.id)}
                    >
                      <div className="flex items-center gap-2 truncate pr-6">
                        <MessageSquare className={cn("w-3.5 h-3.5 flex-shrink-0", isActive ? "text-brand-600" : "text-content-muted")} />
                        <div className="truncate">
                          <span className="truncate block font-medium">
                            {conv.title || "Untitled Conversation"}
                          </span>
                          <span className="text-[10px] text-content-muted block font-normal">
                            {formatRelativeTime(conv.updated_at || conv.created_at)}
                          </span>
                        </div>
                      </div>

                      {/* Delete Action */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConvToDelete(conv);
                        }}
                        title="Delete conversation"
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-content-muted hover:text-rose-600 hover:bg-rose-50 transition-all cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            {/* Sidebar Footer */}
            {conversations.length > 0 && (
              <div className="p-2 border-t border-border/40">
                <button
                  onClick={() => setShowClearConfirm(true)}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[11px] text-content-muted hover:text-rose-600 hover:bg-rose-50/50 rounded-lg transition-colors cursor-pointer"
                >
                  <Trash2 className="w-3 h-3" />
                  {t("Clear All History")}
                </button>
              </div>
            )}
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ═══════════ MAIN CHAT CONTAINER ═══════════ */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-transparent">
        {/* ── Top Header ── */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/40 flex-shrink-0 bg-surface/30 backdrop-blur-md">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                title="Open History"
                className="p-2 rounded-xl text-content-secondary hover:bg-surface-secondary hover:text-content transition-colors cursor-pointer mr-1"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            )}

            <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center border border-brand-100">
              <img src="/assets/the_vahan_logo.png" alt="the vahan" className="w-5 h-5 object-contain" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-content">{t("AI Co-Pilot")}</h1>
                <span className="text-[10px] text-brand-600 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded-lg font-medium">
                  the vahan Intelligence
                </span>
              </div>
              <p className="text-[11px] text-content-secondary">{t("Data-grounded fleet operations and safe operational execution assistant")}</p>
            </div>
          </div>

          <button
            onClick={startNewChat}
            className="flex items-center gap-1.5 text-xs text-content-secondary hover:text-brand-600 py-1.5 px-3 rounded-lg border border-border/60 hover:border-brand-300 transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t("New Chat")}</span>
          </button>
        </div>

        {/* ── Messages Scroll Area ── */}
        <div className="flex-1 overflow-y-auto fg-scrollbar relative px-6 py-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-full text-content-muted gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
              <p className="text-xs">Restoring conversation messages...</p>
            </div>
          ) : isEmpty ? (
            /* ── Empty State ── */
            <div className="flex flex-col items-center justify-center h-full relative">
              <div className="relative z-10 text-center space-y-3 max-w-lg">
                <h2 className="text-2xl font-light text-content">
                  {t("How can I assist your fleet today,")}{' '}
                  <span className="font-semibold">{userName}</span>?
                </h2>
                <p className="text-xs text-content-secondary font-light">
                  {t("Ask about vehicle locations, driver status, trips, fuel metrics, or schedule a verified trip.")}
                </p>
              </div>

              <div className="relative z-10 flex flex-wrap gap-2.5 justify-center mt-8 max-w-2xl px-4">
                {SUGGESTED_PROMPTS.map((prompt, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + i * 0.08 }}
                    onClick={() => handlePromptClick(prompt)}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-surface/50 backdrop-blur-md border border-border text-xs text-content-secondary hover:text-content hover:bg-surface-secondary/80 hover:shadow-fg-glow transition-all duration-300 cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3 text-brand-500" />
                    {prompt}
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            /* ── Chat Messages ── */
            <div className="space-y-5 max-w-4xl mx-auto py-2">
              {messages.map((msg) => (
                <ChatMessageBubble key={msg.id} message={msg} onAction={handleSend} />
              ))}
              <AnimatePresence>
                {isTyping && <TypingIndicator />}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* ── Input Bar ── */}
        <div className="flex-shrink-0 px-6 pt-3 pb-4 space-y-2 border-t border-border/40 bg-surface/40 backdrop-blur-md">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 bg-surface/80 backdrop-blur-xl border border-border rounded-2xl px-4 py-3
              focus-within:border-brand-400 focus-within:shadow-[0_0_20px_rgba(34,197,94,0.15)] transition-all duration-300">
              <button className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-secondary transition-colors flex-shrink-0">
                <Paperclip className="w-4 h-4" />
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t("Ask where trucks are, request fleet status, or schedule a trip...")}
                rows={1}
                className="flex-1 bg-transparent border-none outline-none text-sm text-content placeholder:text-content-muted font-light resize-none leading-relaxed max-h-24 overflow-y-auto"
                style={{ minHeight: '20px' }}
              />
              <button className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-secondary transition-colors flex-shrink-0">
                <Mic className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() && !isTyping}
                className={cn(
                  'p-2.5 rounded-xl transition-all duration-200 flex-shrink-0',
                  input.trim()
                    ? 'bg-brand-500 hover:bg-brand-600 text-white cursor-pointer shadow-sm'
                    : 'bg-surface-secondary text-content-muted cursor-not-allowed'
                )}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[10px] text-content-muted text-center font-light mt-1.5">
              {t("Fleetguard AI retrieves authoritative fleet records and requires explicit confirmation for operational actions.")}
            </p>
          </div>
        </div>
      </div>

      {/* ═══════════ CONFIRMATION MODALS ═══════════ */}
      {/* Delete Single Conversation */}
      <AnimatePresence>
        {convToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-5 max-w-sm w-full shadow-2xl border border-border space-y-4"
            >
              <div className="flex items-center gap-3 text-rose-600">
                <div className="w-9 h-9 rounded-xl bg-rose-50 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-rose-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-content">Delete Conversation</h3>
                  <p className="text-xs text-content-muted">This cannot be undone.</p>
                </div>
              </div>
              <p className="text-xs text-content-secondary">
                Are you sure you want to delete <span className="font-semibold text-content">"{convToDelete.title || 'Untitled'}"</span>? All messages in this conversation will be permanently removed.
              </p>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  onClick={() => setConvToDelete(null)}
                  className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium text-content hover:bg-surface-secondary transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Clear All History Modal */}
      <AnimatePresence>
        {showClearConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-5 max-w-sm w-full shadow-2xl border border-border space-y-4"
            >
              <div className="flex items-center gap-3 text-rose-600">
                <div className="w-9 h-9 rounded-xl bg-rose-50 flex items-center justify-center">
                  <Trash2 className="w-5 h-5 text-rose-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-content">Clear All Conversations</h3>
                  <p className="text-xs text-content-muted">Permanent action</p>
                </div>
              </div>
              <p className="text-xs text-content-secondary">
                Are you sure you want to clear all your past AI Co-Pilot conversations? This will delete all saved transcripts for your account.
              </p>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium text-content hover:bg-surface-secondary transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClearAllConfirm}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                >
                  Clear All
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
