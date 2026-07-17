import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, Bot, User, CheckCheck, MapPin, Image } from 'lucide-react';

export default function WhatsAppChatFeed() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'driver',
      text: 'Bhaiya, fuel fill karwaya h NH-48 toll pe, bill upload kar rha hu',
      time: '12:35 PM',
      type: 'text'
    },
    {
      id: 2,
      sender: 'driver',
      text: 'Receipt image',
      time: '12:35 PM',
      type: 'image',
      mediaUrl: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&q=80&w=200'
    },
    {
      id: 3,
      sender: 'bot',
      text: '🤖 AI Verification: Checking receipt... Found Indian Oil, ₹4,200. Requesting your live location...',
      time: '12:36 PM',
      type: 'bot'
    },
    {
      id: 4,
      sender: 'driver',
      text: 'Live Location Shared',
      time: '12:36 PM',
      type: 'location',
      lat: 24.5854,
      lng: 73.7125,
      locationName: 'NH-48, near Udaipur'
    },
    {
      id: 5,
      sender: 'bot',
      text: '🤖 Location matched with receipt merchant coords. Ticket created for approval.',
      time: '12:37 PM',
      type: 'bot'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMsg = {
      id: Date.now(),
      sender: 'owner',
      text: inputText,
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      type: 'text'
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputText('');

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'driver',
          text: 'Ok sir, waiting for approval.',
          time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
          type: 'text'
        }
      ]);
    }, 1500);
  };

  return (
    <div
      className="rounded-xl bg-surface-850 border border-white/5 flex flex-col h-[400px] shadow-lg"
      id="whatsapp-chat-feed"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between bg-surface-900/40 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-white">WhatsApp Live Chat</h4>
            <p className="text-[10px] text-slate-500 mt-0.5">Driver: Rajesh Kumar (RJ14)</p>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold">
          Active
        </span>
      </div>

      {/* Messages */}
      <div ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto space-y-3 min-h-0 custom-scrollbar bg-surface-900/20">
        {messages.map((msg) => {
          const isOwner = msg.sender === 'owner';
          const isBot = msg.sender === 'bot';

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-2.5 max-w-[85%] ${isOwner ? 'ml-auto flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-6 h-6 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold
                ${isBot ? 'bg-brand-500/20 text-brand-400' : isOwner ? 'bg-slate-700 text-white' : 'bg-emerald-600 text-white'}`}
              >
                {isBot ? <Bot className="w-3.5 h-3.5" /> : isOwner ? <User className="w-3.5 h-3.5" /> : 'R'}
              </div>

              {/* Bubble */}
              <div className={`p-2.5 rounded-xl border text-xs leading-relaxed
                ${isBot
                  ? 'bg-brand-850/40 border-brand-500/20 text-slate-300'
                  : isOwner
                    ? 'bg-brand-500/20 border-brand-500/20 text-white'
                    : 'bg-surface-700 border-white/5 text-slate-300'}`}
            >
                {msg.type === 'text' && <p>{msg.text}</p>}
                
                {msg.type === 'image' && (
                  <div className="space-y-2">
                    <p className="flex items-center gap-1.5 font-medium text-slate-200">
                      <Image className="w-3.5 h-3.5 text-slate-500" />
                      Uploaded Receipt
                    </p>
                    <img src={msg.mediaUrl} alt="Receipt" className="rounded-lg max-w-[120px] aspect-square object-cover border border-white/10" />
                  </div>
                )}

                {msg.type === 'location' && (
                  <div className="space-y-2">
                    <p className="flex items-center gap-1.5 font-medium text-slate-200">
                      <MapPin className="w-3.5 h-3.5 text-red-400" />
                      Location Shared
                    </p>
                    <p className="text-[11px] text-slate-400">{msg.locationName}</p>
                    <p className="text-[9px] text-slate-600">lat: {msg.lat}, lng: {msg.lng}</p>
                  </div>
                )}

                <div className="flex items-center justify-end gap-1 mt-1 text-[9px] text-slate-600">
                  <span>{msg.time}</span>
                  {isOwner && <CheckCheck className="w-3 h-3 text-brand-400" />}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-3 border-t border-white/5 bg-surface-900/20 flex gap-2 shrink-0">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Reply to driver..."
          className="flex-1 px-3 py-1.5 rounded-lg bg-surface-900 border border-white/5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-brand-500/30"
        />
        <button type="submit" className="p-2 rounded-lg bg-brand-500 text-white hover:bg-brand-600 transition-colors">
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
