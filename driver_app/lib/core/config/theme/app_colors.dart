import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // --- Brand Colors ---
  static const Color primary = Color(0xFF0F9D58); // FleetGuard Green
  static const Color primaryLight = Color(0xFF34B26C);
  static const Color primaryDark = Color(0xFF087540);
  
  // --- Supporting ---
  static const Color mutedGreen = Color(0xFFE6F4EA);
  static const Color deepGraphite = Color(0xFF1E2124);
  static const Color coolGray = Color(0xFF757575);
  static const Color blueGray = Color(0xFF546E7A);

  // --- Semantic & Status Colors ---
  static const Color success = Color(0xFF27AE60);
  static const Color warning = Color(0xFFF4B400); // Amber
  static const Color error = Color(0xFFDB4437); // Red
  static const Color info = Color(0xFF4285F4); // Blue

  // Status mappings
  static const Color statusGreen = Color(0xFF27AE60); // healthy/active/completed
  static const Color statusAmber = Color(0xFFF4B400); // warning/attention
  static const Color statusRed = Color(0xFFDB4437);   // critical/failed
  static const Color statusBlue = Color(0xFF4285F4);  // information/in-progress

  // Duty Status Colors
  static const Color onDuty = Color(0xFF27AE60);
  static const Color onBreak = Color(0xFFF4B400);
  static const Color offDuty = Color(0xFF757575);

  static Color driverScoreColor(int score) {
    if (score >= 90) return success;
    if (score >= 70) return warning;
    return error;
  }

  static const LinearGradient dangerGradient = LinearGradient(
    colors: [Color(0xFFDB4437), Color(0xFFC53929)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // --- Light Theme ---
  static const Color lightBackground = Color(0xFFF8F9FA); // Soft white/cream
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightCardBackground = Color(0xFFFFFFFF);
  static const Color lightOnSurface = Color(0xFF1E2124);
  static const Color lightOnSurfaceVariant = Color(0xFF757575);
  static Color lightBorder = const Color(0xFFE8ECF0);
  static Color lightInputFill = const Color(0xFFF4F6F8);
}

