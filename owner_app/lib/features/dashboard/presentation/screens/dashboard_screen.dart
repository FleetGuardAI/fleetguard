import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/metric_card.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../providers/dashboard_provider.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../../tracking/presentation/providers/tracking_provider.dart';
import '../../../../core/services/auth_service.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      body: Stack(
        children: [
          // Background Gradient / Ambient Light
          if (isDark)
            Positioned(
              top: -100,
              left: -100,
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.primary.withValues(alpha: 0.15),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.2),
                      blurRadius: 100,
                      spreadRadius: 100,
                    )
                  ]
                ),
              ),
            ),
          
          SafeArea(
            child: RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(dashboardKPIsProvider);
                await ref.read(dashboardKPIsProvider.future);
                ref.invalidate(recentActivityProvider);
                await ref.read(recentActivityProvider.future);
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(context, ref, isDark),
                    const SizedBox(height: 24),
                    _buildGreeting(ref, isDark),
                    const SizedBox(height: 24),
                    _buildAttentionRequired(ref, isDark),
                    const SizedBox(height: 24),
                    _buildPerformanceOverview(ref, isDark),
                    const SizedBox(height: 24),
                    _buildLiveTrackingCard(context, ref, isDark),
                    const SizedBox(height: 24),
                    _buildRecentActivity(ref, isDark),
                    const SizedBox(height: 100), // Bottom padding for glass nav
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAttentionRequired(WidgetRef ref, bool isDark) {
    final kpisAsync = ref.watch(dashboardKPIsProvider);
    return kpisAsync.when(
      data: (kpis) {
        if (kpis.attentionRequired == 0) return const SizedBox.shrink();
        
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.statusRed.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.statusRed.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.statusRed.withValues(alpha: 0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.warning_amber_rounded, color: AppColors.statusRed),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Attention Required',
                      style: TextStyle(
                        color: AppColors.statusRed,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'You have ${kpis.attentionRequired} pending issue${kpis.attentionRequired > 1 ? 's' : ''} to review.',
                      style: TextStyle(
                        color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 16, color: AppColors.statusRed),
            ],
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  Widget _buildRecentActivity(WidgetRef ref, bool isDark) {
    final activityAsync = ref.watch(recentActivityProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Recent Activity', 
          style: TextStyle(
            fontSize: 18, 
            fontWeight: FontWeight.w700,
            letterSpacing: -0.5,
            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
          ),
        ),
        const SizedBox(height: 16),
        activityAsync.when(
          data: (activities) {
            if (activities.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Text(
                    'No recent activity.',
                    style: TextStyle(
                      color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                    ),
                  ),
                ),
              );
            }
            return ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: activities.length,
              separatorBuilder: (context, index) => Divider(
                color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                height: 24,
              ),
              itemBuilder: (context, index) {
                final item = activities[index];
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                      ),
                      child: Icon(
                        item.type == 'ticket' ? Icons.report_problem_outlined : Icons.info_outline,
                        color: item.status == 'pending' ? AppColors.warning : AppColors.primary,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.title,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                              color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            item.description,
                            style: TextStyle(
                              color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                              fontSize: 13,
                            ),
                          ),
                          if (item.timestamp != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              _formatTime(item.timestamp!),
                              style: TextStyle(
                                color: isDark ? AppColors.darkOnSurfaceVariant.withValues(alpha: 0.5) : AppColors.lightOnSurfaceVariant.withValues(alpha: 0.5),
                                fontSize: 11,
                              ),
                            ),
                          ]
                        ],
                      ),
                    ),
                  ],
                );
              },
            );
          },
          loading: () => ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: 3,
            separatorBuilder: (context, index) => const SizedBox(height: 16),
            itemBuilder: (context, index) => const SkeletonLoader(height: 72, borderRadius: 12),
          ),
          error: (err, stack) => ErrorStateWidget(
            message: 'Failed to load activity.',
            onRetry: () => ref.refresh(recentActivityProvider),
          ),
        ),
      ],
    );
  }

  String _formatTime(String timestamp) {
    try {
      final dt = DateTime.parse(timestamp).toLocal();
      return DateFormat('MMM d, yyyy • h:mm a').format(dt);
    } catch (_) {
      return timestamp;
    }
  }

  Widget _buildHeader(BuildContext context, WidgetRef ref, bool isDark) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCardBackground : Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.asset(
                  'assets/images/owner_logo.png',
                  width: 32,
                  height: 32,
                  fit: BoxFit.contain,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Text(
              'FleetGuard',
              style: TextStyle(
                fontSize: 22, 
                fontWeight: FontWeight.w700,
                letterSpacing: -0.5,
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
              ),
            ),
          ],
        ),
        Row(
          children: [
            _GlassIconButton(
              icon: Icons.notifications_outlined,
              onPressed: () => context.push('/notifications'),
              isDark: isDark,
              semanticLabel: 'Open notifications',
            ),
            const SizedBox(width: 12),
            Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.primary, width: 2),
              ),
              child: InkWell(
                onTap: () => _showProfileSheet(context, ref, isDark),
                borderRadius: BorderRadius.circular(20),
                child: const CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.primary,
                  child: Icon(Icons.person, color: Colors.white, size: 20),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  void _showProfileSheet(BuildContext context, WidgetRef ref, bool isDark) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) {
        final userProfileAsync = ref.watch(userProfileProvider);
        
        return Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkBackground : AppColors.lightBackground,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 48,
                  height: 4,
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  const CircleAvatar(
                    radius: 32,
                    backgroundColor: AppColors.primary,
                    child: Icon(Icons.person, size: 36, color: Colors.white),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: userProfileAsync.when(
                      data: (user) {
                        if (user == null) {
                          return const Text('Profile not available');
                        }
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user.fullName,
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Role: ${user.role.toUpperCase()}',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: AppColors.primary,
                              ),
                            ),
                          ],
                        );
                      },
                      loading: () => const SkeletonLoader(height: 48, width: 150),
                      error: (_, __) => const Text('Error loading profile'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  ref.read(authServiceProvider).logout();
                },
                icon: const Icon(Icons.logout),
                label: const Text('Logout'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.statusRed,
                  side: const BorderSide(color: AppColors.statusRed),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        );
      },
    );
  }

  Widget _buildGreeting(WidgetRef ref, bool isDark) {
    final hour = DateTime.now().hour;
    String timeGreeting = 'Good morning';
    if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else if (hour >= 17) {
      timeGreeting = 'Good evening';
    }

    final userProfileAsync = ref.watch(userProfileProvider);
    final userName = userProfileAsync.valueOrNull?.fullName ?? 'Owner';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$timeGreeting, $userName',
          style: TextStyle(
            fontSize: 28, 
            fontWeight: FontWeight.bold,
            letterSpacing: -0.5,
            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          "Fleet operations are running smoothly today.",
          style: TextStyle(
            color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, 
            fontSize: 15,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }



  Widget _buildLiveTrackingCard(BuildContext context, WidgetRef ref, bool isDark) {
    final locationsAsync = ref.watch(fleetLocationsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Live Tracking', 
              style: TextStyle(
                fontSize: 18, 
                fontWeight: FontWeight.w700,
                letterSpacing: -0.5,
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
              ),
            ),
            TextButton.icon(
              onPressed: () => context.push('/tracking'),
              icon: const Icon(Icons.fullscreen, size: 20),
              label: const Text('Full Map'),
              style: TextButton.styleFrom(
                foregroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          height: 180,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 15,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: locationsAsync.when(
              data: (locations) {
                // Determine bounds
                final markers = locations.map((loc) {
                  return Marker(
                    markerId: MarkerId(loc.driverId.toString()),
                    position: LatLng(loc.latitude, loc.longitude),
                    infoWindow: InfoWindow(title: loc.driverName, snippet: loc.dutyStatus),
                  );
                }).toSet();
                
                LatLng center = locations.isNotEmpty ? LatLng(locations.first.latitude, locations.first.longitude) : const LatLng(28.6139, 77.2090);

                return GoogleMap(
                  initialCameraPosition: CameraPosition(
                    target: center,
                    zoom: locations.isNotEmpty ? 10 : 4,
                  ),
                  markers: markers,
                  myLocationEnabled: false,
                  zoomControlsEnabled: false,
                  mapToolbarEnabled: false,
                );
              },
              loading: () => const SkeletonLoader(height: 180, borderRadius: 24),
              error: (err, stack) => const Center(child: Text('Map Error', style: TextStyle(color: AppColors.error))),
            ),
          ),
        )
      ],
    );
  }

  Widget _buildPerformanceOverview(WidgetRef ref, bool isDark) {
    final kpisAsync = ref.watch(dashboardKPIsProvider);
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Operational Metrics', 
          style: TextStyle(
            fontSize: 18, 
            fontWeight: FontWeight.w700,
            letterSpacing: -0.5,
            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
          ),
        ),
        const SizedBox(height: 16),
        kpisAsync.when(
          data: (kpis) => GridView.count(
            shrinkWrap: true,
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: 1.4,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              MetricCard(title: 'Active Trucks', value: kpis.totalActiveTrucks.toString(), icon: Icons.local_shipping_outlined),
              MetricCard(title: 'Active Drivers', value: kpis.totalActiveDrivers.toString(), icon: Icons.person_outline),
              MetricCard(title: 'Ongoing Trips', value: kpis.activeTrips.toString(), icon: Icons.route_outlined),
              MetricCard(title: 'Monthly Spend', value: currencyFormatter.format(kpis.monthlyExpenses), icon: Icons.account_balance_wallet_outlined),
            ],
          ),
          loading: () => GridView.count(
            shrinkWrap: true,
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: 1.4,
            physics: const NeverScrollableScrollPhysics(),
            children: List.generate(4, (index) => const SkeletonLoader(height: 100, borderRadius: 24)),
          ),
          error: (err, stack) => ErrorStateWidget(
            message: 'Failed to load KPIs.',
            onRetry: () => ref.refresh(dashboardKPIsProvider),
          ),
        ),
      ],
    );
  }
}

class _GlassIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  final bool isDark;
  final String? semanticLabel;

  const _GlassIconButton({required this.icon, required this.onPressed, required this.isDark, this.semanticLabel});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(14),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
                      onTap: onPressed,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (isDark ? Colors.white : Colors.black).withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.black.withValues(alpha: 0.05),
                ),
              ),
              child: Icon(
                icon, 
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, 
                size: 22,
                semanticLabel: semanticLabel,
              ),
            ),
          ),
        ),
      ),
    );
  }
}




