import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/services/auth_service.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
      appBar: AppBar(
        title: const Text('More', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: AppColors.backgroundDark,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildSectionHeader('Financials'),
          _buildOpCard(
            context,
            icon: Icons.receipt_long,
            title: 'Expenses',
            subtitle: 'Track trip, fuel, and maintenance costs',
            onTap: () => context.push('/expense'),
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('System'),
          _buildOpCard(
            context,
            icon: Icons.logout,
            title: 'Logout',
            subtitle: 'Sign out of Owner App',
            iconColor: Colors.redAccent,
            onTap: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: AppColors.surfaceDark,
                  title: const Text('Logout', style: TextStyle(color: Colors.white)),
                  content: const Text('Are you sure you want to log out?', style: TextStyle(color: Colors.white70)),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                    TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Logout', style: TextStyle(color: Colors.redAccent))),
                  ],
                ),
              );
              if (confirmed == true) {
                await ref.read(authServiceProvider).logout();
                if (context.mounted) {
                  context.go('/auth/qr-scan');
                }
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 8, top: 8),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(
          color: Colors.white54,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildOpCard(BuildContext context, {required IconData icon, required String title, required String subtitle, required VoidCallback onTap, Color? iconColor}) {
    return Card(
      color: AppColors.surfaceDark,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Icon(icon, color: iconColor ?? Colors.white70),
        title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
        trailing: const Icon(Icons.chevron_right, color: Colors.white30, size: 20),
        onTap: onTap,
      ),
    );
  }
}
