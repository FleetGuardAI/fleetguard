import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/services/auth_service.dart';
import '../../../../core/providers/settings_provider.dart';
import 'package:fleetguard_owner/l10n/app_localizations.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final userAsync = ref.watch(userProfileProvider);
    final settings = ref.watch(settingsProvider);
    final loc = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(loc.profile, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authServiceProvider).logout();
            },
          )
        ],
      ),
      body: userAsync.when(
        data: (user) {
          if (user == null) {
            return const Center(child: Text('No user profile found'));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const SizedBox(height: 24),
              Center(
                child: CircleAvatar(
                  radius: 50,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.2),
                  child: Text(
                    user.fullName.isNotEmpty ? user.fullName[0].toUpperCase() : 'U',
                    style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  user.fullName,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Center(
                child: Text(
                  user.role,
                  style: TextStyle(
                    fontSize: 16,
                    color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                  ),
                ),
              ),
              const SizedBox(height: 32),
              
              _buildSectionHeader('Account Details', isDark),
              _buildCard(
                isDark,
                child: Column(
                  children: [
                    _buildInfoRow('Email', user.email ?? 'Not provided', Icons.email, isDark),
                    _buildInfoRow('Phone', user.phone ?? 'Not provided', Icons.phone, isDark),
                    _buildInfoRow('Company ID', user.companyId ?? 'N/A', Icons.business, isDark),
                    _buildInfoRow('Role', user.role, Icons.security, isDark, isLast: true),
                  ],
                )
              ),
              
              const SizedBox(height: 24),
              _buildSectionHeader(loc.theme, isDark),
              _buildCard(
                isDark,
                child: Column(
                  children: [
                    RadioListTile<ThemeMode>(
                      title: Text(loc.system, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                      value: ThemeMode.system,
                      groupValue: settings.themeMode,
                      onChanged: (mode) {
                        if (mode != null) ref.read(settingsProvider.notifier).setThemeMode(mode);
                      },
                    ),
                    RadioListTile<ThemeMode>(
                      title: Text(loc.light, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                      value: ThemeMode.light,
                      groupValue: settings.themeMode,
                      onChanged: (mode) {
                        if (mode != null) ref.read(settingsProvider.notifier).setThemeMode(mode);
                      },
                    ),
                    RadioListTile<ThemeMode>(
                      title: Text(loc.dark, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                      value: ThemeMode.dark,
                      groupValue: settings.themeMode,
                      onChanged: (mode) {
                        if (mode != null) ref.read(settingsProvider.notifier).setThemeMode(mode);
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              _buildSectionHeader(loc.language, isDark),
              _buildCard(
                isDark,
                child: Column(
                  children: [
                    RadioListTile<String>(
                      title: Text('English', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                      value: 'en',
                      groupValue: settings.locale.languageCode,
                      onChanged: (code) {
                        if (code != null) ref.read(settingsProvider.notifier).setLocale(Locale(code));
                      },
                    ),
                    RadioListTile<String>(
                      title: Text('हिंदी (Hindi)', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                      value: 'hi',
                      groupValue: settings.locale.languageCode,
                      onChanged: (code) {
                        if (code != null) ref.read(settingsProvider.notifier).setLocale(Locale(code));
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error loading profile: $e')),
      ),
    );
  }

  Widget _buildSectionHeader(String title, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 8),
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

  Widget _buildCard(bool isDark, {required Widget child}) {
    return Card(
      color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: child,
    );
  }

  Widget _buildInfoRow(String label, String value, IconData icon, bool isDark, {bool isLast = false}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: isLast ? null : Border(bottom: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder)),
      ),
      child: Row(
        children: [
          Icon(icon, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12)),
              Text(value, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 16, fontWeight: FontWeight.w500)),
            ],
          ),
        ],
      ),
    );
  }
}
