import { useState, useEffect } from 'react';
import { Search, Filter, AlertCircle, RefreshCw, X, MessageSquare, Send, Lock } from 'lucide-react';
import api, { getApiErrorMessage } from '../api';

interface Ticket {
  id: number;
  ticket_id: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  requester_type: string;
  requester_name: string;
  requester_email?: string;
  requester_phone?: string;
  company_id?: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  closed_at?: string;
}

interface Message {
  id: number;
  ticket_id: number;
  content: string;
  message_type: 'PUBLIC' | 'INTERNAL_NOTE' | 'SYSTEM_EVENT';
  sender_type: string;
  sender_name: string;
  created_at: string;
}

export default function SupportTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [messageType, setMessageType] = useState<'PUBLIC' | 'INTERNAL_NOTE'>('PUBLIC');
  const [statusUpdating, setStatusUpdating] = useState(false);

  const fetchTickets = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/tickets');
      setTickets(response.data);
    } catch (err: any) {
      console.error("Tickets fetch error", {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url
      });
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const openTicket = async (ticket: Ticket) => {
    setSelectedTicket(ticket);
    setMessagesLoading(true);
    try {
      const response = await api.get(`/tickets/${ticket.id}/messages`);
      setMessages(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setMessagesLoading(false);
    }
  };

  const closeTicketModal = () => {
    setSelectedTicket(null);
    setMessages([]);
    setNewMessage('');
    setMessageType('PUBLIC');
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedTicket) return;
    
    try {
      const response = await api.post(`/tickets/${selectedTicket.id}/messages`, {
        content: newMessage.trim(),
        message_type: messageType
      });
      setMessages([...messages, response.data]);
      setNewMessage('');
      
      // If public reply was sent, update ticket status locally if needed
      if (messageType === 'PUBLIC' && (selectedTicket.status === 'OPEN' || selectedTicket.status === 'IN_PROGRESS')) {
        setSelectedTicket({ ...selectedTicket, status: 'WAITING_FOR_USER' });
        setTickets(tickets.map(t => t.id === selectedTicket.id ? { ...t, status: 'WAITING_FOR_USER' } : t));
      }
    } catch (err) {
      alert('Failed to send message');
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!selectedTicket) return;
    setStatusUpdating(true);
    try {
      const response = await api.patch(`/tickets/${selectedTicket.id}/status`, {
        status: newStatus
      });
      setSelectedTicket(response.data);
      setTickets(tickets.map(t => t.id === selectedTicket.id ? response.data : t));
      // Refresh messages to show the new system event message
      const msgRes = await api.get(`/tickets/${selectedTicket.id}/messages`);
      setMessages(msgRes.data);
    } catch (err) {
      alert('Failed to update ticket status');
    } finally {
      setStatusUpdating(false);
    }
  };

  const filteredTickets = tickets.filter(t => {
    const matchesSearch = 
      t.ticket_id.toLowerCase().includes(search.toLowerCase()) || 
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      (t.requester_name && t.requester_name.toLowerCase().includes(search.toLowerCase())) ||
      (t.requester_email && t.requester_email.toLowerCase().includes(search.toLowerCase())) ||
      (t.requester_phone && t.requester_phone.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'OPEN': return 'bg-blue-100 text-blue-800';
      case 'IN_PROGRESS': return 'bg-amber-100 text-amber-800';
      case 'WAITING_FOR_USER': return 'bg-purple-100 text-purple-800';
      case 'RESOLVED': return 'bg-emerald-100 text-emerald-800';
      case 'CLOSED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'LOW': return 'bg-slate-100 text-slate-800';
      case 'MEDIUM': return 'bg-blue-100 text-blue-800';
      case 'HIGH': return 'bg-orange-100 text-orange-800';
      case 'URGENT': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Tickets & Assistance</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage customer assistance requests, emergency SOS alerts, and technical issues across all fleets.</p>
        </div>
        <button onClick={fetchTickets} className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm">
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-wrap gap-4 items-center justify-between">
          <div className="relative flex-1 min-w-[280px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search by ID, title, requester, or phone..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-slate-500" />
            <span className="text-xs font-semibold text-slate-500 uppercase">Status:</span>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="WAITING_FOR_USER">Waiting for User</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
            <p className="mt-2 text-slate-500">Loading tickets...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-3" />
            <p className="text-red-600 font-medium">{error}</p>
            <button onClick={fetchTickets} className="mt-4 text-emerald-600 hover:underline">Try again</button>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-lg font-medium text-slate-700">No tickets found</p>
            <p>We couldn't find any tickets matching your criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-sm uppercase tracking-wider border-b border-slate-200">
                  <th className="px-6 py-4 font-semibold">ID</th>
                  <th className="px-6 py-4 font-semibold">Details</th>
                  <th className="px-6 py-4 font-semibold">Requester</th>
                  <th className="px-6 py-4 font-semibold">Status / Priority</th>
                  <th className="px-6 py-4 font-semibold">Date</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {filteredTickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">{ticket.ticket_id}</td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-800">{ticket.title}</p>
                      <p className="text-slate-500 text-xs mt-1 truncate max-w-xs">{ticket.description}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{ticket.requester_name || 'Unknown'}</p>
                      <p className="text-slate-500 text-xs">
                        <span className="font-semibold">{ticket.requester_type}</span>
                        {ticket.requester_phone ? ` • ${ticket.requester_phone}` : ''}
                      </p>
                    </td>
                    <td className="px-6 py-4 space-y-1">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${getStatusColor(ticket.status)}`}>
                        {ticket.status}
                      </span>
                      <br/>
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => openTicket(ticket)} className="text-emerald-600 hover:text-emerald-800 font-semibold px-3 py-1.5 rounded-lg border border-emerald-200 hover:bg-emerald-50 transition">
                        Manage & Reply
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ticket Details & Action Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 bg-slate-50">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                    {selectedTicket.ticket_id}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getStatusColor(selectedTicket.status)}`}>
                    {selectedTicket.status}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getPriorityColor(selectedTicket.priority)}`}>
                    {selectedTicket.priority}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedTicket.title}</h3>
                <p className="text-xs text-slate-500">
                  By {selectedTicket.requester_name} ({selectedTicket.requester_type})
                  {selectedTicket.requester_phone ? ` • Tel: ${selectedTicket.requester_phone}` : ''}
                  {selectedTicket.company_id ? ` • Company #${selectedTicket.company_id}` : ''}
                </p>
              </div>
              <button onClick={closeTicketModal} className="text-slate-400 hover:text-slate-600 bg-white border border-slate-200 p-1.5 rounded-lg shadow-sm">
                <X size={20} />
              </button>
            </div>

            {/* Quick Status Bar */}
            <div className="px-6 py-2.5 bg-slate-100 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="font-semibold text-slate-600">Quick Actions:</span>
              <div className="flex gap-2">
                {selectedTicket.status !== 'IN_PROGRESS' && (
                  <button
                    disabled={statusUpdating}
                    onClick={() => handleUpdateStatus('IN_PROGRESS')}
                    className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded font-medium disabled:opacity-50"
                  >
                    Set In Progress
                  </button>
                )}
                {selectedTicket.status !== 'RESOLVED' && (
                  <button
                    disabled={statusUpdating}
                    onClick={() => handleUpdateStatus('RESOLVED')}
                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium disabled:opacity-50"
                  >
                    Mark Resolved
                  </button>
                )}
                {selectedTicket.status !== 'CLOSED' && (
                  <button
                    disabled={statusUpdating}
                    onClick={() => handleUpdateStatus('CLOSED')}
                    className="px-2.5 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded font-medium disabled:opacity-50"
                  >
                    Close Ticket
                  </button>
                )}
                {selectedTicket.status === 'CLOSED' && (
                  <button
                    disabled={statusUpdating}
                    onClick={() => handleUpdateStatus('OPEN')}
                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
                  >
                    Reopen
                  </button>
                )}
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50 space-y-6">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Original Issue Description</h4>
                <p className="text-slate-800 text-sm whitespace-pre-wrap">{selectedTicket.description}</p>
              </div>

              <div className="space-y-4">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <MessageSquare size={16} /> Conversation Thread
                </h4>
                {messagesLoading ? (
                  <div className="text-center py-4"><div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-emerald-500 border-t-transparent"></div></div>
                ) : messages.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-4 bg-white rounded-xl border border-slate-200">No replies yet.</p>
                ) : (
                  messages.map(msg => {
                    const isInternal = msg.message_type === 'INTERNAL_NOTE';
                    const isSystem = msg.message_type === 'SYSTEM_EVENT';
                    const isStaff = msg.sender_type === 'INTERNAL_USER';

                    if (isSystem) {
                      return (
                        <div key={msg.id} className="text-center my-2">
                          <span className="inline-block bg-slate-200/80 text-slate-600 text-xs px-3 py-1 rounded-full font-medium">
                            ⚙️ {msg.content} • {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      );
                    }

                    return (
                      <div 
                        key={msg.id} 
                        className={`p-4 rounded-xl max-w-[85%] text-sm ${
                          isInternal 
                            ? 'bg-amber-50 border border-amber-200 ml-auto' 
                            : isStaff 
                            ? 'bg-emerald-50 border border-emerald-100 ml-auto' 
                            : 'bg-white border border-slate-200 mr-auto shadow-sm'
                        }`}
                      >
                        <div className="flex justify-between items-center mb-1 gap-4">
                          <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                            {isInternal && <Lock size={12} className="text-amber-600" />}
                            {msg.sender_name || 'User'}
                            {isInternal && <span className="text-amber-700 text-xs font-bold">(Internal Note)</span>}
                          </span>
                          <span className="text-xs text-slate-400">{new Date(msg.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-slate-800 whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className="p-4 bg-white border-t border-slate-200 space-y-2">
              <div className="flex gap-4 items-center">
                <span className="text-xs font-semibold text-slate-500 uppercase">Post as:</span>
                <label className="flex items-center gap-1.5 text-xs font-medium cursor-pointer text-slate-700">
                  <input
                    type="radio"
                    name="msgType"
                    checked={messageType === 'PUBLIC'}
                    onChange={() => setMessageType('PUBLIC')}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  Public Customer Reply
                </label>
                <label className="flex items-center gap-1.5 text-xs font-medium cursor-pointer text-amber-700">
                  <input
                    type="radio"
                    name="msgType"
                    checked={messageType === 'INTERNAL_NOTE'}
                    onChange={() => setMessageType('INTERNAL_NOTE')}
                    className="text-amber-600 focus:ring-amber-500"
                  />
                  🔒 Private Internal Note
                </label>
              </div>

              <form onSubmit={handleSendMessage} className="flex gap-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder={messageType === 'PUBLIC' ? "Type a reply to the requester..." : "Write a private internal note for agents..."}
                  className={`flex-1 border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 ${
                    messageType === 'INTERNAL_NOTE'
                      ? 'border-amber-300 bg-amber-50/30 focus:ring-amber-500 focus:border-amber-500'
                      : 'border-slate-300 focus:ring-emerald-500 focus:border-emerald-500'
                  }`}
                />
                <button 
                  type="submit" 
                  disabled={!newMessage.trim()} 
                  className={`px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-colors shadow-sm text-white disabled:opacity-50 ${
                    messageType === 'INTERNAL_NOTE'
                      ? 'bg-amber-600 hover:bg-amber-700 disabled:hover:bg-amber-600'
                      : 'bg-emerald-600 hover:bg-emerald-700 disabled:hover:bg-emerald-600'
                  }`}
                >
                  <Send size={18} /> {messageType === 'INTERNAL_NOTE' ? 'Add Note' : 'Send'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
