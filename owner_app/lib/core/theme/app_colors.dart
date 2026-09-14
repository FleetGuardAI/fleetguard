import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // --- Brand Colors (Light) ---
  static const Color primary = Color(0xFF087A4A); // Deep Green
  static const Color primaryDark = Color(0xFF064E3B); // Dark Green
  static const Color emerald = Color(0xFF0B8F5A); // Primary Emerald
  static const Color lightMint = Color(0xFFDDF7EB); // Light Mint
  static const Color veryLightMint = Color(0xFFF1FBF6); // Very Light Mint

  // --- Supporting Accents ---
  static const Color blueAccent = Color(0xFF3182CE);
  static const Color orangeAccent = Color(0xFFF59E0B);
  static const Color purpleAccent = Color(0xFF6D4AFF);
  static const Color redAlert = Color(0xFFDC4C45);

  // --- Semantic & Status Colors ---
  static const Color success = emerald;
  static const Color warning = orangeAccent; 
  static const Color error = redAlert; 
  static const Color info = blueAccent; 

  // Status mappings
  static const Color statusGreen = emerald; 
  static const Color statusAmber = orangeAccent; 
  static const Color statusRed = redAlert;   
  static const Color statusBlue = blueAccent;  
  static const Color coolGray = Color(0xFF64748B);

  // --- Light Theme ---
  static const Color lightBackground = Color(0xFFF7F9F8);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightCardBackground = Color(0xFFFFFFFF);
  static const Color lightOnSurface = Color(0xFF18221D); // Primary Text
  static const Color lightOnSurfaceVariant = Color(0xFF66736B); // Secondary Text
  static const Color lightMutedText = Color(0xFF8B95A5); // Muted Text
  static const Color lightBorder = Color(0xFFE4E9E6);
  static const Color lightInputFill = Color(0xFFF7F9F8);

  // --- Dark Theme ---
  static const Color darkBackground = Color(0xFF12151B);
  static const Color darkSecondaryBackground = Color(0xFF1A1F27);
  static const Color darkSurface = Color(0xFF1A1F27);
  static const Color darkCardBackground = Color(0xFF242A34); 
  static const Color darkCardElevated = Color(0xFF242A34); 
  static const Color darkPrimary = Color(0xFF16A36A); // Primary Green Dark
  static const Color darkMint = Color(0xFF0B8F5A); // Mint Green Dark
  static const Color darkOnSurface = Color(0xFFF5F7F6); // Primary Text Dark
  static const Color darkOnSurfaceVariant = Color(0xFFA8B1AC); // Secondary Text Dark
  static const Color darkBorder = Color(0xFF303743);
  static const Color darkInputFill = Color(0xFF1A1F27);
}
