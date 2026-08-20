import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/fleet_repository.dart';

class VehicleDetailScreen extends StatelessWidget {
  final Vehicle vehicle;

  const VehicleDetailScreen({super.key, required this.vehicle});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
      appBar: AppBar(
        title: Text(vehicle.licensePlate, style: const TextStyle(color: Colors.white)),
        backgroundColor: AppColors.backgroundDark,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildInfoCard('Overview', [
            _buildRow('Registration', vehicle.licensePlate),
            _buildRow('Model', '${vehicle.make} ${vehicle.model}'),
            _buildRow('Status', vehicle.status),
          ]),
          const SizedBox(height: 16),
          _buildInfoCard('Operations', [
            _buildRow('Current Trip', 'N/A'), // Waiting on backend expansion
            _buildRow('Utilization', 'N/A'),
          ]),
          const SizedBox(height: 16),
          _buildInfoCard('Maintenance & Financials', [
            _buildRow('Service History', 'Up to date'),
            _buildRow('Total Expenses', 'Unavailable'),
          ]),
        ],
      ),
    );
  }

  Widget _buildInfoCard(String title, List<Widget> children) {
    return Card(
      color: AppColors.surfaceDark,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.bold, fontSize: 14)),
            const Divider(color: Colors.white10, height: 24),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70)),
          Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
