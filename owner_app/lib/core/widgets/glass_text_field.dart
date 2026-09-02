import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class GlassTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hintText;
  final IconData? prefixIcon;
  final VoidCallback? onClear;
  final ValueChanged<String>? onChanged;

  const GlassTextField({
    super.key,
    required this.controller,
    required this.hintText,
    this.prefixIcon,
    this.onClear,
    this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      decoration: BoxDecoration(
        color: (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground).withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: TextField(
        controller: controller,
        style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        onChanged: onChanged,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
          prefixIcon: prefixIcon != null ? Icon(prefixIcon, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant) : null,
          suffixIcon: onClear != null && controller.text.isNotEmpty
              ? IconButton(
                  icon: Icon(Icons.clear, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                  onPressed: onClear,
                  tooltip: 'Clear search',
                )
              : null,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
      ),
    );
  }
}
