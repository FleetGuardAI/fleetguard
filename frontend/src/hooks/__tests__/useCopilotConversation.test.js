import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCopilotConversation } from '../useCopilotConversation';
import api from '@/api/client';

vi.mock('@/api/client', () => ({
  default: {
    copilot: {
      getConversations: vi.fn(),
      getConversation: vi.fn(),
      createConversation: vi.fn(),
      updateConversationTitle: vi.fn(),
      deleteConversation: vi.fn(),
      clearConversations: vi.fn(),
      chat: vi.fn(),
    },
  },
}));

describe('useCopilotConversation Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    api.copilot.getConversations.mockResolvedValue({
      conversations: [],
      total_count: 0,
    });
    api.copilot.getConversation.mockResolvedValue({
      id: 'default-conv',
      title: 'Default Conversation',
      messages: [],
    });
  });

  it('loads conversations list on mount', async () => {
    api.copilot.getConversations.mockResolvedValue({
      conversations: [
        { id: 'conv-1', title: 'Trip Inquiry', message_count: 2, updated_at: new Date().toISOString() },
      ],
      total_count: 1,
    });

    const { result } = renderHook(() => useCopilotConversation());

    await act(async () => {
      await result.current.loadConversations();
    });

    expect(result.current.conversations).toHaveLength(1);
    expect(result.current.conversations[0].title).toBe('Trip Inquiry');
  });

  it('selects a conversation and normalizes user and assistant messages', async () => {
    api.copilot.getConversation.mockResolvedValue({
      id: 'conv-123',
      title: 'Truck 02 Status',
      messages: [
        { id: 1, sequence_number: 1, role: 'user', content: 'Where is Truck 02?', created_at: new Date().toISOString() },
        { id: 2, sequence_number: 2, role: 'assistant', content: 'Truck 02 is in Pune.', metadata: { locations: [] }, created_at: new Date().toISOString() },
        { id: 3, sequence_number: 3, role: 'tool', content: '{"status": "ok"}', created_at: new Date().toISOString() },
      ],
    });

    const { result } = renderHook(() => useCopilotConversation());

    await act(async () => {
      await result.current.selectConversation('conv-123');
    });

    expect(result.current.activeConversationId).toBe('conv-123');
    // Only user and assistant messages should be rendered in UI
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content.text).toBe('Where is Truck 02?');
    expect(result.current.messages[1].content.text).toBe('Truck 02 is in Pune.');
  });

  it('starts a new chat by clearing active conversation and pointer', async () => {
    const { result } = renderHook(() => useCopilotConversation());

    act(() => {
      result.current.startNewChat();
    });

    expect(result.current.activeConversationId).toBeNull();
    expect(result.current.messages).toEqual([]);
  });

  it('sends message and registers newly created conversation ID', async () => {
    api.copilot.chat.mockResolvedValue({
      conversation_id: 'conv-new-uuid',
      message: 'Fleet is doing well.',
      metadata: {},
    });
    api.copilot.getConversations.mockResolvedValue({
      conversations: [{ id: 'conv-new-uuid', title: 'New Conversation' }],
      total_count: 1,
    });

    const { result } = renderHook(() => useCopilotConversation());

    await act(async () => {
      await result.current.sendMessage('How is my fleet?');
    });

    expect(result.current.activeConversationId).toBe('conv-new-uuid');
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content.text).toBe('How is my fleet?');
    expect(result.current.messages[1].content.text).toBe('Fleet is doing well.');
  });

  it('deletes a conversation and switches to new chat if active', async () => {
    api.copilot.deleteConversation.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useCopilotConversation());

    await act(async () => {
      await result.current.deleteConversation('conv-to-delete');
    });

    expect(api.copilot.deleteConversation).toHaveBeenCalledWith('conv-to-delete');
  });

  it('clears all conversations and resets chat state', async () => {
    api.copilot.clearConversations.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useCopilotConversation());

    await act(async () => {
      await result.current.clearAllConversations();
    });

    expect(api.copilot.clearConversations).toHaveBeenCalled();
    expect(result.current.conversations).toEqual([]);
    expect(result.current.activeConversationId).toBeNull();
  });
});
