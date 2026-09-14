import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../trip/presentation/providers/trip_provider.dart';
import '../../../trip/data/trip_intelligence_repository.dart';
import '../../../trip/data/trip_intelligence_models.dart';
import '../../../trip/data/trip_repository.dart';

class TripIntelligenceDashboardCard extends ConsumerStatefulWidget {
  const TripIntelligenceDashboardCard({super.key});

  @override
  ConsumerState<TripIntelligenceDashboardCard> createState() => _TripIntelligenceDashboardCardState();
}

class _TripIntelligenceDashboardCardState extends ConsumerState<TripIntelligenceDashboardCard> {
  bool _isLoading = false;
  LiveTripIntelligenceResponse? _singleTripIntel;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tripsAsync = ref.watch(fleetTripsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Trip Intelligence',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.5,
            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
          ),
        ),
        const SizedBox(height: 16),
        tripsAsync.when(
          data: (trips) {
            final activeTrips = trips.where((t) => t.status == 'IN_PROGRESS' || t.status == 'PAUSED').toList();
            if (activeTrips.isEmpty) {
              return _buildEmptyState(isDark);
            } else if (activeTrips.length == 1) {
              return _buildSingleTripCard(activeTrips.first, isDark);
            } else {
              return _buildMultipleTripsCard(activeTrips, isDark);
            }
          },
          loading: () => const SkeletonLoader(height: 180, borderRadius: 24),
          error: (_, __) => const GlassCard(
            padding: EdgeInsets.all(16),
            child: Text('Trip intelligence unavailable because trip data could not be loaded.', style: TextStyle(color: AppColors.error)),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState(bool isDark) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
      child: Center(
        child: Column(
          children: [
            Icon(Icons.auto_awesome, size: 48, color: isDark ? AppColors.darkOnSurfaceVariant.withValues(alpha: 0.5) : AppColors.lightOnSurfaceVariant.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            Text(
              'No Active Trip Intelligence',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
            ),
            const SizedBox(height: 8),
            Text(
              'Trip insights will appear here when\nyour fleet begins a trip.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSingleTripCard(OwnerTrip trip, bool isDark) {
    // If not loaded yet, fetch it
    if (_singleTripIntel == null && !_isLoading) {
      _loadSingleTripIntel(trip.id);
    }

    final String origin = trip.originLocation ?? 'Unknown';
    final String destination = trip.destinationLocation ?? 'Unknown';

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Trip: $origin → $destination',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text('ACTIVE', style: TextStyle(color: AppColors.primary, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 20),
          if (_isLoading || _singleTripIntel == null)
            const Center(child: Padding(padding: EdgeInsets.all(16.0), child: CircularProgressIndicator()))
          else ...[
            Builder(
              builder: (context) {
                final healthStatus = _singleTripIntel!.healthStatus;
                final score = healthStatus == 'ON_TRACK' ? 95 : (healthStatus == 'AT_RISK' ? 65 : 40);
                
                final hasVehicleDev = _singleTripIntel!.deviations.any((d) => d.metric.toLowerCase().contains('vehicle'));
                final hasDriverDev = _singleTripIntel!.deviations.any((d) => d.metric.toLowerCase().contains('driver') || d.metric.toLowerCase().contains('speed'));
                final hasRouteDev = _singleTripIntel!.deviations.any((d) => d.metric.toLowerCase().contains('route') || d.metric.toLowerCase().contains('time'));

                return Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _getColorForScore(score).withValues(alpha: 0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Column(
                        children: [
                          Text(
                            '$score%',
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: _getColorForScore(score)),
                          ),
                          Text('Health', style: TextStyle(fontSize: 10, color: _getColorForScore(score))),
                        ],
                      ),
                    ),
                    const SizedBox(width: 24),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildCheckListItem('Vehicle', !hasVehicleDev, isDark),
                          _buildCheckListItem('Driver', !hasDriverDev, isDark),
                          _buildCheckListItem('Route', !hasRouteDev, isDark),
                        ],
                      ),
                    ),
                  ],
                );
              }
            ),
          ],
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => context.push('/trips'), // In a real app, might navigate directly to trip detail
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
              ),
              child: const Text('View Live Intelligence →'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMultipleTripsCard(List<OwnerTrip> activeTrips, bool isDark) {
    // For multiple, we could just show a summary. Mocking healthy vs needs attention for now.
    final healthyCount = activeTrips.length > 1 ? activeTrips.length - 1 : activeTrips.length;
    final attentionCount = activeTrips.length - healthyCount;

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, color: AppColors.primary),
              const SizedBox(width: 8),
              Text('${activeTrips.length} Active Trips', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: AppColors.statusGreen.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      Text(healthyCount.toString(), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.statusGreen)),
                      const Text('Healthy', style: TextStyle(color: AppColors.statusGreen, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: attentionCount > 0 ? AppColors.statusAmber.withValues(alpha: 0.1) : AppColors.statusGreen.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      Text(attentionCount.toString(), style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: attentionCount > 0 ? AppColors.statusAmber : AppColors.statusGreen)),
                      Text(attentionCount > 0 ? 'Needs Attention' : 'All Clear', style: TextStyle(color: attentionCount > 0 ? AppColors.statusAmber : AppColors.statusGreen, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => context.push('/trips'),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
              ),
              child: const Text('View All Trips →'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckListItem(String label, bool isOk, bool isDark) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6.0),
      child: Row(
        children: [
          Icon(isOk ? Icons.check_circle : Icons.warning, size: 16, color: isOk ? AppColors.statusGreen : AppColors.statusAmber),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(fontSize: 14, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
          const Spacer(),
          Text(isOk ? 'Healthy' : 'Attention', style: TextStyle(fontSize: 12, color: isOk ? AppColors.statusGreen : AppColors.statusAmber, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Color _getColorForScore(int score) {
    if (score >= 85) return AppColors.statusGreen;
    if (score >= 65) return AppColors.statusAmber;
    return AppColors.statusRed;
  }

  Future<void> _loadSingleTripIntel(int tripId) async {
    setState(() => _isLoading = true);
    try {
      final intelRepo = ref.read(tripIntelligenceRepositoryProvider);
      final intel = await intelRepo.getLiveTripIntelligence(tripId);
      if (mounted) {
        setState(() => _singleTripIntel = intel);
      }
    } catch (e) {
      debugPrint('Failed to load live intel: $e');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }
}
