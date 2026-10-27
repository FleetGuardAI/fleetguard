import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Paperclip, Mic, Send, Globe, Bell, User,
  Sparkles, MessageSquare, ArrowRight, AlertTriangle,
  Table2, List, BarChart3, ChevronRight,
  Truck, MapPin, Calendar, Clock, CheckCircle2, XCircle, AlertCircle, Navigation
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { getInitials } from '@/utils/formatters';
import MarkdownMessage from '@/components/shared/MarkdownMessage';
import api from '@/api/client';

const SUGGESTED_PROMPTS = [
  "Show me the fleet health overview",
  "Where are both my trucks?",
  "Schedule a trip for Truck 02 tomorrow",
  "Which vehicles need maintenance?",
  "Show me yesterday's fuel anomalies"
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
        'px-4 py-3 max-w-full rounded-2xl shadow-sm border backdrop-blur-md space-y-2.5',
        isUser
          ? 'bg-fg-green/10 border-fg-green/20 text-content rounded-br-sm'
          : 'bg-surface/50 border-border text-content rounded-bl-sm'
      )}>
        {/* Message content */}
        {message.content?.text && (
          isUser ? (
            <div className="text-sm leading-relaxed whitespace-pre-wrap font-light">
              {message.content.text}
            </div>
          ) : (
            <MarkdownMessage content={message.content.text} />
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
                  <div className="space-y-1 text-xs text-content-secondary">
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
                        <span>Recorded: {new Date(loc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} ({loc.source})</span>
                      </div>
                    )}
                    {loc.assigned_driver && (
                      <div className="flex items-center gap-1.5 text-[11px]">
                        <User className="w-3 h-3 text-content-muted" />
                        <span>Driver: {loc.assigned_driver}</span>
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

  const handleSend = useCallback(async (text) => {
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

    try {
      const payload = {
        message: messageText,
      };
      if (conversationId) {
        payload.conversation_id = conversationId;
      }
      if (location.state?.context) {
        payload.context = location.state.context;
      }

      const response = await api.copilot.chat(payload);
      
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: { text: response.message },
        metadata: response.metadata || {},
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Copilot chat error:", err);
      let errorMessage = "I'm sorry, I encountered an error while processing your request. Please try again later.";
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = `Error: ${err.response.data.detail}`;
      } else if (err.message) {
        errorMessage = `Error: ${err.message}`;
      }

      const errorMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: { text: errorMessage },
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  }, [input, conversationId, location.state]);

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
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-5xl mx-auto relative px-4">
      {/* ═══════════ HEADER ═══════════ */}
      <div className="flex items-center justify-between pb-4 border-b border-border/40 flex-shrink-0 relative z-10 bg-transparent">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center border border-brand-100">
            <img src="/assets/the_vahan_logo.png" alt="the vahan" className="w-6 h-6 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-content">{t("AI Co-Pilot")}</h1>
              <span className="text-[10px] text-brand-600 bg-brand-50 border border-brand-100 px-2 py-0.5 rounded-lg font-medium">
                the vahan Intelligence
              </span>
            </div>
            <p className="text-xs text-content-secondary">{t("Data-grounded fleet operations and safe operational execution assistant")}</p>
          </div>
        </div>
      </div>

      {/* ═══════════ MESSAGES AREA ═══════════ */}
      <div className="flex-1 overflow-y-auto fg-scrollbar relative py-4">
        {isEmpty ? (
          /* ── Empty State ── */
          <div className="flex flex-col items-center justify-center h-full relative">
            <div className="relative z-10 text-center space-y-4 max-w-lg">
              <h2 className="text-2xl font-light text-content">
                {t("How can I assist your fleet today,")}{' '}
                <span className="font-semibold">{userName}</span>?
              </h2>
              <p className="text-sm text-content-secondary font-light">
                {t("Ask about vehicle locations, driver status, trips, fuel metrics, or schedule a verified trip.")}
              </p>
            </div>

            <div className="relative z-10 flex flex-wrap gap-2.5 justify-center mt-10 max-w-2xl px-4">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.08 }}
                  onClick={() => handlePromptClick(prompt)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface/40 backdrop-blur-md border border-border text-sm text-content-secondary hover:text-content hover:bg-surface-secondary/80 hover:shadow-fg-glow hover:-translate-y-0.5 transition-all duration-300 cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                  {prompt}
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          /* ── Chat Messages ── */
          <div className="space-y-5 py-2 px-2">
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
      <div className="flex-shrink-0 pt-3 pb-4 space-y-2 relative z-10">
        <div className="flex items-center gap-3 bg-surface/60 backdrop-blur-xl border border-border rounded-2xl px-4 py-3
          focus-within:border-brand-400 focus-within:shadow-[0_0_20px_rgba(34,197,94,0.15)] transition-all duration-300">
          <button className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-secondary transition-colors flex-shrink-0">
            <Paperclip className="w-4.5 h-4.5" />
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
            <Mic className="w-4.5 h-4.5" />
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
        <p className="text-[10px] text-content-muted text-center font-light">
          {t("Fleetguard AI retrieves authoritative fleet records and requires explicit confirmation for operational actions.")}
        </p>
      </div>
    </div>
  );
}
