import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/services/auth_service.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('More', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        elevation: 1,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildSectionHeader('Fleet', isDark),
          _buildOpCard(
            context,
            icon: Icons.local_shipping,
            title: 'Vehicles',
            subtitle: 'Manage trucks, hardware & assets',
            onTap: () => context.push('/fleet'),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.people,
            title: 'Drivers',
            subtitle: 'Manage drivers, shifts & invites',
            onTap: () => context.push('/fleet'),
            isDark: isDark,
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('Operations', isDark),
          _buildOpCard(
            context,
            icon: Icons.map,
            title: 'Live Tracking',
            subtitle: 'Full map view of fleet',
            onTap: () => context.push('/tracking'),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.route,
            title: 'Trips',
            subtitle: 'Active, upcoming, and completed trips',
            onTap: () => context.push('/trips'),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.smart_toy,
            title: 'Copilot',
            subtitle: 'AI fleet assistant',
            onTap: () => context.push('/copilot'),
            isDark: isDark,
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('Finance', isDark),
          _buildOpCard(
            context,
            icon: Icons.receipt_long,
            title: 'Expenses',
            subtitle: 'Track trip, fuel, and maintenance costs',
            onTap: () => context.push('/finance'),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.account_balance_wallet,
            title: 'Invoices',
            subtitle: 'Manage payments & billing',
            onTap: () => context.push('/finance'),
            isDark: isDark,
          ),
          const SizedBox(height: 16),
          _buildSectionHeader('Account & System', isDark),
          _buildOpCard(
            context,
            icon: Icons.settings,
            title: 'Settings',
            subtitle: 'App preferences and notifications',
            onTap: () => context.push('/settings'),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.logout,
            title: 'Logout',
            subtitle: 'Sign out of Owner App',
            iconColor: AppColors.statusRed,
            onTap: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                  title: Text('Logout', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                  content: Text('Are you sure you want to log out?', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                    TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Logout', style: TextStyle(color: AppColors.statusRed))),
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
            isDark: isDark,
          ),
        ],
      ),
    );
  }



  Widget _buildSectionHeader(String title, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 8, top: 8),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildOpCard(BuildContext context, {required IconData icon, required String title, required String subtitle, required VoidCallback onTap, Color? iconColor, required bool isDark}) {
    return Card(
      color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      elevation: 0,
      child: ListTile(
        leading: Icon(icon, color: iconColor ?? (isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        title: Text(title, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12)),
        trailing: Icon(Icons.chevron_right, color: isDark ? AppColors.darkBorder : AppColors.lightBorder, size: 20),
        onTap: onTap,
      ),
    );
  }
}
