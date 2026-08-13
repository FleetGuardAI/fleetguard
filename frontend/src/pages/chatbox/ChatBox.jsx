import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Paperclip, Mic, Send, Globe, Bell, User,
  Sparkles, MessageSquare, ArrowRight, AlertTriangle,
  Table2, List, BarChart3, ChevronRight,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { getInitials } from '@/utils/formatters';
import { SUGGESTED_PROMPTS, getMockResponse } from '@/data/chatMockData';

// ── Message Types ──
function ChatMessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
      className={cn('flex gap-3 max-w-[85%]', isUser ? 'ml-auto flex-row-reverse' : '')}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-fg-green-deep flex items-center justify-center flex-shrink-0 mt-1 border border-fg-green/20">
          <Sparkles className="w-4 h-4 text-fg-green" />
        </div>
      )}

      {/* Bubble */}
      <div className={cn(
        'px-4 py-3 max-w-full rounded-2xl shadow-sm border backdrop-blur-md',
        isUser
          ? 'bg-fg-green/10 border-fg-green/20 text-content rounded-br-sm'
          : 'bg-surface/50 border-border text-content rounded-bl-sm'
      )}>
        {/* Text content */}
        {message.content?.text && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content.text}</p>
        )}

        {/* Table response */}
        {message.content?.data?.headers && (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-fg-border">
                  {message.content.data.headers.map((h, i) => (
                    <th key={i} className="text-left py-2 px-2 text-fg-text-sec font-semibold uppercase tracking-wider text-[10px]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {message.content.data.rows.map((row, i) => (
                  <tr key={i} className="border-b border-fg-border/50 hover:bg-white/[0.02]">
                    {row.map((cell, j) => (
                      <td key={j} className="py-2 px-2 text-fg-text">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* List response */}
        {message.content?.data?.items && (
          <div className="mt-3 space-y-2">
            {message.content.data.items.map((item, i) => (
              <div key={i} className="flex items-start gap-2 py-1.5 px-2 rounded-lg bg-white/[0.02]">
                <span className="w-1.5 h-1.5 rounded-full bg-fg-green mt-2 flex-shrink-0" />
                <div>
                  <span className="text-sm text-fg-text font-medium">{item.label}</span>
                  {item.detail && <span className="text-xs text-fg-text-sec ml-2">— {item.detail}</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Metrics response */}
        {message.content?.data?.metrics && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {message.content.data.metrics.map((m, i) => (
              <div key={i} className="p-2.5 rounded-xl bg-white/[0.03] border border-fg-border">
                <p className="text-[10px] text-fg-text-sec uppercase tracking-wider">{m.label}</p>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-lg font-bold text-fg-text">{m.value}</span>
                  {m.trend && (
                    <span className={cn(
                      'text-[10px] font-semibold',
                      m.trend.startsWith('+') ? 'text-red-400' : m.trend.startsWith('-') ? 'text-fg-green' : 'text-amber-400'
                    )}>{m.trend}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Alerts response */}
        {message.content?.data?.alerts && (
          <div className="mt-3 space-y-2">
            {message.content.data.alerts.map((a, i) => (
              <div key={i} className={cn(
                'flex items-start gap-2 py-2 px-3 rounded-xl border',
                a.severity === 'critical' ? 'bg-red-500/5 border-red-500/20' :
                a.severity === 'warning' ? 'bg-amber-500/5 border-amber-500/20' :
                'bg-fg-green/5 border-fg-green/20'
              )}>
                <AlertTriangle className={cn(
                  'w-3.5 h-3.5 mt-0.5 flex-shrink-0',
                  a.severity === 'critical' ? 'text-red-400' :
                  a.severity === 'warning' ? 'text-amber-400' : 'text-fg-green'
                )} />
                <div>
                  <p className="text-sm text-fg-text">{a.title}</p>
                  {a.time && <p className="text-[11px] text-fg-text-sec mt-0.5">{a.time}</p>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Suggestion */}
        {message.content?.suggestion && (
          <p className="mt-3 pt-3 border-t border-fg-border text-xs text-fg-green italic">
            {message.content.suggestion}
          </p>
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

    // Simulate AI response with streaming delay
    setTimeout(() => {
      const response = getMockResponse(messageText);
      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setIsTyping(false);
      setMessages(prev => [...prev, aiMsg]);
    }, 1200 + Math.random() * 800);
  }, [input]);

  // Handle initial message from search bar navigation
  useEffect(() => {
    if (location.state?.initialMessage) {
      handleSend(location.state.initialMessage);
      // Clean up navigation state
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
    // Auto-send after brief visual feedback
    setTimeout(() => handleSend(prompt), 150);
  };

  const userName = user?.name || 'Dev1';
  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] max-w-[1200px] mx-auto animate-fade-in">

      {/* ═══════════ HEADER ═══════════ */}
      <div className="flex items-center justify-between py-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-fg-green-deep flex items-center justify-center border border-fg-green/20">
            <img src="/assets/fleetguard-logo.png" alt="FleetGuard" className="w-5 h-5 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold text-fg-text">{t("AI Co-Pilot")}</h1>
              <span className="text-[10px] text-fg-text-sec bg-fg-green-deep/50 border border-fg-green/20 px-2 py-0.5 rounded-lg font-medium">
                FleetGuard.AI
              </span>
            </div>
            <p className="text-[11px] text-fg-text-sec">{t("Your intelligent operations assistant")}</p>
          </div>
        </div>
      </div>

      {/* ═══════════ MESSAGES AREA ═══════════ */}
      <div className="flex-1 overflow-y-auto fg-scrollbar relative">
        {isEmpty ? (
          /* ── Empty State ── */
          <div className="flex flex-col items-center justify-center h-full relative">
            {/* Atmospheric background */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              {/* Subtle radial green glow */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-fg-green/[0.03] blur-[120px]" />
              
              {/* Faint grid */}
              <div 
                className="absolute inset-0 opacity-[0.02]"
                style={{
                  backgroundImage: `
                    linear-gradient(to right, rgba(25,184,106,0.3) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(25,184,106,0.3) 1px, transparent 1px)
                  `,
                  backgroundSize: '48px 48px',
                }}
              />

              {/* Abstract route lines */}
              <svg className="absolute inset-0 w-full h-full opacity-[0.03]" viewBox="0 0 800 600">
                <path d="M100,300 C200,200 350,400 500,250 S700,350 800,200" stroke="#19B86A" strokeWidth="1" fill="none" />
                <path d="M0,400 C150,350 300,500 450,300 S650,450 800,350" stroke="#19B86A" strokeWidth="0.5" fill="none" />
                <path d="M200,100 C300,200 400,150 500,250 S650,200 750,300" stroke="#19B86A" strokeWidth="0.5" fill="none" />
                {/* Data particles */}
                <circle cx="250" cy="250" r="2" fill="#19B86A" opacity="0.3">
                  <animate attributeName="opacity" values="0.1;0.4;0.1" dur="3s" repeatCount="indefinite" />
                </circle>
                <circle cx="500" cy="280" r="1.5" fill="#19B86A" opacity="0.2">
                  <animate attributeName="opacity" values="0.1;0.3;0.1" dur="4s" repeatCount="indefinite" />
                </circle>
                <circle cx="650" cy="320" r="2" fill="#19B86A" opacity="0.25">
                  <animate attributeName="opacity" values="0.15;0.35;0.15" dur="3.5s" repeatCount="indefinite" />
                </circle>
              </svg>
            </div>

            <div className="relative z-10 text-center space-y-4 max-w-lg">
              <h2 className="text-2xl font-light text-fg-text">
                {t("How can I help you today,")}{' '}
                <span className="font-semibold">{userName}</span>?
              </h2>
              <p className="text-sm text-fg-text-sec font-light">
                {t("Ask me anything about your fleet, drivers, loads, fuel, or reports.")}
              </p>
            </div>

            {/* Suggested Prompt Pills */}
            <div className="relative z-10 flex flex-wrap gap-2.5 justify-center mt-10 max-w-2xl px-4">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.08 }}
                  onClick={() => handlePromptClick(prompt)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface/40 backdrop-blur-md border border-border text-sm text-content-secondary hover:text-content hover:bg-surface-secondary/80 hover:shadow-fg-glow hover:-translate-y-0.5 transition-all duration-300"
                >
                  <Sparkles className="w-3.5 h-3.5 text-fg-green" />
                  {prompt}
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          /* ── Chat Messages ── */
          <div className="space-y-5 py-6 px-2">
            {messages.map((msg) => (
              <ChatMessageBubble key={msg.id} message={msg} />
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
          focus-within:border-fg-green/40 focus-within:shadow-[0_0_20px_rgba(25,184,106,0.15)] transition-all duration-300">
          <button className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-secondary transition-colors flex-shrink-0">
            <Paperclip className="w-4.5 h-4.5" />
          </button>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("Ask anything...")}
            rows={1}
            className="flex-1 bg-transparent border-none outline-none text-sm text-fg-text placeholder:text-fg-text-sec/50 font-light resize-none leading-relaxed max-h-24 overflow-y-auto"
            style={{ minHeight: '20px' }}
          />
          <button className="p-1.5 rounded-lg hover:bg-white/[0.05] text-fg-text-sec transition-colors flex-shrink-0">
            <Mic className="w-4.5 h-4.5" />
          </button>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() && !isTyping}
            className={cn(
              'p-2.5 rounded-xl transition-all duration-200 flex-shrink-0',
              input.trim()
                ? 'bg-fg-green hover:bg-fg-green-bright text-fg-dark cursor-pointer'
                : 'bg-white/[0.03] text-fg-text-sec/40 cursor-not-allowed'
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[11px] text-fg-text-sec/40 text-center font-light">
          {t("FleetGuard AI may make mistakes. Please verify important information.")}
        </p>
      </div>
    </div>
  );
}
