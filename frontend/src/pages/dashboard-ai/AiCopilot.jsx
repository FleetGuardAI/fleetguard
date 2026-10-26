import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Paperclip, Mic, Send, Globe, Bell, User,
  Sparkles, MessageSquare, ArrowRight, AlertTriangle,
  Table2, List, BarChart3, ChevronRight, X,
  Truck, MapPin, Calendar, Clock, CheckCircle2, XCircle
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { getInitials } from '@/utils/formatters';
import api from '@/api/client';

const SUGGESTED_PROMPTS = [
  "Show me the fleet health overview",
  "Where are both my trucks?",
  "Schedule a trip for Truck 02 tomorrow",
  "Which vehicles need maintenance?"
];

// ── Message Types ──
function ChatMessageBubble({ message, onAction }) {
  const isUser = message.role === 'user';
  const metadata = message.metadata || {};
  const proposals = metadata.proposals || [];
  const locations = metadata.locations || [];
  const verifiedTrip = metadata.verified_trip;

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
        {message.content?.text && (
          <div className="text-sm leading-relaxed whitespace-pre-wrap font-light">
            {message.content.text}
          </div>
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
                    "bg-slate-100 text-slate-600 border-slate-200"
                  )}>
                    <span className={cn(
                      "w-1 h-1 rounded-full",
                      loc.freshness === "FRESH" ? "bg-emerald-500 animate-pulse" :
                      loc.freshness === "STALE" ? "bg-amber-500" : "bg-slate-400"
                    )} />
                    {loc.freshness_label || loc.freshness}
                  </span>
                </div>
                {loc.has_location ? (
                  <div className="space-y-0.5 text-[11px] text-content-secondary">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-brand-500" />
                      <span>{loc.latitude?.toFixed(4)}, {loc.longitude?.toFixed(4)}</span>
                    </div>
                    {loc.timestamp && (
                      <div className="flex items-center gap-1 text-[10px] text-content-muted">
                        <Clock className="w-2.5 h-2.5" />
                        <span>{new Date(loc.timestamp).toLocaleTimeString()} ({loc.source})</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-[11px] text-content-muted italic">{loc.message || "No telemetry available."}</p>
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
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const [user, setUser] = useState(null);
  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
    if (cached) setUser(JSON.parse(cached));
  }, []);

  const handleSend = useCallback((text) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    // Add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: { text: messageText },
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    const payload = {
      message: messageText,
      context: { page: location.pathname }
    };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }

    // Call real AI backend
    api.copilot.chat(payload).then(res => {
      if (res.conversation_id && !conversationId) {
        setConversationId(res.conversation_id);
      }
      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: { text: res.message },
        metadata: res.metadata || {},
        timestamp: new Date(),
      };
      setIsTyping(false);
      setMessages(prev => [...prev, aiMsg]);
    }).catch(err => {
      console.error('Copilot Error:', err);
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: { text: "I'm sorry, I encountered an error while processing your request. Please try again later." },
        timestamp: new Date(),
      }]);
    });
  }, [input, location.pathname, conversationId]);

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

  useEffect(() => { scrollToBottom(); }, [messages, isTyping, scrollToBottom]);

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
            className="fixed bottom-24 right-6 w-[420px] h-[620px] max-h-[85vh] z-50 flex flex-col bg-white border border-border/80 rounded-2xl overflow-hidden shadow-2xl"
          >
            {/* ═══════════ HEADER ═══════════ */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-border/40 flex-shrink-0 relative z-10 bg-surface/40 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center border border-brand-100">
                  <img src="/assets/the_vahan_logo.png" alt="the vahan" className="w-5 h-5 object-contain" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-sm font-semibold text-content">{t("AI Co-Pilot")}</h1>
                    <span className="text-[10px] text-brand-600 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded-lg font-medium">
                      the vahan AI
                    </span>
                  </div>
                  <p className="text-[11px] text-content-secondary">{t("Fleet operations intelligence assistant")}</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-xl text-content-secondary hover:bg-surface-secondary transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* ═══════════ MESSAGES AREA ═══════════ */}
            <div className="flex-1 overflow-y-auto fg-scrollbar relative p-3">
              {isEmpty ? (
                /* ── Empty State ── */
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3 px-4">
                  <h2 className="text-lg font-light text-content">
                    {t("How can I help you today,")}{' '}
                    <span className="font-semibold">{userName}</span>?
                  </h2>
                  <p className="text-xs text-content-secondary font-light">
                    {t("Ask about truck locations, driver status, or schedule a trip.")}
                  </p>

                  <div className="flex flex-wrap gap-2 justify-center mt-4">
                    {SUGGESTED_PROMPTS.map((prompt, i) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 + i * 0.08 }}
                        onClick={() => handlePromptClick(prompt)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface/50 border border-border text-xs text-content-secondary hover:text-content hover:bg-surface-secondary transition-all cursor-pointer"
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
            <div className="flex-shrink-0 px-4 pt-2 pb-4 space-y-2 relative z-10 bg-surface/40 border-t border-border/40">
              <div className="flex items-center gap-2 bg-surface/60 backdrop-blur-xl border border-border rounded-xl px-3 py-2
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
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
