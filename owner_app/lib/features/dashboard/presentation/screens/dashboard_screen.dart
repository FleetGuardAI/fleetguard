import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/metric_card.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../providers/dashboard_provider.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../../core/config/app_config.dart';
import '../../../tracking/presentation/providers/tracking_provider.dart';
import '../../../../core/services/auth_service.dart';
import '../widgets/trip_intelligence_dashboard_card.dart';
import '../../../../core/utils/navigation_safe_area.dart';

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
                    _buildPerformanceOverview(context, ref, isDark),
                    const SizedBox(height: 24),
                    const TripIntelligenceDashboardCard(),
                    const SizedBox(height: 24),
                    _buildLiveTrackingCard(context, ref, isDark),
                    const SizedBox(height: 24),
                    _buildRecentActivity(ref, isDark),
                    SizedBox(height: context.scrollContentClearance), // Dynamic bottom padding for glass nav
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
        if (kpis.attentionRequired > 0) {
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.error.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.error.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.error.withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.warning_amber_rounded, color: AppColors.error),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Attention Required',
                        style: TextStyle(
                          color: AppColors.error,
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'You have ${kpis.attentionRequired} pending issue${kpis.attentionRequired > 1 ? 's' : ''} to review.',
                        style: TextStyle(
                          color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios, size: 16, color: AppColors.error),
              ],
            ),
          );
        }
        
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkMint.withValues(alpha: 0.15) : AppColors.lightMint,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: isDark ? AppColors.darkMint.withValues(alpha: 0.3) : AppColors.primary.withValues(alpha: 0.1)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check, color: Colors.white, size: 20),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'All systems operational',
                      style: TextStyle(
                        color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Your fleet is running smoothly.',
                      style: TextStyle(
                        color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, size: 20, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
            ],
          ),
        );
      },
      loading: () => const SkeletonLoader(height: 80, borderRadius: 20),
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
                onTap: () => context.push('/profile'),
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
          '$timeGreeting,\n$userName 👋',
          style: TextStyle(
            fontSize: 28, 
            fontWeight: FontWeight.bold,
            letterSpacing: -0.5,
            height: 1.2,
            color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "Your fleet is on the move. Here's today's overview.",
          style: TextStyle(
            color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, 
            fontSize: 15,
            fontWeight: FontWeight.w400,
          ),
        ),
        const SizedBox(height: 24),
        // Hero landscape placeholder
        Container(
          width: double.infinity,
          height: 140,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            gradient: const LinearGradient(
              colors: [AppColors.emerald, AppColors.primaryDark],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Stack(
            children: [
              Positioned(
                bottom: 16,
                left: 20,
                child: Text(
                  '"Safer Journeys\nStronger Businesses"',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.9),
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
              Positioned(
                right: -20,
                bottom: 0,
                child: Icon(Icons.local_shipping, size: 120, color: Colors.white.withValues(alpha: 0.15)),
              ),
            ],
          ),
        ),
      ],
    );
  }



  Widget _buildLiveTrackingCard(BuildContext context, WidgetRef ref, bool isDark) {
    final mapsApiKey = AppConfig.geoapifyApiKey;
    if (mapsApiKey.isEmpty) {
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
            ],
          ),
          const SizedBox(height: 8),
          Container(
            height: 180,
            width: double.infinity,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
              color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
            ),
            child: const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Text('Map unavailable — map configuration is missing.', style: TextStyle(color: AppColors.error), textAlign: TextAlign.center),
              ),
            ),
          )
        ],
      );
    }

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
                final geoapifyKey = AppConfig.geoapifyApiKey;
                if (geoapifyKey.isEmpty) {
                  return const Center(child: Text('Map unavailable - API key is missing.', style: TextStyle(color: AppColors.statusRed)));
                }

                LatLng center = locations.isNotEmpty ? LatLng(locations.first.latitude, locations.first.longitude) : const LatLng(28.6139, 77.2090);

                return FlutterMap(
                  options: MapOptions(
                    initialCenter: center,
                    initialZoom: locations.isNotEmpty ? 10.0 : 4.0,
                    interactionOptions: const InteractionOptions(
                      flags: InteractiveFlag.none,
                    ),
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: 'https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png?apiKey={apiKey}',
                      additionalOptions: {
                        'apiKey': geoapifyKey,
                      },
                      userAgentPackageName: 'com.example.fleetguard_owner',
                    ),
                    MarkerLayer(markers: locations.map((loc) {
                      return Marker(
                        point: LatLng(loc.latitude, loc.longitude),
                        width: 40,
                        height: 40,
                        child: const Icon(
                          Icons.local_shipping,
                          color: AppColors.statusGreen,
                          size: 30,
                        ),
                      );
                    }).toList()),
                  ],
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

  Widget _buildPerformanceOverview(BuildContext context, WidgetRef ref, bool isDark) {
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
              MetricCard(
                title: 'Active Trucks', 
                value: kpis.totalActiveTrucks.toString(), 
                icon: Icons.local_shipping, 
                trend: '↑ +2', 
                isTrendPositive: true,
                iconBackgroundColor: isDark ? AppColors.darkMint.withValues(alpha: 0.15) : AppColors.lightMint,
                iconColor: isDark ? AppColors.darkMint : AppColors.primary,
                onTap: () => context.push('/fleet'),
              ),
              MetricCard(
                title: 'Active Drivers', 
                value: kpis.totalActiveDrivers.toString(), 
                icon: Icons.person, 
                trend: '↑ +1', 
                isTrendPositive: true,
                iconBackgroundColor: isDark ? AppColors.info.withValues(alpha: 0.15) : AppColors.info.withValues(alpha: 0.1),
                iconColor: AppColors.info,
                onTap: () => context.push('/fleet'),
              ),
              MetricCard(
                title: 'Ongoing Trips', 
                value: kpis.activeTrips.toString(), 
                icon: Icons.route, 
                trend: '↑ +3', 
                isTrendPositive: true,
                iconBackgroundColor: isDark ? AppColors.purpleAccent.withValues(alpha: 0.15) : AppColors.purpleAccent.withValues(alpha: 0.1),
                iconColor: AppColors.purpleAccent,
                onTap: () => context.push('/trips'),
              ),
              MetricCard(
                title: 'Approved Expenses', 
                value: currencyFormatter.format(kpis.monthlyExpenses), 
                icon: Icons.account_balance_wallet, 
                trend: '↓ 12%', 
                isTrendPositive: true, // Lower spend is positive
                iconBackgroundColor: isDark ? AppColors.warning.withValues(alpha: 0.15) : AppColors.warning.withValues(alpha: 0.1),
                iconColor: AppColors.warning,
                onTap: () => context.push('/finance'),
              ),
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




