import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/trip_repository.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/info_row.dart';
import '../../../../core/widgets/section_header.dart';
import '../../../../core/widgets/status_chip.dart';

class TripDetailScreen extends StatefulWidget {
  final OwnerTrip trip;

  const TripDetailScreen({super.key, required this.trip});

  @override
  State<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends State<TripDetailScreen> {
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    Color statusColor;
    switch (widget.trip.status) {
      case 'COMPLETED':
        statusColor = AppColors.statusGreen;
        break;
      case 'IN_PROGRESS':
        statusColor = AppColors.statusBlue;
        break;
      case 'PAUSED':
      case 'DELAYED':
        statusColor = AppColors.statusAmber;
        break;
      case 'CANCELLED':
        statusColor = AppColors.statusRed;
        break;
      case 'CREATED':
      default:
        statusColor = AppColors.coolGray;
        break;
    }

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(widget.trip.tripId, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
      ),
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Container(
              padding: const EdgeInsets.all(24.0),
              color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
              child: Column(
                children: [
                  const Icon(Icons.route, size: 48, color: AppColors.primary),
                  const SizedBox(height: 16),
                  Text(
                    '${widget.trip.originLocation ?? "Unknown"} → ${widget.trip.destinationLocation ?? "Unknown"}',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.warning.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.location_off, color: AppColors.warning, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Trip Route Map Unavailable (No Telemetry)',
                          style: TextStyle(
                            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  )
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16.0),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                GlassCard(
                  
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Route Info'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Origin', value: widget.trip.originLocation ?? 'N/A'),
                      InfoRow(label: 'Destination', value: widget.trip.destinationLocation ?? 'N/A'),
                      const SizedBox(height: 12),
                      const Divider(),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Status', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                          StatusChip(label: widget.trip.status.replaceAll('_', ' '), color: statusColor),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                GlassCard(
                  
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Assignments'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Truck', value: widget.trip.vehicle?['registration_number'] ?? 'Unassigned'),
                      InfoRow(label: 'Driver', value: widget.trip.driver?['name'] ?? 'Unassigned'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                GlassCard(
                  
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Schedule'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Scheduled Start', value: widget.trip.plannedStartTime ?? 'N/A'),
                      InfoRow(label: 'Actual Start', value: widget.trip.actualStartTime ?? 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                GlassCard(
                  
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Statistics'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Planned Distance', value: widget.trip.plannedDistance != null ? '${widget.trip.plannedDistance} km' : 'N/A'),
                      InfoRow(label: 'Actual Distance', value: widget.trip.actualDistance != null ? '${widget.trip.actualDistance} km' : 'N/A'),
                      InfoRow(label: 'Cargo Weight', value: widget.trip.cargoWeight != null ? '${widget.trip.cargoWeight} kg' : 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                GlassCard(
                  
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Financials'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Revenue', value: widget.trip.revenue != null ? '₹${widget.trip.revenue}' : 'N/A'),
                      InfoRow(label: 'Planned Cost', value: widget.trip.plannedCost != null ? '₹${widget.trip.plannedCost}' : 'N/A'),
                      InfoRow(label: 'Planned Fuel', value: widget.trip.plannedFuelLiters != null ? '${widget.trip.plannedFuelLiters} L' : 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 80),
              ]),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // Pass context to Copilot
          context.push('/copilot?contextType=trip&contextId=${widget.trip.tripId}&contextLabel=${widget.trip.tripId}');
        },
        backgroundColor: AppColors.info,
        icon: const Icon(Icons.auto_awesome, color: Colors.white),
        label: const Text('Ask Copilot', style: TextStyle(color: Colors.white)),
      ),
    );
  }
}
