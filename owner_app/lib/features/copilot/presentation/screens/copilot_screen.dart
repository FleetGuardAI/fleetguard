import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/widgets/glass_card.dart';

final copilotMessagesProvider = StateNotifierProvider.autoDispose<CopilotMessagesNotifier, List<Map<String, dynamic>>>((ref) {
  return CopilotMessagesNotifier(ref);
});

class CopilotMessagesNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  final Ref ref;
  CopilotMessagesNotifier(this.ref) : super([]);

  Future<void> sendMessage(String text, {String? contextType, String? contextId}) async {
    final dio = ref.read(apiClientProvider).dio;

    // Add user message to state
    state = [...state, {'role': 'user', 'content': text}];
    
    // Add typing indicator placeholder
    state = [...state, {'role': 'assistant', 'content': '', 'isTyping': true}];

    try {
      final response = await dio.post(
        '/api/v1/copilot/chat',
        data: {
          'message': text,
          if (contextType != null) 'context_type': contextType,
          if (contextId != null) 'context_id': contextId,
        },
      );

      final reply = response.data['reply'] ?? 'No reply received.';
      
      // Remove typing indicator and add actual response
      state = [
        ...state.where((msg) => msg['isTyping'] != true),
        {'role': 'assistant', 'content': reply}
      ];
    } catch (e) {
      // Remove typing indicator and add error message
      state = [
        ...state.where((msg) => msg['isTyping'] != true),
        {'role': 'assistant', 'content': 'Error connecting to Copilot. Please try again.', 'isError': true}
      ];
    }
  }
}

class CopilotScreen extends ConsumerStatefulWidget {
  final String? contextType;
  final String? contextId;
  final String? contextLabel; // Used purely for UI display (e.g. "HR26XX0000")

  const CopilotScreen({super.key, this.contextType, this.contextId, this.contextLabel});

  @override
  ConsumerState<CopilotScreen> createState() => _CopilotScreenState();
}

class _CopilotScreenState extends ConsumerState<CopilotScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _sendMessage(String text) {
    if (text.trim().isEmpty) return;
    
    _controller.clear();
    ref.read(copilotMessagesProvider.notifier).sendMessage(
      text, 
      contextType: widget.contextType, 
      contextId: widget.contextId
    );
    
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final messages = ref.watch(copilotMessagesProvider);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Row(
          children: [
            Icon(Icons.auto_awesome, color: AppColors.primary, size: 24),
            const SizedBox(width: 8),
            Text('Copilot', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
          ],
        ),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (widget.contextType != null) _buildContextChip(isDark),
            Expanded(
              child: messages.isEmpty 
                  ? _buildEmptyState(isDark)
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16.0),
                      itemCount: messages.length,
                      itemBuilder: (context, index) {
                        final msg = messages[index];
                        final isUser = msg['role'] == 'user';
                        if (isUser) {
                          return _buildUserMessage(msg['content'], isDark);
                        } else {
                          return _buildBotMessage(
                            msg['content'], 
                            isDark, 
                            msg['isTyping'] == true,
                            msg['isError'] == true
                          );
                        }
                      },
                    ),
            ),
            _buildMessageInput(isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildContextChip(bool isDark) {
    String labelText = 'Global';
    if (widget.contextType == 'vehicle') {
      labelText = 'Vehicle • ${widget.contextLabel ?? widget.contextId ?? 'Unknown'}';
    } else if (widget.contextType == 'trip') {
      labelText = 'Trip • ${widget.contextLabel ?? widget.contextId ?? 'Unknown'}';
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.link, size: 14, color: AppColors.primary),
          const SizedBox(width: 6),
          Text(
            labelText,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(bool isDark) {
    List<String> suggestions = [
      'Show me fleet performance.',
      'Which vehicles need maintenance?',
      'Summarize recent expenses.',
    ];
    
    if (widget.contextType == 'vehicle') {
      suggestions = [
        'How is this vehicle performing?',
        'What maintenance needs attention?',
        'Show me its recent expenses.',
        'Are there any issues with this vehicle?',
      ];
    } else if (widget.contextType == 'trip') {
      suggestions = [
        'Summarize this trip.',
        'What went wrong on this trip?',
        'How much did this trip cost?',
        'What should I investigate?',
      ];
    }

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome, size: 64, color: AppColors.primary),
            ),
            const SizedBox(height: 24),
            Text(
              'Fleet Copilot',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Ask me anything about your fleet.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
              ),
            ),
            const SizedBox(height: 32),
            ...suggestions.map((suggestion) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: InkWell(
                onTap: () => _sendMessage(suggestion),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                  ),
                  child: Text(
                    suggestion,
                    style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w500),
                  ),
                ),
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildUserMessage(String text, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0, left: 32.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
              ),
              child: Text(
                text,
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
            radius: 16,
            child: const Icon(Icons.person, size: 18, color: AppColors.primary),
          ),
        ],
      ),
    );
  }

  Widget _buildBotMessage(String text, bool isDark, bool isTyping, bool isError) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0, right: 32.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            backgroundColor: AppColors.primary.withValues(alpha: 0.1),
            radius: 16,
            child: const Icon(Icons.auto_awesome, size: 18, color: AppColors.primary),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isError 
                  ? AppColors.statusRed.withValues(alpha: 0.1) 
                  : (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground),
                borderRadius: const BorderRadius.only(
                  topRight: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
                border: Border.all(
                  color: isError 
                    ? AppColors.statusRed 
                    : (isDark ? AppColors.darkBorder : AppColors.lightBorder)
                ),
              ),
              child: isTyping
                  ? Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                        ),
                        const SizedBox(width: 8),
                        Text('Thinking...', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                      ],
                    )
                  : MarkdownBody(
                      data: text,
                      styleSheet: MarkdownStyleSheet(
                        p: TextStyle(color: isError ? AppColors.statusRed : (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface), fontSize: 16),
                        h1: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 24, fontWeight: FontWeight.bold),
                        h2: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 20, fontWeight: FontWeight.bold),
                        h3: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 18, fontWeight: FontWeight.bold),
                        listBullet: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                        code: TextStyle(
                          backgroundColor: isDark ? Colors.black26 : Colors.black12,
                          color: isDark ? Colors.greenAccent : Colors.green[800],
                          fontFamily: 'monospace',
                        ),
                        codeblockDecoration: BoxDecoration(
                          color: isDark ? Colors.black26 : Colors.black12,
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageInput(bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        border: Border(top: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                maxLines: 4,
                minLines: 1,
                decoration: InputDecoration(
                  hintText: 'Ask Copilot...',
                  hintStyle: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                  filled: true,
                  fillColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                ),
                onSubmitted: _sendMessage,
              ),
            ),
            const SizedBox(width: 12),
            CircleAvatar(
              backgroundColor: AppColors.primary,
              radius: 24,
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white),
                tooltip: 'Send message',
                onPressed: () => _sendMessage(_controller.text),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
