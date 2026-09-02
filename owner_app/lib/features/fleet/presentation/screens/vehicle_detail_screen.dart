import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/fleet_repository.dart';
import '../providers/fleet_provider.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/info_row.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../../../../core/widgets/section_header.dart';
import '../../../../core/widgets/status_chip.dart';

class VehicleDetailScreen extends ConsumerWidget {
  final Vehicle vehicle;

  const VehicleDetailScreen({super.key, required this.vehicle});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final insightsAsync = ref.watch(vehicleInsightsProvider(vehicle.id));
    Color statusColor;
    switch (vehicle.status.toUpperCase()) {
      case 'ACTIVE': statusColor = AppColors.statusGreen; break;
      case 'IN_SHOP': statusColor = AppColors.statusAmber; break;
      case 'OUT_OF_SERVICE': statusColor = AppColors.statusRed; break;
      default: statusColor = AppColors.coolGray; break;
    }
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(vehicle.licensePlate, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          GlassCard(
            
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SectionHeader(title: 'Identity'),
                const SizedBox(height: 12),
                InfoRow(label: 'Registration', value: vehicle.licensePlate),
                InfoRow(label: 'Model', value: '${vehicle.make} ${vehicle.model}'),
                const SizedBox(height: 12),
                const Divider(),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Status', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                    StatusChip(label: vehicle.status, color: statusColor),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          
          insightsAsync.when(
            data: (insights) {
              final activeTrip = insights['active_trip'];
              final totalExpenses = insights['total_expenses'];
              final completedTrips = insights['completed_trips'] ?? 0;
              final utilization = insights['utilization_percentage'];
              final maintenance = insights['maintenance_status'];
              final location = insights['last_known_location'];

              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  GlassCard(
                    
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SectionHeader(title: 'Operations'),
                        const SizedBox(height: 12),
                        InfoRow(label: 'Current Trip', value: activeTrip != null ? '${activeTrip['origin']} → ${activeTrip['destination']}' : 'No active trip'),
                        InfoRow(label: 'Completed Trips', value: completedTrips.toString()),
                        InfoRow(label: 'Utilization', value: utilization != null ? '$utilization%' : 'Unavailable'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  GlassCard(
                    
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SectionHeader(title: 'Maintenance & Financials'),
                        const SizedBox(height: 12),
                        InfoRow(label: 'Service History', value: maintenance ?? 'Unavailable'),
                        InfoRow(label: 'Total Expenses', value: totalExpenses != null ? '₹$totalExpenses' : 'Unavailable'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  if (location == null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.location_off, color: AppColors.warning, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Vehicle location currently unavailable',
                              style: TextStyle(
                                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    ElevatedButton.icon(
                      onPressed: () {
                        final url = Uri.parse('https://www.google.com/maps/search/?api=1&query=${location['lat']},${location['lng']}');
                        launchUrl(url);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      icon: const Icon(Icons.navigation),
                      label: const Text('Navigate to Vehicle'),
                    ),
                ],
              );
            },
            loading: () => const SkeletonLoader(height: 250, borderRadius: 24),
            error: (err, stack) => ErrorStateWidget(
              message: 'Failed to load insights.',
              onRetry: () => ref.refresh(vehicleInsightsProvider(vehicle.id)),
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // Pass context to Copilot
          context.push('/copilot?contextType=vehicle&contextId=${vehicle.id}&contextLabel=${vehicle.licensePlate}');
        },
        backgroundColor: AppColors.info,
        icon: const Icon(Icons.auto_awesome, color: Colors.white),
        label: const Text('Ask Copilot', style: TextStyle(color: Colors.white)),
      ),
    );
  }
}
