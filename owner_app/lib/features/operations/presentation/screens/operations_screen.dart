import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';

class OperationsScreen extends StatelessWidget {
  const OperationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Operations', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        elevation: 1,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
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
        ],
      ),
    );
  }

  Widget _buildOpCard(BuildContext context, {required IconData icon, required String title, required String subtitle, required VoidCallback onTap, required bool isDark}) {
    return Card(
      color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: AppColors.primary),
        ),
        title: Text(title, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold, fontSize: 16)),
        subtitle: Text(subtitle, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        trailing: Icon(Icons.chevron_right, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
        onTap: onTap,
      ),
    );
  }
}
