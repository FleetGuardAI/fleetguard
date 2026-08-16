import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class CopilotScreen extends StatelessWidget {
  const CopilotScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(title: const Text('Fleet Copilot')),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16.0),
              children: [
                _buildBotMessage('How can I help with your fleet today?'),
                const SizedBox(height: 24),
                const Text('Suggested questions:', style: TextStyle(color: AppTheme.textSecondary, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                _buildSuggestion('How is my fleet doing?'),
                _buildSuggestion('What needs my attention?'),
                _buildSuggestion('Which truck is performing worst?'),
                _buildSuggestion('Why is TRK-104 consuming more fuel?'),
                _buildSuggestion('Which vehicles need maintenance?'),
                _buildSuggestion('How much did I spend this month?'),
              ],
            ),
          ),
          _buildMessageInput(),
        ],
      ),
    );
  }

  Widget _buildBotMessage(String text) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const CircleAvatar(
          backgroundColor: AppTheme.primaryGreen,
          child: Icon(Icons.smart_toy, color: Colors.white),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.cardLight,
              borderRadius: BorderRadius.circular(16).copyWith(topLeft: const Radius.circular(0)),
              boxShadow: [
                BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 5, offset: const Offset(0, 2)),
              ],
            ),
            child: Text(text, style: const TextStyle(fontSize: 16)),
          ),
        ),
        const SizedBox(width: 32),
      ],
    );
  }

  Widget _buildSuggestion(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: InkWell(
        onTap: () {},
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppTheme.primaryGreen.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.3)),
          ),
          child: Text(text, style: const TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardLight,
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, -4)),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Ask Fleet Copilot...',
                filled: true,
                fillColor: AppTheme.backgroundCream,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
          ),
          const SizedBox(width: 12),
          CircleAvatar(
            backgroundColor: AppTheme.primaryGreen,
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.white, size: 20),
              onPressed: () {},
            ),
          )
        ],
      ),
    );
  }
}
