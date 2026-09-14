import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/utils/navigation_safe_area.dart';
import 'package:dio/dio.dart';

final copilotMessagesProvider = StateNotifierProvider.autoDispose<CopilotMessagesNotifier, List<Map<String, dynamic>>>((ref) {
  return CopilotMessagesNotifier(ref);
});

class CopilotMessagesNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  final Ref ref;
  CopilotMessagesNotifier(this.ref) : super([]);

  Future<void> sendMessage(String text, {String? contextType, String? contextId, String? locale}) async {
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
          if (locale != null) 'language': locale,
        },
      );

      final reply = response.data['message'] ?? 'No reply received.';
      
      // Remove typing indicator and add actual response
      state = [
        ...state.where((msg) => msg['isTyping'] != true),
        {'role': 'assistant', 'content': reply}
      ];
    } catch (e) {
      String errorMessage = 'Error connecting to Copilot. Please try again.';
      if (e is DioException && e.response?.data != null) {
        errorMessage = e.response?.data['detail'] ?? errorMessage;
      }
      
      // Remove typing indicator and add error message
      state = [
        ...state.where((msg) => msg['isTyping'] != true),
        {'role': 'assistant', 'content': errorMessage, 'isError': true}
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
    final currentLocale = Localizations.localeOf(context).languageCode;
    ref.read(copilotMessagesProvider.notifier).sendMessage(
      text, 
      contextType: widget.contextType, 
      contextId: widget.contextId,
      locale: currentLocale,
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
            SizedBox(height: context.fixedControlClearance),
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
          const Icon(Icons.link, size: 14, color: AppColors.primary),
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
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkMint.withValues(alpha: 0.1) : AppColors.lightMint,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome, size: 72, color: AppColors.primary),
            ),
            const SizedBox(height: 32),
            Text(
              'Fleet Copilot',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Your AI assistant for fleet insights.\nAsk me anything!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 40),
            ...suggestions.map((suggestion) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: InkWell(
                onTap: () => _sendMessage(suggestion),
                borderRadius: BorderRadius.circular(16),
                child: Card(
                  margin: EdgeInsets.zero,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                  ),
                  color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
                    child: Row(
                      children: [
                        const Icon(Icons.chat_bubble_outline, size: 20, color: AppColors.primary),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            suggestion,
                            style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.w500),
                          ),
                        ),
                        Icon(Icons.arrow_forward_ios, size: 14, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                      ],
                    ),
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
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                  bottomLeft: Radius.circular(20),
                  bottomRight: Radius.circular(4),
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
            radius: 14,
            child: const Icon(Icons.person, size: 16, color: AppColors.primary),
          ),
        ],
      ),
    );
  }

  Widget _buildBotMessage(String text, bool isDark, bool isTyping, bool isError) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0, right: 32.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          CircleAvatar(
            backgroundColor: isDark ? AppColors.darkMint.withValues(alpha: 0.1) : AppColors.lightMint,
            radius: 14,
            child: const Icon(Icons.auto_awesome, size: 16, color: AppColors.primary),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isError 
                  ? AppColors.statusRed.withValues(alpha: 0.1) 
                  : (isDark ? AppColors.darkCardBackground : Colors.white),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                  bottomLeft: Radius.circular(4),
                  bottomRight: Radius.circular(20),
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
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                        ),
                        const SizedBox(width: 8),
                        Text('Thinking...', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                      ],
                    )
                  : _buildMarkdownBlocks(text, isDark, isError),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMarkdownBlocks(String text, bool isDark, bool isError) {
    final pattern = RegExp(r'((?:^\|.*?\|(?:\n|$))+)');
    final matches = pattern.allMatches(text);
    
    if (matches.isEmpty) {
      return _buildMarkdownBody(text, isDark, isError);
    }

    final List<Widget> children = [];
    int lastMatchEnd = 0;

    for (final match in matches) {
      if (match.start > lastMatchEnd) {
        final preText = text.substring(lastMatchEnd, match.start);
        if (preText.trim().isNotEmpty) {
          children.add(_buildMarkdownBody(preText, isDark, isError));
        }
      }

      final tableText = match.group(0)!;
      children.add(
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: _buildMarkdownBody(tableText, isDark, isError),
        ),
      );

      lastMatchEnd = match.end;
    }

    if (lastMatchEnd < text.length) {
      final postText = text.substring(lastMatchEnd);
      if (postText.trim().isNotEmpty) {
        children.add(_buildMarkdownBody(postText, isDark, isError));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  Widget _buildMarkdownBody(String text, bool isDark, bool isError) {
    return MarkdownBody(
      data: text,
      styleSheet: MarkdownStyleSheet(
        p: TextStyle(color: isError ? AppColors.statusRed : (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface), fontSize: 16),
        h1: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 24, fontWeight: FontWeight.bold),
        h2: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 20, fontWeight: FontWeight.bold),
        h3: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 18, fontWeight: FontWeight.bold),
        listBullet: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        tableBody: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 14),
        tableHead: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 14, fontWeight: FontWeight.bold),
        tableCellsPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        tableBorder: TableBorder.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder, width: 1),
        tableColumnWidth: const IntrinsicColumnWidth(),
        code: TextStyle(
          backgroundColor: isDark ? Colors.black26 : AppColors.lightMint,
          color: isDark ? Colors.greenAccent : AppColors.primary,
          fontFamily: 'monospace',
        ),
        codeblockDecoration: BoxDecoration(
          color: isDark ? Colors.black26 : AppColors.lightMint.withValues(alpha: 0.3),
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      builders: {
        // Optional: Custom builders if needed
      },
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
