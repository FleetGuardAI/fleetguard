import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Paperclip, Mic, Send, Sparkles, MessageSquare, Plus, Trash2,
  History, Clock, Calendar, CheckCircle2, XCircle, Truck,
  MapPin, User, ChevronRight, X, AlertTriangle, Loader2, ArrowLeft
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import MarkdownMessage from '@/components/shared/MarkdownMessage';
import { useCopilotConversation } from '@/hooks/useCopilotConversation';

const SUGGESTED_PROMPTS = [
  "Show me the fleet health overview",
  "Where are both my trucks?",
  "Schedule a trip for Truck 02 tomorrow",
  "Which vehicles need maintenance?"
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
  const verifiedTrip = metadata.verified_trip;

  const textContent = typeof message.content === 'object' ? message.content?.text : message.content;

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
        'px-4 py-3 max-w-full rounded-2xl shadow-sm border backdrop-blur-md space-y-2',
        isUser
          ? 'bg-fg-green/10 border-fg-green/20 text-content rounded-br-sm'
          : 'bg-surface/50 border-border text-content rounded-bl-sm'
      )}>
        {textContent && (
          isUser ? (
            <div className="text-sm leading-relaxed whitespace-pre-wrap font-light">
              {textContent}
            </div>
          ) : (
            <MarkdownMessage content={textContent} />
          )
        )}

        {/* GPS Telemetry Cards */}
        {locations.length > 0 && (
          <div className="space-y-2 pt-1">
            {locations.map((loc, idx) => (
              <div key={idx} className="p-2.5 rounded-xl border border-border/70 bg-white text-content">
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5">
                    <Truck className="w-3.5 h-3.5 text-brand-500" />
                    <span className="text-xs font-bold font-mono">{loc.registration_number}</span>
                  </div>
                  <span className={cn(
                    "text-[9px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1",
                    loc.freshness === "FRESH" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                    loc.freshness === "STALE" ? "bg-amber-50 text-amber-700 border-amber-200" :
                    loc.freshness === "VERY_STALE" ? "bg-rose-50 text-rose-700 border-rose-200" :
                    loc.freshness === "FUTURE_TIMESTAMP" ? "bg-purple-50 text-purple-700 border-purple-200" :
                    "bg-slate-100 text-slate-600 border-slate-200"
                  )}>
                    <span className={cn(
                      "w-1 h-1 rounded-full",
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
                  <div className="space-y-0.5 text-[11px] text-content-secondary">
                    <div className="flex items-center gap-1">
                      <MapPin className={cn(
                        "w-3 h-3",
                        loc.freshness === "FRESH" ? "text-emerald-500" : "text-amber-500"
                      )} />
                      <span className="text-[10px] text-content-secondary font-medium">
                        {loc.freshness === "FRESH" ? "Current GPS:" : "Last-Known Position:"}
                      </span>
                      <span>{loc.latitude?.toFixed(4)}, {loc.longitude?.toFixed(4)}</span>
                    </div>
                    {loc.timestamp && (
                      <div className="flex items-center gap-1 text-[10px] text-content-muted">
                        <Clock className="w-2.5 h-2.5" />
                        <span>Recorded: {new Date(loc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} ({loc.source})</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-[11px] text-content-muted italic">{loc.message || "Location Unavailable: No GPS telemetry recorded."}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Proposals */}
        {proposals.map((prop, idx) => (
          <div key={idx} className="p-3 rounded-xl border border-brand-200 bg-brand-50/50 text-content space-y-2 mt-1.5">
            <div className="flex items-center justify-between border-b border-brand-100 pb-1.5">
              <span className="text-[11px] font-semibold text-brand-700 uppercase flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Trip Proposal
              </span>
              <span className="text-[9px] font-mono bg-brand-100 text-brand-800 px-1.5 py-0.5 rounded font-bold">
                {prop.proposal_id}
              </span>
            </div>
            <div className="text-[11px] space-y-0.5">
              <p><span className="text-content-secondary">Route:</span> <span className="font-medium">{prop.summary?.origin} → {prop.summary?.destination}</span></p>
              <p><span className="text-content-secondary">Vehicle:</span> <span className="font-medium">{prop.summary?.vehicle}</span></p>
              <p><span className="text-content-secondary">Driver:</span> <span className="font-medium">{prop.summary?.driver || 'Unassigned'}</span></p>
            </div>
            <div className="flex items-center gap-1.5 pt-1.5 border-t border-brand-100">
              <button
                onClick={() => onAction && onAction(`Confirm trip ${prop.proposal_id}`)}
                className="flex-1 py-1 px-2.5 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors cursor-pointer"
              >
                <CheckCircle2 className="w-3 h-3" /> Confirm Trip
              </button>
              <button
                onClick={() => onAction && onAction(`Cancel trip proposal ${prop.proposal_id}`)}
                className="py-1 px-2.5 bg-white border border-border text-content-secondary rounded-lg text-[11px] hover:bg-surface-secondary transition-colors cursor-pointer"
              >
                <XCircle className="w-3 h-3" /> Cancel
              </button>
            </div>
          </div>
        ))}

        {/* Verified Trip */}
        {verifiedTrip && (
          <div className="p-2.5 rounded-xl border border-emerald-300 bg-emerald-50/50 text-content space-y-1 mt-1.5">
            <div className="flex items-center gap-1.5 text-emerald-800 font-semibold text-[11px]">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Verified Trip: {verifiedTrip.business_id}
            </div>
            <div className="text-[11px] text-emerald-950/80">
              <p>{verifiedTrip.origin} → {verifiedTrip.destination} ({verifiedTrip.vehicle})</p>
            </div>
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

// ── Main AiCopilot Component ──
export function AiCopilot() {
  const { t } = useLanguage();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [input, setInput] = useState('');
  const [convToDelete, setConvToDelete] = useState(null);

  const {
    conversations,
    activeConversationId,
    messages,
    isLoading,
    isLoadingHistory,
    isTyping,
    loadConversations,
    selectConversation,
    startNewChat,
    sendMessage,
    deleteConversation,
  } = useCopilotConversation();

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const [user, setUser] = useState(null);
  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
    if (cached) setUser(JSON.parse(cached));
  }, []);

  // When drawer opens, refresh conversations list if history open
  useEffect(() => {
    if (isOpen && showHistory) {
      loadConversations();
    }
  }, [isOpen, showHistory, loadConversations]);

  const handleSend = useCallback(async (text) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    setInput('');
    const context = { page: location.pathname };
    await sendMessage(messageText, context);
  }, [input, location.pathname, sendMessage]);

  // Handle initial message from search bar navigation
  const initialMessageSent = useRef(false);
  useEffect(() => {
    if (location.state?.initialMessage && !initialMessageSent.current) {
      initialMessageSent.current = true;
      setIsOpen(true);
      handleSend(location.state.initialMessage);
      window.history.replaceState({}, document.title);
    }
  }, [location.state, handleSend]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (isOpen && !showHistory) {
      scrollToBottom();
    }
  }, [messages, isTyping, isOpen, showHistory, scrollToBottom]);

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

  const userName = user?.name || 'Owner';
  const isEmpty = messages.length === 0;

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-brand-500 rounded-full shadow-lg flex items-center justify-center hover:scale-105 transition-transform z-50 text-white shadow-[0_4px_20px_rgba(34,197,94,0.3)] cursor-pointer"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="fixed bottom-24 right-6 w-[430px] h-[640px] max-h-[85vh] z-50 flex flex-col bg-white border border-border/80 rounded-2xl overflow-hidden shadow-2xl"
          >
            {/* ═══════════ HEADER ═══════════ */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/40 flex-shrink-0 relative z-10 bg-surface/50 backdrop-blur-md">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-brand-50 flex items-center justify-center border border-brand-100">
                  <img src="/assets/the_vahan_logo.png" alt="the vahan" className="w-5 h-5 object-contain" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <h1 className="text-sm font-semibold text-content">{t("AI Co-Pilot")}</h1>
                    <span className="text-[9px] text-brand-600 bg-brand-50 border border-brand-100 px-1.5 py-0.5 rounded font-medium">
                      the vahan AI
                    </span>
                  </div>
                  <p className="text-[10px] text-content-secondary">{t("Fleet operations intelligence")}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => {
                    startNewChat();
                    setShowHistory(false);
                  }}
                  title="New Chat"
                  className="p-1.5 rounded-lg text-content-secondary hover:text-brand-600 hover:bg-surface-secondary transition-colors cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setShowHistory(!showHistory);
                    if (!showHistory) loadConversations();
                  }}
                  title="Conversation History"
                  className={cn(
                    "p-1.5 rounded-lg transition-colors cursor-pointer",
                    showHistory ? "bg-brand-50 text-brand-600" : "text-content-secondary hover:bg-surface-secondary hover:text-content"
                  )}
                >
                  <History className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  title="Close AI Co-Pilot"
                  className="p-1.5 rounded-lg text-content-secondary hover:bg-surface-secondary transition-colors cursor-pointer"
                >
                  <X className="w-4.5 h-4.5" />
                </button>
              </div>
            </div>

            {/* ═══════════ CONTENT (CHAT VS HISTORY) ═══════════ */}
            {showHistory ? (
              /* ── Conversation History Overlay ── */
              <div className="flex-1 flex flex-col overflow-hidden bg-surface/20">
                <div className="p-3 border-b border-border/40 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowHistory(false)}
                      className="p-1 rounded-md text-content-secondary hover:bg-surface-secondary transition-colors cursor-pointer"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <span className="text-xs font-semibold text-content">{t("Past Conversations")}</span>
                  </div>
                  <button
                    onClick={() => {
                      startNewChat();
                      setShowHistory(false);
                    }}
                    className="flex items-center gap-1 text-[11px] text-brand-600 hover:text-brand-700 font-medium cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>New Chat</span>
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto fg-scrollbar p-2 space-y-1">
                  {isLoadingHistory ? (
                    <div className="flex items-center justify-center py-12 text-content-muted text-xs gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                      <span>Loading history...</span>
                    </div>
                  ) : conversations.length === 0 ? (
                    <div className="text-center py-12 px-4 text-content-muted text-xs space-y-1">
                      <MessageSquare className="w-6 h-6 mx-auto opacity-30" />
                      <p>No past conversations found</p>
                    </div>
                  ) : (
                    conversations.map((conv) => {
                      const isActive = conv.id === activeConversationId;
                      return (
                        <div
                          key={conv.id}
                          className={cn(
                            "group flex items-center justify-between rounded-xl px-2.5 py-2 text-xs transition-all cursor-pointer",
                            isActive
                              ? "bg-brand-500/10 border border-brand-500/30 text-brand-700 font-medium shadow-xs"
                              : "hover:bg-surface-secondary/80 text-content border border-transparent"
                          )}
                          onClick={() => {
                            selectConversation(conv.id);
                            setShowHistory(false);
                          }}
                        >
                          <div className="truncate pr-4">
                            <span className="truncate block font-medium">
                              {conv.title || "Untitled Conversation"}
                            </span>
                            <span className="text-[10px] text-content-muted block font-normal">
                              {formatRelativeTime(conv.updated_at || conv.created_at)}
                            </span>
                          </div>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setConvToDelete(conv);
                            }}
                            title="Delete"
                            className="opacity-0 group-hover:opacity-100 p-1 text-content-muted hover:text-rose-600 transition-opacity cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            ) : (
              /* ── Main Chat Area ── */
              <>
                <div className="flex-1 overflow-y-auto fg-scrollbar relative p-3">
                  {isLoading ? (
                    <div className="flex flex-col items-center justify-center h-full text-content-muted gap-2">
                      <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
                      <p className="text-xs">Restoring conversation...</p>
                    </div>
                  ) : isEmpty ? (
                    /* ── Empty State ── */
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-3 px-4">
                      <h2 className="text-base font-light text-content">
                        {t("How can I help you today,")}{' '}
                        <span className="font-semibold">{userName}</span>?
                      </h2>
                      <p className="text-xs text-content-secondary font-light">
                        {t("Ask about truck locations, driver status, or schedule a trip.")}
                      </p>

                      <div className="flex flex-wrap gap-1.5 justify-center mt-3">
                        {SUGGESTED_PROMPTS.map((prompt, i) => (
                          <motion.button
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 + i * 0.08 }}
                            onClick={() => handlePromptClick(prompt)}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-surface/50 border border-border text-[11px] text-content-secondary hover:text-content hover:bg-surface-secondary transition-all cursor-pointer"
                          >
                            <Sparkles className="w-3 h-3 text-brand-500" />
                            {prompt}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    /* ── Chat Messages ── */
                    <div className="space-y-4">
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

                {/* ═══════════ INPUT BAR ═══════════ */}
                <div className="flex-shrink-0 px-3.5 pt-2 pb-3.5 space-y-1.5 relative z-10 bg-surface/40 border-t border-border/40">
                  <div className="flex items-center gap-2 bg-surface/80 backdrop-blur-xl border border-border rounded-xl px-3 py-2
                    focus-within:border-brand-400 transition-all">
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={t("Ask anything...")}
                      rows={1}
                      className="flex-1 bg-transparent border-none outline-none text-xs text-content placeholder:text-content-muted font-light resize-none leading-relaxed max-h-20 overflow-y-auto"
                      style={{ minHeight: '18px' }}
                    />
                    <button
                      onClick={() => handleSend()}
                      disabled={!input.trim() && !isTyping}
                      className={cn(
                        'p-2 rounded-lg transition-all flex-shrink-0',
                        input.trim()
                          ? 'bg-brand-500 hover:bg-brand-600 text-white cursor-pointer shadow-xs'
                          : 'bg-surface-secondary text-content-muted cursor-not-allowed'
                      )}
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* ═══════════ DELETE CONFIRMATION ═══════════ */}
            <AnimatePresence>
              {convToDelete && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    className="bg-white rounded-xl p-4 max-w-xs w-full shadow-xl border border-border space-y-3"
                  >
                    <div className="flex items-center gap-2 text-rose-600">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      <h4 className="text-xs font-semibold">Delete Conversation?</h4>
                    </div>
                    <p className="text-[11px] text-content-secondary">
                      Delete "{convToDelete.title || 'Untitled'}"? This cannot be undone.
                    </p>
                    <div className="flex items-center justify-end gap-2 pt-1">
                      <button
                        onClick={() => setConvToDelete(null)}
                        className="px-2.5 py-1 rounded-md border border-border text-[11px] text-content hover:bg-surface-secondary cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleDeleteConfirm}
                        className="px-2.5 py-1 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-semibold cursor-pointer"
                      >
                        Delete
                      </button>
                    </div>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
