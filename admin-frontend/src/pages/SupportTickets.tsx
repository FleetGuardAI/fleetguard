import { useState, useEffect } from 'react';
import { Search, Filter, AlertCircle, RefreshCw, X, MessageSquare, Send } from 'lucide-react';
import api from '../api';

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
  created_at: string;
  updated_at: string;
}

interface Message {
  id: number;
  content: string;
  sender_type: string;
  sender_name: string;
  created_at: string;
}

export default function SupportTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [newMessage, setNewMessage] = useState('');

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
      setError('Failed to load tickets. Please try again.');
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
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedTicket) return;
    
    try {
      const response = await api.post(`/tickets/${selectedTicket.id}/messages`, {
        content: newMessage,
        message_type: 'PUBLIC'
      });
      setMessages([...messages, response.data]);
      setNewMessage('');
    } catch (err) {
      alert('Failed to send message');
    }
  };

  const filteredTickets = tickets.filter(t => 
    t.ticket_id.toLowerCase().includes(search.toLowerCase()) || 
    t.title.toLowerCase().includes(search.toLowerCase()) ||
    (t.requester_name && t.requester_name.toLowerCase().includes(search.toLowerCase()))
  );

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'OPEN': return 'bg-blue-100 text-blue-800';
      case 'IN_PROGRESS': return 'bg-amber-100 text-amber-800';
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
        <h1 className="text-2xl font-bold text-slate-900">Support Tickets</h1>
        <button onClick={fetchTickets} className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm">
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search tickets by ID, title, or user..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-slate-700 bg-white hover:bg-slate-50">
            <Filter size={18} />
            Filter
          </button>
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
                    <td className="px-6 py-4 font-medium text-slate-900">{ticket.ticket_id}</td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-800">{ticket.title}</p>
                      <p className="text-slate-500 text-xs mt-1 truncate max-w-xs">{ticket.description}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{ticket.requester_name || 'Unknown'}</p>
                      <p className="text-slate-500 text-xs">{ticket.requester_type}</p>
                    </td>
                    <td className="px-6 py-4 space-y-2">
                      <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(ticket.status)}`}>
                        {ticket.status}
                      </span>
                      <br/>
                      <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => openTicket(ticket)} className="text-emerald-600 hover:text-emerald-800 font-medium">
                        View & Reply
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ticket Details Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 bg-slate-50">
              <div>
                <h3 className="text-lg font-bold text-slate-900">{selectedTicket.ticket_id}: {selectedTicket.title}</h3>
                <p className="text-sm text-slate-500">By {selectedTicket.requester_name} ({selectedTicket.requester_type})</p>
              </div>
              <button onClick={closeTicketModal} className="text-slate-400 hover:text-slate-600 bg-white border border-slate-200 p-1.5 rounded-lg shadow-sm">
                <X size={20} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50 space-y-6">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Description</h4>
                <p className="text-slate-800 whitespace-pre-wrap">{selectedTicket.description}</p>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <MessageSquare size={16} /> Conversation
                </h4>
                {messagesLoading ? (
                  <div className="text-center py-4"><div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-emerald-500 border-t-transparent"></div></div>
                ) : messages.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-4 bg-white rounded-xl border border-slate-200">No replies yet.</p>
                ) : (
                  messages.map(msg => (
                    <div key={msg.id} className={`p-4 rounded-xl max-w-[85%] ${msg.sender_type === 'INTERNAL_USER' ? 'bg-emerald-50 ml-auto border border-emerald-100' : 'bg-white border border-slate-200 mr-auto shadow-sm'}`}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-sm text-slate-900">{msg.sender_name}</span>
                        <span className="text-xs text-slate-500">{new Date(msg.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-slate-800 text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="p-4 bg-white border-t border-slate-200">
              <form onSubmit={handleSendMessage} className="flex gap-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder="Type a reply..."
                  className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
                <button type="submit" disabled={!newMessage.trim()} className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:hover:bg-emerald-600 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-colors shadow-sm">
                  <Send size={18} /> Send
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
