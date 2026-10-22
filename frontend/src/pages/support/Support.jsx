import React, { useState, useEffect } from 'react';
import { LifeBuoy, Plus, Mail, Phone, Clock, MessageSquare, ExternalLink, CheckCircle, Send, X } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Table } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import api from '@/api/client';

export default function Support() {
  const { success, error } = useToast();

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('General Inquiry');
  const [description, setDescription] = useState('');

  // Selected Ticket & Conversation State
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  const loadTickets = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await api.support.list();
      setTickets(Array.isArray(data) ? data : []);
    } catch (e) {
      setFetchError(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const openTicketDetails = async (ticket) => {
    setSelectedTicket(ticket);
    setMessagesLoading(true);
    setReplyText('');
    try {
      const data = await api.support.getMessages(ticket.ticket_id || ticket.id);
      setMessages(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load ticket messages', err);
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  const closeTicketDetails = () => {
    setSelectedTicket(null);
    setMessages([]);
    setReplyText('');
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || !selectedTicket) return;

    setSendingReply(true);
    try {
      const newMsg = await api.support.sendMessage(selectedTicket.ticket_id || selectedTicket.id, {
        content: replyText.trim(),
      });
      setMessages((prev) => [...prev, newMsg]);
      setReplyText('');
      success('Reply Sent', 'Your message has been sent to our support team.');
      loadTickets(); // Refresh status in background
    } catch (err) {
      error('Failed to Send', err.message || 'Could not send reply. Please try again.');
    } finally {
      setSendingReply(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      error('Validation Error', 'Please fill in all required fields.');
      return;
    }

    setSubmitting(true);
    try {
      const categoryMap = {
        'General Inquiry': 'OTHER',
        'Technical Issue': 'APP_BUG',
        'Billing & Payments': 'PAYMENT',
        'Hardware / Telematics': 'TECHNICAL',
        'Feature Request': 'FEATURE_REQUEST',
      };
      const backendCategory = categoryMap[category] || 'OTHER';

      const payload = {
        title: subject,
        category: backendCategory,
        description,
        priority: 'MEDIUM',
      };
      await api.support.create(payload);
      success('Ticket Submitted', 'Our support team will get back to you shortly.');
      setModalOpen(false);
      setSubject('');
      setDescription('');
      loadTickets();
    } catch (e) {
      error('Submission Failed', e.message || 'Failed to submit ticket. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return <Badge variant="info">OPEN</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="warning">IN PROGRESS</Badge>;
      case 'WAITING_FOR_USER':
        return <Badge variant="secondary">ACTION REQUIRED</Badge>;
      case 'RESOLVED':
        return <Badge variant="success">RESOLVED</Badge>;
      case 'CLOSED':
        return <Badge variant="default">CLOSED</Badge>;
      default:
        return <Badge variant="warning">{status || 'OPEN'}</Badge>;
    }
  };

  const columns = [
    {
      key: 'ticket_id',
      label: 'Ticket ID',
      render: (t) => (
        <span className="font-mono font-medium text-brand-600">
          {t.ticket_id || `TICK-${t.id}`}
        </span>
      ),
    },
    {
      key: 'title',
      label: 'Subject',
      render: (t) => (
        <div>
          <span className="font-semibold text-content block">{t.title}</span>
          <span className="text-xs text-content-muted line-clamp-1">{t.description}</span>
        </div>
      ),
    },
    {
      key: 'category',
      label: 'Category',
      render: (t) => <span className="text-content-secondary text-xs">{t.category}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      render: (t) => getStatusBadge(t.status),
    },
    {
      key: 'created_at',
      label: 'Date Raised',
      render: (t) => (
        <span className="text-content-secondary text-xs whitespace-nowrap">
          {new Date(t.created_at || Date.now()).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Action',
      render: (t) => (
        <Button
          variant="outline"
          size="sm"
          className="text-xs py-1 px-2.5 h-auto"
          onClick={() => openTicketDetails(t)}
        >
          View & Reply
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <LifeBuoy className="h-6 w-6 text-brand-600" />
            Support Center
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">
            Need help? Raise a ticket or track ongoing requests below.
          </p>
        </div>
        <Button variant="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>
          Raise New Ticket
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Support Resources / Contact Info */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="space-y-4 bg-brand-900 border-none shadow-lg text-white">
            <CardHeader className="p-0">
              <CardTitle className="text-lg text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <div className="space-y-4 pt-2">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Phone className="h-4 w-4 text-brand-100" />
                </div>
                <div>
                  <p className="text-xs text-brand-100 uppercase tracking-wider font-semibold">Toll-Free Helpline</p>
                  <p className="text-sm font-medium mt-0.5">1-800-FLEET-99</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Mail className="h-4 w-4 text-brand-100" />
                </div>
                <div>
                  <p className="text-xs text-brand-100 uppercase tracking-wider font-semibold">Email Support</p>
                  <p className="text-sm font-medium mt-0.5">support@fleetguard.ai</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Clock className="h-4 w-4 text-brand-100" />
                </div>
                <div>
                  <p className="text-xs text-brand-100 uppercase tracking-wider font-semibold">Operating Hours</p>
                  <p className="text-sm font-medium mt-0.5">24/7 Monitoring & Support</p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="space-y-4">
            <CardHeader className="p-0">
              <CardTitle className="text-base">Quick Links</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              <a href="#" className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-brand-300 hover:bg-brand-50/50 transition-colors group">
                <span className="text-sm font-medium text-content group-hover:text-brand-700">Knowledge Base</span>
                <ExternalLink className="h-4 w-4 text-content-muted group-hover:text-brand-600" />
              </a>
              <a href="#" className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-brand-300 hover:bg-brand-50/50 transition-colors group">
                <span className="text-sm font-medium text-content group-hover:text-brand-700">System Status</span>
                <ExternalLink className="h-4 w-4 text-content-muted group-hover:text-brand-600" />
              </a>
              <a href="#" className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-brand-300 hover:bg-brand-50/50 transition-colors group">
                <span className="text-sm font-medium text-content group-hover:text-brand-700">Driver Emergency Center</span>
                <ExternalLink className="h-4 w-4 text-content-muted group-hover:text-brand-600" />
              </a>
            </div>
          </Card>
        </div>

        {/* Tickets Table */}
        <div className="lg:col-span-2">
          <Card padding="none" className="h-full min-h-[400px]">
            <div className="p-4 border-b border-border flex justify-between items-center">
              <CardTitle className="text-base">My Support Tickets</CardTitle>
              <Button variant="ghost" size="sm" onClick={loadTickets}>
                Refresh
              </Button>
            </div>
            {loading ? (
              <div className="p-12 flex justify-center">
                <Loader />
              </div>
            ) : fetchError ? (
              <ErrorState title="Error Loading Tickets" message="Could not retrieve your support history." onRetry={loadTickets} />
            ) : tickets.length === 0 ? (
              <EmptyState 
                title="No Support Tickets" 
                description="You haven't raised any support tickets yet. Click 'Raise New Ticket' if you need assistance."
                icon={<CheckCircle className="h-10 w-10 text-green-500" />}
              />
            ) : (
              <div className="overflow-x-auto">
                <Table columns={columns} data={tickets} keyExtractor={(t) => t.ticket_id || t.id} />
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Ticket Conversation & Details Modal */}
      {selectedTicket && (
        <Modal
          open={!!selectedTicket}
          onClose={closeTicketDetails}
          title={`Ticket: ${selectedTicket.ticket_id || selectedTicket.id}`}
          description={selectedTicket.title}
          footer={
            <Button variant="outline" onClick={closeTicketDetails}>
              Close
            </Button>
          }
        >
          <div className="space-y-4 max-h-[70vh] flex flex-col">
            <div className="p-3 bg-surface rounded-xl border border-border text-sm space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-content-muted uppercase">Status / Priority</span>
                <div className="flex gap-2 items-center">
                  {getStatusBadge(selectedTicket.status)}
                  <Badge variant="outline">{selectedTicket.priority}</Badge>
                </div>
              </div>
              <div>
                <p className="text-xs text-content-muted font-medium">Original Description:</p>
                <p className="text-content whitespace-pre-wrap mt-0.5">{selectedTicket.description}</p>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 p-1 min-h-[160px] max-h-[300px]">
              <h4 className="text-xs font-bold uppercase tracking-wider text-content-secondary">
                Conversation Thread
              </h4>
              {messagesLoading ? (
                <div className="p-6 text-center"><Loader /></div>
              ) : messages.length === 0 ? (
                <p className="text-xs text-content-muted italic">No messages yet.</p>
              ) : (
                messages.map((m) => {
                  const isStaff = m.sender_type === 'INTERNAL_USER';
                  return (
                    <div
                      key={m.id}
                      className={`p-3 rounded-xl max-w-[85%] text-sm ${
                        isStaff
                          ? 'bg-brand-50 border border-brand-200 ml-auto'
                          : 'bg-surface border border-border mr-auto'
                      }`}
                    >
                      <div className="flex justify-between items-center text-xs text-content-muted mb-1 gap-4">
                        <span className="font-semibold text-content">
                          {isStaff ? '⭐ The Vahan Support' : (m.sender_name || 'You')}
                        </span>
                        <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="text-content whitespace-pre-wrap">{m.content}</p>
                    </div>
                  );
                })
              )}
            </div>

            {selectedTicket.status !== 'CLOSED' ? (
              <form onSubmit={handleSendReply} className="pt-2 border-t border-border flex gap-2">
                <Input
                  placeholder="Type a response to support..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  variant="primary"
                  loading={sendingReply}
                  disabled={!replyText.trim()}
                  icon={<Send className="h-4 w-4" />}
                >
                  Send
                </Button>
              </form>
            ) : (
              <p className="text-xs text-content-muted text-center pt-2 border-t border-border">
                This ticket is closed. If you have questions, please raise a new ticket.
              </p>
            )}
          </div>
        </Modal>
      )}

      {/* Raise Ticket Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Raise a Support Ticket"
        description="Please describe your issue in detail. Our support team will investigate and respond promptly."
        footer={
          <>
            <Button variant="outline" onClick={() => setModalOpen(false)} disabled={submitting}>Cancel</Button>
            <Button variant="primary" onClick={handleCreateTicket} loading={submitting}>Submit Ticket</Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleCreateTicket}>
          <Select
            label="Issue Category"
            options={[
              { value: 'General Inquiry', label: 'General Inquiry' },
              { value: 'Technical Issue', label: 'Technical Issue / Bug' },
              { value: 'Billing & Payments', label: 'Billing & Payments' },
              { value: 'Hardware / Telematics', label: 'Hardware / Telematics Error' },
              { value: 'Feature Request', label: 'Feature Request' },
            ]}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
          />
          <Input
            label="Subject"
            placeholder="Brief summary of the issue..."
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
          />
          <div className="space-y-1.5 pt-1">
            <span className="block text-sm font-medium text-content-secondary">Detailed Description</span>
            <textarea
              className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-content outline-none transition-all focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 min-h-[120px] resize-y"
              placeholder="Please provide as much context as possible..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
}
