import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/fleet_repository.dart';

class DriverDetailScreen extends StatelessWidget {
  final Driver driver;

  const DriverDetailScreen({super.key, required this.driver});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(driver.name, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildInfoCard('Personal Information', [
            _buildRow('Phone Number', driver.phoneNumber, isDark),
            _buildRow('Status', driver.status, isDark),
          ], isDark),
          const SizedBox(height: 16),
          _buildInfoCard('Operations', [
            _buildRow('Current Trip', 'N/A', isDark), // Waiting on backend expansion
            _buildRow('Vehicle Assigned', 'N/A', isDark),
          ], isDark),
          const SizedBox(height: 16),
          _buildInfoCard('Documents & Compliance', [
            _buildRow('License', 'Verified', isDark),
            _buildRow('Background Check', 'Pending', isDark),
          ], isDark),
        ],
      ),
    );
  }

  Widget _buildInfoCard(String title, List<Widget> children, bool isDark) {
    return Card(
      color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontWeight: FontWeight.bold, fontSize: 14)),
            Divider(color: isDark ? AppColors.darkBorder : AppColors.lightBorder, height: 24),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
          Text(value, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
