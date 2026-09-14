import 'package:flutter/material.dart';

extension NavigationSafeArea on BuildContext {
  /// Returns the required bottom clearance for scroll views to ensure the 
  /// last item can scroll completely above the floating glassmorphic navigation bar.
  /// 
  /// The physical height of the floating navigation bar including its own bottom padding,
  /// but NOT including the system safe area.
  double get floatingNavBarHeight => 64.0 + 16.0;

  /// The total clearance needed for SCROLLABLE content to sit above the navigation bar
  /// when scrolled to the very bottom.
  double get scrollContentClearance => 
      MediaQuery.of(this).padding.bottom + floatingNavBarHeight + 16.0; // 16px extra visual padding

  /// The bottom padding required for FIXED UI controls (like FABs or input fields)
  /// so they sit nicely above the floating navigation bar.
  /// If the keyboard is open, this returns 0 because the keyboard pushes the fixed control up anyway.
  double get fixedControlClearance {
    final bottomInset = MediaQuery.of(this).viewInsets.bottom;
    if (bottomInset > 0) return 0.0; // Keyboard is open
    return MediaQuery.of(this).padding.bottom + floatingNavBarHeight + 16.0;
  }
}
