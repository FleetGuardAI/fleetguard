import 'package:flutter/material.dart';
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/trip_provider.dart';
import '../../data/trip_repository.dart';
import 'trip_detail_screen.dart';

import '../../../../core/widgets/empty_state_widget.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/glass_text_field.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../../../../core/widgets/status_chip.dart';

class TripsScreen extends ConsumerStatefulWidget {
  const TripsScreen({super.key});

  @override
  ConsumerState<TripsScreen> createState() => _TripsScreenState();
}

class _TripsScreenState extends ConsumerState<TripsScreen> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _showFilterBottomSheet() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    showModalBottomSheet(
      context: context,
      backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Filter by Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 16),
              Wrap(
                spacing: 8.0,
                runSpacing: 8.0,
                children: ['ALL', 'CREATED', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'CANCELLED'].map((status) {
                  final currentStatus = ref.watch(tripStatusProvider);
                  final isSelected = currentStatus == status;
                  return ChoiceChip(
                    label: Text(status.replaceAll('_', ' ')),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        ref.read(tripStatusProvider.notifier).state = status;
                        Navigator.pop(context);
                      }
                    },
                    selectedColor: AppColors.primary.withValues(alpha: 0.2),
                    labelStyle: TextStyle(color: isSelected ? AppColors.primary : (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tripsAsync = ref.watch(fleetTripsProvider);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Active Trips', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        actions: [
          IconButton(
            icon: Icon(Icons.filter_list, color: ref.watch(tripStatusProvider) != 'ALL' ? AppColors.primary : (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            onPressed: _showFilterBottomSheet,
            tooltip: 'Filter trips',
          )
        ],
      ),
      body: tripsAsync.when(
        data: (trips) {
          final status = ref.watch(tripStatusProvider);
          if (trips.isEmpty) {
            return EmptyStateWidget(
              icon: Icons.route,
              title: 'No Trips Found',
              message: status == 'ALL' 
                  ? 'Your fleet has no recorded trips yet.' 
                  : 'No trips found with status "${status.replaceAll('_', ' ')}".',
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(fleetTripsProvider);
            },
            child: ListView.separated(
              padding: const EdgeInsets.all(16.0),
              itemCount: trips.length + 1,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                if (index == 0) {
                  return GlassTextField(
                    controller: _searchController,
                    hintText: 'Search trips...',
                    prefixIcon: Icons.search,
                    onChanged: (value) {
                      if (_debounce?.isActive ?? false) _debounce!.cancel();
                      _debounce = Timer(const Duration(milliseconds: 500), () {
                        ref.read(tripSearchProvider.notifier).state = value;
                      });
                    },
                    onClear: () {
                      _searchController.clear();
                      ref.read(tripSearchProvider.notifier).state = '';
                    },
                  );
                }
                final trip = trips[index - 1];
                
                // Construct display strings safely
                final origin = trip.originLocation ?? 'Unknown Origin';
                final destination = trip.destinationLocation ?? 'Unknown Destination';
                final route = '$origin → $destination';
                
                final truck = trip.vehicle?['registration_number'] ?? 'Unassigned Truck';
                
                Color statusColor;
                switch (trip.status) {
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

                return _buildTripCard(
                  context,
                  trip,
                  truck,
                  route,
                  trip.status.replaceAll('_', ' '),
                  statusColor,
                  isDark,
                );
              },
            ),
          );
        },
        loading: () => ListView.separated(
          padding: const EdgeInsets.all(16.0),
          itemCount: 4,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (_, __) => const SkeletonLoader(height: 120, borderRadius: 16),
        ),
        error: (err, stack) => ErrorStateWidget(
          message: 'Failed to load trips.',
          onRetry: () => ref.refresh(fleetTripsProvider),
        ),
      ),
    );
  }

  Widget _buildTripCard(BuildContext context, OwnerTrip trip, String truck, String route, String status, Color statusColor, bool isDark) {
    return InkWell(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: (_) => TripDetailScreen(trip: trip)));
      },
      child: GlassCard(
        
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(trip.tripId, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold, fontSize: 16)),
                StatusChip(
                  label: status,
                  color: statusColor,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.local_shipping, size: 16, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                const SizedBox(width: 8),
                Text(truck, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.route, size: 16, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                const SizedBox(width: 8),
                Expanded(child: Text(route, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.w600))),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
