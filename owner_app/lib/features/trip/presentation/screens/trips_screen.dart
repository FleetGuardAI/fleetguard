import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../providers/trip_provider.dart';
import '../../data/trip_repository.dart';

class TripsScreen extends ConsumerWidget {
  const TripsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripsAsync = ref.watch(fleetTripsProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(title: const Text('Active Trips')),
      body: tripsAsync.when(
        data: (trips) {
          if (trips.isEmpty) {
            return const Center(
              child: Text('No trips found for your fleet.', style: TextStyle(color: AppTheme.textSecondary)),
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(fleetTripsProvider);
            },
            child: ListView.separated(
              padding: const EdgeInsets.all(16.0),
              itemCount: trips.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final trip = trips[index];
                
                // Construct display strings safely
                final origin = trip.originLocation ?? 'Unknown Origin';
                final destination = trip.destinationLocation ?? 'Unknown Destination';
                final route = '$origin → $destination';
                
                final truck = trip.vehicle?['registration_number'] ?? 'Unassigned Truck';
                
                Color statusColor;
                switch (trip.status) {
                  case 'COMPLETED':
                    statusColor = AppTheme.primaryGreen;
                    break;
                  case 'IN_PROGRESS':
                    statusColor = AppTheme.primaryGreen;
                    break;
                  case 'PAUSED':
                  case 'DELAYED':
                    statusColor = AppTheme.warningAmber;
                    break;
                  case 'CANCELLED':
                    statusColor = AppTheme.errorRed;
                    break;
                  case 'CREATED':
                  default:
                    statusColor = AppTheme.textSecondary;
                    break;
                }

                return _buildTripCard(
                  trip.tripId,
                  truck,
                  route,
                  trip.status.replaceAll('_', ' '),
                  statusColor,
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Failed to load trips: $err', textAlign: TextAlign.center),
              TextButton(
                onPressed: () => ref.invalidate(fleetTripsProvider),
                child: const Text('Retry'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTripCard(String tripId, String truck, String route, String status, Color statusColor) {
    return InkWell(
      onTap: () {},
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 5, offset: const Offset(0, 2)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(tripId, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(status, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12)),
                )
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.local_shipping, size: 16, color: AppTheme.textSecondary),
                const SizedBox(width: 8),
                Text(truck, style: const TextStyle(color: AppTheme.textSecondary)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.route, size: 16, color: AppTheme.textSecondary),
                const SizedBox(width: 8),
                Text(route, style: const TextStyle(fontWeight: FontWeight.w600)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
