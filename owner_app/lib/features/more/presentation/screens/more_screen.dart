import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/services/auth_service.dart';
import '../../../../core/utils/navigation_safe_area.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Profile', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        elevation: 0,
      ),
      body: ListView(
        padding: EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: context.scrollContentClearance),
        children: [
          // Avatar Card
          Card(
            color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
            ),
            elevation: 0,
            child: InkWell(
              onTap: () => context.push('/fleet'),
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 32,
                      backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                      child: const Icon(Icons.business, size: 32, color: AppColors.primary),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Fleet Owner', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 20, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 4),
                          Text('Admin Account', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 14)),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.edit, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                      onPressed: () => context.push('/settings'),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),

          _buildSectionHeader('Account', isDark),
          _buildOpCard(
            context,
            icon: Icons.settings,
            title: 'Settings',
            subtitle: 'App preferences and notifications',
            onTap: () => context.push('/settings'),
            isDark: isDark,
          ),
          const SizedBox(height: 16),

          _buildSectionHeader('Support & Preferences', isDark),
          _buildOpCard(
            context,
            icon: Icons.palette,
            title: 'Theme',
            subtitle: 'Toggle light and dark mode',
            onTap: () => _showThemeBottomSheet(context, isDark),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.help_outline,
            title: 'Help Center',
            subtitle: 'FAQs and support contact',
            onTap: () => _showSupportDialog(context, isDark),
            isDark: isDark,
          ),
          _buildOpCard(
            context,
            icon: Icons.info_outline,
            title: 'About FleetGuard',
            subtitle: 'Version 2.0.1',
            onTap: () => _showAboutAppDialog(context, isDark),
            isDark: isDark,
          ),
          const SizedBox(height: 32),

          // Logout Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.logout, color: Colors.white),
              label: const Text('Logout', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.statusRed,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: 0,
              ),
              onPressed: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    title: Text('Logout', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
                    content: Text('Are you sure you want to log out?', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text('Cancel', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant))),
                      TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Logout', style: TextStyle(color: AppColors.statusRed, fontWeight: FontWeight.bold))),
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
          ),
        ],
      ),
    );
  }



  Widget _buildSectionHeader(String title, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 12, top: 8),
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
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      elevation: 0,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: (iconColor ?? AppColors.primary).withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: iconColor ?? AppColors.primary, size: 20),
        ),
        title: Text(title, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 13)),
        trailing: Icon(Icons.chevron_right, color: isDark ? AppColors.darkBorder : AppColors.lightBorder, size: 20),
        onTap: onTap,
      ),
    );
  }

  void _showThemeBottomSheet(BuildContext context, bool isDark) {
    showModalBottomSheet(
      context: context,
      useRootNavigator: true,
      backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Theme Preferences', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 24),
              ListTile(
                leading: const Icon(Icons.wb_sunny_outlined),
                title: const Text('Light Mode'),
                trailing: !isDark ? const Icon(Icons.check, color: AppColors.primary) : null,
                onTap: () {
                  // In a real app we would update a theme provider
                  Navigator.pop(ctx);
                },
              ),
              ListTile(
                leading: const Icon(Icons.nights_stay_outlined),
                title: const Text('Dark Mode'),
                trailing: isDark ? const Icon(Icons.check, color: AppColors.primary) : null,
                onTap: () {
                  // In a real app we would update a theme provider
                  Navigator.pop(ctx);
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  void _showSupportDialog(BuildContext context, bool isDark) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text('Help Center', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
        content: Text('Please contact our support team at support@fleetguard.com.', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
          ),
        ],
      ),
    );
  }

  void _showAboutAppDialog(BuildContext context, bool isDark) {
    showAboutDialog(
      context: context,
      applicationName: 'FleetGuard Owner',
      applicationVersion: '2.0.1',
      applicationIcon: Image.asset('assets/images/owner_logo.png', width: 48, height: 48),
      children: [
        const SizedBox(height: 16),
        Text(
          'Premium Fleet Management App.\n© 2026 FleetGuard Inc.',
          style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
        ),
      ],
    );
  }
}
