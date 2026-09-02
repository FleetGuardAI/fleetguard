import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:fleetguard_owner/l10n/app_localizations.dart';
import '../../../../core/theme/app_colors.dart';
import 'dart:ui';

class ScaffoldWithNavBar extends StatelessWidget {
  const ScaffoldWithNavBar({
    required this.child,
    super.key,
  });

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final loc = AppLocalizations.of(context)!;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currentIndex = _calculateSelectedIndex(context);

    return Scaffold(
      body: child,
      extendBody: true, // Allow body to flow behind the bottom nav bar
      bottomNavigationBar: SafeArea(
        bottom: true,
        child: Container(
          margin: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkCardBackground.withValues(alpha: 0.8) : AppColors.lightCardBackground.withValues(alpha: 0.9),
            borderRadius: BorderRadius.circular(32),
            border: Border.all(
              color: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.black.withValues(alpha: 0.05),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(32),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildNavItem(context, Icons.home, loc.home, 0, currentIndex, isDark),
                    _buildNavItem(context, Icons.local_shipping, loc.fleet, 1, currentIndex, isDark),
                    _buildNavItem(context, Icons.route, loc.trips, 2, currentIndex, isDark),
                    _buildNavItem(context, Icons.account_balance_wallet, loc.finance, 3, currentIndex, isDark),
                    _buildNavItem(context, Icons.auto_awesome, 'Copilot', 4, currentIndex, isDark),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(BuildContext context, IconData icon, String label, int index, int currentIndex, bool isDark) {
    final isSelected = index == currentIndex;
    
    return Semantics(
      label: label,
      selected: isSelected,
      child: GestureDetector(
        onTap: () => _onItemTapped(index, context),
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOutCubic,
          padding: EdgeInsets.symmetric(horizontal: isSelected ? 16 : 12, vertical: 8),
          decoration: BoxDecoration(
            color: isSelected 
                ? (isDark ? AppColors.primary.withValues(alpha: 0.2) : AppColors.primary.withValues(alpha: 0.15))
                : Colors.transparent,
            borderRadius: BorderRadius.circular(24),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 24,
                color: isSelected 
                    ? AppColors.primary 
                    : (isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
              ),
              if (isSelected) ...[
                const SizedBox(width: 6),
                Text(
                  label,
                  style: TextStyle(
                    color: isDark ? AppColors.darkOnSurface : AppColors.primary,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ]
            ],
          ),
        ),
      ),
    );
  }

  static int _calculateSelectedIndex(BuildContext context) {
    final String location = GoRouterState.of(context).uri.toString();
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/fleet')) return 1;
    if (location.startsWith('/trips')) return 2;
    if (location.startsWith('/finance')) return 3;
    if (location.startsWith('/copilot')) return 4;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/dashboard');
        break;
      case 1:
        context.go('/fleet');
        break;
      case 2:
        context.go('/trips');
        break;
      case 3:
        context.go('/finance');
        break;
      case 4:
        context.go('/copilot');
        break;
    }
  }
}
