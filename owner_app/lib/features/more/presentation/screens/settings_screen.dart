import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/providers/settings_provider.dart';
import 'package:fleetguard_owner/l10n/app_localizations.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final settings = ref.watch(settingsProvider);
    final loc = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(loc.settings, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
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
        ],
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
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: child,
    );
  }
}
