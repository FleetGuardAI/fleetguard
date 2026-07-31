import 'package:flutter/material.dart';

/// FleetGuard curated color palette — premium fleet management aesthetics
class AppColors {
  AppColors._();

  // --- Brand Colors ---
  static const Color primary = Color(0xFF1B5E8C);
  static const Color primaryLight = Color(0xFF4DA8DA);
  static const Color primaryDark = Color(0xFF0D3F5E);
  static const Color secondary = Color(0xFF2ECC71);
  static const Color accent = Color(0xFFF39C12);

  // --- Semantic Colors ---
  static const Color success = Color(0xFF27AE60);
  static const Color warning = Color(0xFFF39C12);
  static const Color error = Color(0xFFE74C3C);
  static const Color info = Color(0xFF3498DB);

  // --- Status Colors ---
  static const Color onDuty = Color(0xFF27AE60);
  static const Color offDuty = Color(0xFF95A5A6);
  static const Color onBreak = Color(0xFFF39C12);
  static const Color onTrip = Color(0xFF3498DB);
  static const Color emergency = Color(0xFFE74C3C);
  static const Color pendingApproval = Color(0xFFE67E22);

  // --- Light Theme ---
  static const Color lightBackground = Color(0xFFF8FAFB);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightCardBackground = Color(0xFFFFFFFF);
  static const Color lightOnSurface = Color(0xFF1A2332);
  static const Color lightOnSurfaceVariant = Color(0xFF6B7B8D);
  static Color lightBorder = const Color(0xFFE8ECF0);
  static Color lightInputFill = const Color(0xFFF4F6F8);

  // --- Dark Theme ---
  static const Color darkBackground = Color(0xFF0F1923);
  static const Color darkSurface = Color(0xFF1A2736);
  static const Color darkCardBackground = Color(0xFF1E2D3D);
  static const Color darkOnSurface = Color(0xFFE8EDF2);
  static const Color darkOnSurfaceVariant = Color(0xFF8899AA);
  static Color darkBorder = const Color(0xFF2A3A4A);
  static Color darkInputFill = const Color(0xFF162230);

  // --- Gradients ---
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary, primaryLight],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient successGradient = LinearGradient(
    colors: [Color(0xFF27AE60), Color(0xFF2ECC71)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient dangerGradient = LinearGradient(
    colors: [Color(0xFFE74C3C), Color(0xFFFF6B6B)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient darkCardGradient = LinearGradient(
    colors: [Color(0xFF1E2D3D), Color(0xFF243447)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // --- Driver Score Colors ---
  static Color driverScoreColor(double score) {
    if (score >= 90) return success;
    if (score >= 75) return const Color(0xFF2ECC71);
    if (score >= 60) return warning;
    if (score >= 40) return const Color(0xFFE67E22);
    return error;
  }
}
