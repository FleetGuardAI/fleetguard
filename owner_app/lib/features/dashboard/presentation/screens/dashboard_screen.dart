import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/providers/mock_data_provider.dart';
import '../providers/dashboard_provider.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../tracking/presentation/providers/tracking_provider.dart';

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
                  color: AppColors.primary.withOpacity(0.15),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.2),
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
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(ref, isDark),
                    const SizedBox(height: 24),
                    _buildGreeting(isDark),
                    const SizedBox(height: 32),
                    _buildFleetScoreSection(isDark),
                    const SizedBox(height: 24),
                    _buildLiveTrackingCard(ref, isDark),
                    const SizedBox(height: 24),
                    _buildPerformanceOverview(ref, isDark),
                    const SizedBox(height: 24),
                    _buildAttentionCard(isDark),
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

  Widget _buildHeader(WidgetRef ref, bool isDark) {
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
                    color: Colors.black.withOpacity(0.05),
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
              onPressed: () {},
              isDark: isDark,
            ),
            const SizedBox(width: 12),
            Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.primary, width: 2),
              ),
              child: CircleAvatar(
                radius: 18,
                backgroundImage: ref.watch(mockAvatarProvider),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildGreeting(bool isDark) {
    final hour = DateTime.now().hour;
    String timeGreeting = 'Good morning';
    if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else if (hour >= 17) {
      timeGreeting = 'Good evening';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$timeGreeting, Suryansh',
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

  Widget _buildFleetScoreSection(bool isDark) {
    return _GlassCard(
      isDark: isDark,
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          // Main Score Ring
          Expanded(
            flex: 5,
            child: Column(
              children: [
                Text(
                  'Fleet Health Score', 
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                    fontSize: 13,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 16),
                Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 110,
                      height: 110,
                      child: CircularProgressIndicator(
                        value: 0.84,
                        strokeWidth: 8,
                        strokeCap: StrokeCap.round,
                        backgroundColor: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                        color: AppColors.statusGreen,
                      ),
                    ),
                    Column(
                      children: [
                        Text(
                          '84', 
                          style: TextStyle(
                            fontSize: 36, 
                            fontWeight: FontWeight.bold,
                            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.statusGreen.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text(
                            'Good', 
                            style: TextStyle(
                              color: AppColors.statusGreen, 
                              fontWeight: FontWeight.w600, 
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ],
                    )
                  ],
                ),
              ],
            ),
          ),
          Container(
            width: 1, 
            height: 120, 
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
            margin: const EdgeInsets.symmetric(horizontal: 16),
          ),
          // Breakdown
          Expanded(
            flex: 6,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _ScoreRow(label: 'Drivers', score: 88, color: AppColors.statusGreen, isDark: isDark),
                const SizedBox(height: 16),
                _ScoreRow(label: 'Vehicles', score: 82, color: AppColors.statusGreen, isDark: isDark),
                const SizedBox(height: 16),
                _ScoreRow(label: 'Maintenance', score: 76, color: AppColors.statusAmber, isDark: isDark),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveTrackingCard(WidgetRef ref, bool isDark) {
    final locationsAsync = ref.watch(fleetLocationsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
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
        const SizedBox(height: 16),
        Container(
          height: 180,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
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

                return GoogleMap(
                  initialCameraPosition: const CameraPosition(
                    target: LatLng(28.6139, 77.2090), // Default to New Delhi or dynamic center
                    zoom: 10,
                  ),
                  markers: markers,
                  myLocationEnabled: false,
                  zoomControlsEnabled: false,
                  mapToolbarEnabled: false,
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Center(child: Text('Map Error', style: TextStyle(color: AppColors.statusRed))),
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
              _MetricCard(title: 'Active Trucks', value: kpis.totalActiveTrucks.toString(), icon: Icons.local_shipping_outlined, isDark: isDark),
              _MetricCard(title: 'Active Drivers', value: kpis.totalActiveDrivers.toString(), icon: Icons.person_outline, isDark: isDark),
              _MetricCard(title: 'Ongoing Trips', value: kpis.activeTrips.toString(), icon: Icons.route_outlined, isDark: isDark),
              _MetricCard(title: 'Monthly Spend', value: currencyFormatter.format(kpis.monthlyExpenses), icon: Icons.account_balance_wallet_outlined, isDark: isDark),
            ],
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, stack) => Center(child: Text('Failed to load KPIs: $err', style: const TextStyle(color: AppColors.statusRed))),
        ),
      ],
    );
  }

  Widget _buildAttentionCard(bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: AppColors.statusRed.withOpacity(0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.statusRed.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.statusRed.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.warning_amber_rounded, color: AppColors.statusRed),
              ),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '4 vehicles', 
                    style: TextStyle(
                      fontWeight: FontWeight.bold, 
                      fontSize: 16,
                      color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                    ),
                  ),
                  const Text(
                    'Require immediate service', 
                    style: TextStyle(color: AppColors.statusRed, fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ],
          ),
          Icon(Icons.arrow_forward_ios, color: AppColors.statusRed.withOpacity(0.7), size: 16),
        ],
      ),
    );
  }
}

class _GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final bool isDark;

  const _GlassCard({required this.child, required this.padding, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground).withOpacity(0.7),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: isDark ? Colors.white.withOpacity(0.08) : Colors.black.withOpacity(0.05),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }
}

class _GlassIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  final bool isDark;

  const _GlassIconButton({required this.icon, required this.onPressed, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(14),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onPressed: onPressed,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (isDark ? Colors.white : Colors.black).withOpacity(0.05),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: isDark ? Colors.white.withOpacity(0.1) : Colors.black.withOpacity(0.05),
                ),
              ),
              child: Icon(
                icon, 
                color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, 
                size: 22,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ScoreRow extends StatelessWidget {
  final String label;
  final int score;
  final Color color;
  final bool isDark;

  const _ScoreRow({required this.label, required this.score, required this.color, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label, 
          style: TextStyle(
            fontSize: 14, 
            fontWeight: FontWeight.w500,
            color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            score.toString(),
            style: TextStyle(
              color: color, 
              fontWeight: FontWeight.w700, 
              fontSize: 13,
            ),
          ),
        )
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final bool isDark;

  const _MetricCard({
    required this.title, 
    required this.value, 
    required this.icon,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return _GlassCard(
      isDark: isDark,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title, 
                style: TextStyle(
                  color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, 
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Icon(
                icon, 
                color: isDark ? AppColors.darkOnSurfaceVariant.withOpacity(0.5) : AppColors.lightOnSurfaceVariant.withOpacity(0.5), 
                size: 18,
              ),
            ],
          ),
          Text(
            value, 
            style: TextStyle(
              fontWeight: FontWeight.w700, 
              fontSize: 24,
              letterSpacing: -0.5,
              color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
            ),
          ),
        ],
      ),
    );
  }
}
