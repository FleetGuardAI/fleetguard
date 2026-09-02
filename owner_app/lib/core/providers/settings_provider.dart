import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});

class SettingsState {
  final ThemeMode themeMode;
  final Locale locale;

  SettingsState({
    required this.themeMode,
    required this.locale,
  });

  SettingsState copyWith({
    ThemeMode? themeMode,
    Locale? locale,
  }) {
    return SettingsState(
      themeMode: themeMode ?? this.themeMode,
      locale: locale ?? this.locale,
    );
  }
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  static const _themeKey = 'theme_mode';
  static const _localeKey = 'locale';

  SettingsNotifier() : super(SettingsState(themeMode: ThemeMode.system, locale: const Locale('en'))) {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    
    // Load theme
    final themeStr = prefs.getString(_themeKey);
    ThemeMode mode = ThemeMode.system;
    if (themeStr == 'light') mode = ThemeMode.light;
    if (themeStr == 'dark') mode = ThemeMode.dark;

    // Load locale
    final localeStr = prefs.getString(_localeKey) ?? 'en';
    
    state = SettingsState(themeMode: mode, locale: Locale(localeStr));
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    String themeStr = 'system';
    if (mode == ThemeMode.light) themeStr = 'light';
    if (mode == ThemeMode.dark) themeStr = 'dark';
    await prefs.setString(_themeKey, themeStr);
    
    state = state.copyWith(themeMode: mode);
  }

  Future<void> setLocale(Locale locale) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_localeKey, locale.languageCode);
    
    state = state.copyWith(locale: locale);
  }
}
