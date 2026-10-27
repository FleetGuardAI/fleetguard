import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/api/client';

export function useCopilotConversation() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [totalConversations, setTotalConversations] = useState(0);

  // Get current user id for scoped storage key
  const getStorageKey = useCallback(() => {
    try {
      const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
      if (cached) {
        const u = JSON.parse(cached);
        if (u?.id) return `fleetguard_copilot_active_conv_${u.id}`;
      }
    } catch {
      // fallback
    }
    return 'fleetguard_copilot_active_conv_default';
  }, []);

  // Fetch list of conversations
  const loadConversations = useCallback(async (limit = 30, offset = 0) => {
    setIsLoadingHistory(true);
    try {
      const data = await api.copilot.getConversations(limit, offset);
      setConversations(data?.conversations || []);
      setTotalConversations(data?.total_count || data?.total || 0);
      return data?.conversations || [];
    } catch (err) {
      console.warn('Failed to load conversation history:', err);
      return [];
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Load a specific conversation and its messages
  const selectConversation = useCallback(async (convId) => {
    if (!convId) {
      setActiveConversationId(null);
      setMessages([]);
      try {
        localStorage.removeItem(getStorageKey());
      } catch {}
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const detail = await api.copilot.getConversation(convId);
      if (!detail) {
        throw new Error('Conversation not found');
      }
      const targetId = detail?.id || detail?.conversation?.id || convId;
      setActiveConversationId(targetId);
      try {
        localStorage.setItem(getStorageKey(), targetId);
      } catch {}

      // Normalize messages for UI rendering
      const rawMsgs = detail?.messages || detail?.conversation?.messages || [];
      const normalized = rawMsgs
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m) => ({
          id: m.id || m.sequence_number || `${m.role}-${Date.now()}-${Math.random()}`,
          role: m.role,
          content: { text: m.content },
          metadata: m.metadata || {},
          timestamp: new Date(m.created_at || Date.now()),
        }));

      setMessages(normalized);
    } catch (err) {
      console.error('Failed to load conversation:', err);
      // If 404 or unauthorized, reset pointer
      setActiveConversationId(null);
      setMessages([]);
      try {
        localStorage.removeItem(getStorageKey());
      } catch {}
      setError('Could not load the requested conversation.');
    } finally {
      setIsLoading(false);
    }
  }, [getStorageKey]);

  // Start a fresh conversation
  const startNewChat = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(getStorageKey());
    } catch {}
  }, [getStorageKey]);

  // Initial load: restore active conversation if pointer exists
  const initialRestoreDone = useRef(false);
  useEffect(() => {
    if (initialRestoreDone.current) return;
    initialRestoreDone.current = true;

    let savedId = null;
    try {
      savedId = localStorage.getItem(getStorageKey());
    } catch {}

    loadConversations();

    if (savedId) {
      selectConversation(savedId);
    }
  }, [getStorageKey, loadConversations, selectConversation]);

  // Send message
  const sendMessage = useCallback(async (messageText, context = null) => {
    if (!messageText || !messageText.trim()) return;

    const trimmed = messageText.trim();
    const tempUserId = `user-${Date.now()}`;
    const userMsg = {
      id: tempUserId,
      role: 'user',
      content: { text: trimmed },
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setError(null);

    try {
      const payload = {
        message: trimmed,
      };
      if (activeConversationId) {
        payload.conversation_id = activeConversationId;
      }
      if (context) {
        payload.context = context;
      }

      const response = await api.copilot.chat(payload);

      // If this was a new conversation, record its ID
      if (response.conversation_id && response.conversation_id !== activeConversationId) {
        setActiveConversationId(response.conversation_id);
        try {
          localStorage.setItem(getStorageKey(), response.conversation_id);
        } catch {}
        // Refresh conversations list to show new title
        loadConversations();
      }

      const aiMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: { text: response.message },
        metadata: response.metadata || {},
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
      return response;
    } catch (err) {
      console.error('Copilot send message error:', err);
      let errMsg = "I'm sorry, I encountered an error while processing your request. Please try again later.";
      if (err.response?.data?.detail) {
        errMsg = `Error: ${err.response.data.detail}`;
      } else if (err.message) {
        errMsg = `Error: ${err.message}`;
      }

      const errorBubble = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: { text: errMsg },
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorBubble]);
      setError(errMsg);
    } finally {
      setIsTyping(false);
    }
  }, [activeConversationId, getStorageKey, loadConversations]);

  // Delete an individual conversation
  const deleteConversation = useCallback(async (convId) => {
    if (!convId) return;
    try {
      await api.copilot.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      setTotalConversations((prev) => Math.max(0, prev - 1));

      // If the deleted one is currently active, start new chat
      if (activeConversationId === convId) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      throw err;
    }
  }, [activeConversationId, startNewChat]);

  // Clear all conversations
  const clearAllConversations = useCallback(async () => {
    try {
      await api.copilot.clearConversations();
      setConversations([]);
      setTotalConversations(0);
      startNewChat();
    } catch (err) {
      console.error('Failed to clear conversations:', err);
      throw err;
    }
  }, [startNewChat]);

  return {
    conversations,
    activeConversationId,
    messages,
    isLoading,
    isLoadingHistory,
    isTyping,
    error,
    totalConversations,
    loadConversations,
    selectConversation,
    startNewChat,
    sendMessage,
    deleteConversation,
    clearAllConversations,
  };
}
