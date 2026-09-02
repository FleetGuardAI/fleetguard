import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/theme/app_colors.dart';
import '../../../../core/services/notification_service.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/services/auth_service.dart';
import '../providers/dashboard_providers.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final dio = ref.read(apiClientProvider).dio;
      NotificationService.registerFcmToken(dio);
    });
  }

  Future<void> _changeDutyStatus(String status) async {
    try {
      final dio = ref.read(apiClientProvider).dio;
      String endpoint;
      switch (status) {
        case 'ON_DUTY':
          endpoint = '/api/v1/driver-app/duty/start';
          break;
        case 'ON_BREAK':
          endpoint = '/api/v1/driver-app/duty/break';
          break;
        case 'OFF_DUTY':
          endpoint = '/api/v1/driver-app/duty/end';
          break;
        default:
          return;
      }
      await dio.post(endpoint);
      ref.invalidate(driverProfileProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Status changed to ${status.replaceAll('_', ' ')}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to change status: $e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final profileAsync = ref.watch(driverProfileProvider);
    final tripsAsync = ref.watch(todayTripsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/images/driver_logo.png',
                width: 28,
                height: 28,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) =>
                    const Icon(Icons.local_shipping, size: 28),
              ),
            ),
            const SizedBox(width: 8),
            const Flexible(
              child: Text(
                'FleetGuard Driver',
                style: TextStyle(fontWeight: FontWeight.bold),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(driverProfileProvider);
              ref.invalidate(todayTripsProvider);
            },
          ),
          PopupMenuButton<String>(
            onSelected: (value) async {
              if (value == 'logout') {
                await ref.read(authServiceProvider).logout();
              }
            },
            icon: const Icon(Icons.account_circle),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, color: Colors.red),
                    SizedBox(width: 8),
                    Text('Logout', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                const SizedBox(height: 16),
                Text('Failed to load profile', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text('$err', textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () => ref.invalidate(driverProfileProvider),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (profile) {
          final String name = profile['name'] ?? 'Driver Name';
          final String phone = profile['phone_number'] ?? '';
          final String fleet = profile['company_name'] ?? 'FleetGuard';
          final String? vehicleStr = profile['assigned_vehicle'];
          final String dutyStr = profile['duty_status'] ?? 'OFF_DUTY';
          final double score = (profile['driver_score'] ?? 85.0).toDouble();

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- Driver Profile & Duty Status Card ---
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              radius: 28,
                              backgroundColor: AppColors.primaryLight,
                              backgroundImage: profile['avatar_url'] != null
                                  ? NetworkImage(profile['avatar_url'])
                                  : null,
                              child: profile['avatar_url'] == null
                                  ? const Icon(Icons.person, size: 36, color: Colors.white)
                                  : null,
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    name,
                                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '$fleet • $phone',
                                    style: TextStyle(color: Theme.of(context).colorScheme.outline, fontSize: 12),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppColors.driverScoreColor(score.toInt()).withOpacity(0.15),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                children: [
                                  Icon(Icons.star, size: 16, color: AppColors.driverScoreColor(score.toInt())),
                                  Text(
                                    '${score.toInt()}',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.driverScoreColor(score.toInt()),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const Divider(height: 24),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Row(
                                children: [
                                  Container(
                                    width: 12,
                                    height: 12,
                                    decoration: BoxDecoration(
                                      color: dutyStr == 'ON_DUTY'
                                          ? AppColors.onDuty
                                          : dutyStr == 'ON_BREAK'
                                              ? AppColors.onBreak
                                              : AppColors.offDuty,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      'Duty Status: ${dutyStr.replaceAll('_', ' ')}',
                                      style: const TextStyle(fontWeight: FontWeight.w600),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            PopupMenuButton<String>(
                              onSelected: _changeDutyStatus,
                              itemBuilder: (context) => const [
                                PopupMenuItem(value: 'ON_DUTY', child: Text('Start Duty (ON DUTY)')),
                                PopupMenuItem(value: 'ON_BREAK', child: Text('Take Break (ON BREAK)')),
                                PopupMenuItem(value: 'OFF_DUTY', child: Text('End Duty (OFF DUTY)')),
                              ],
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Theme.of(context).colorScheme.primaryContainer,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: const Row(
                                  children: [
                                    Text('Change', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                    Icon(Icons.arrow_drop_down, size: 16),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // --- SOS Emergency Button Banner ---
                InkWell(
                  onTap: () => context.push('/emergency'),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: AppColors.dangerGradient,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.warning_amber_rounded, color: Colors.white, size: 36),
                        SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('EMERGENCY SOS', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                              Text('Tap to instantly share location with fleet manager', style: TextStyle(color: Colors.white70, fontSize: 12)),
                            ],
                          ),
                        ),
                        Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // --- Assigned Vehicle Section ---
                if (vehicleStr != null)
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.directions_bus, size: 36, color: AppColors.primary),
                      title: Text('Assigned Vehicle: $vehicleStr', style: const TextStyle(fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis),
                      subtitle: const Text('Ready for dispatch', overflow: TextOverflow.ellipsis),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/vehicle'),
                    ),
                  )
                else
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.warning, size: 36, color: Colors.orange),
                      title: const Text('No Vehicle Assigned', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: const Text('Please contact your fleet manager.'),
                    ),
                  ),
                const SizedBox(height: 16),

                // --- Today's Trips ---
                Text("Today's Trips", style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                tripsAsync.when(
                  loading: () => const Center(child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: CircularProgressIndicator(),
                  )),
                  error: (err, stack) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        children: [
                          const Icon(Icons.error_outline, color: Colors.orange),
                          const SizedBox(height: 8),
                          Text('Error loading trips: $err', textAlign: TextAlign.center),
                          const SizedBox(height: 8),
                          TextButton(
                            onPressed: () => ref.invalidate(todayTripsProvider),
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  data: (trips) {
                    if (trips.isEmpty) {
                      return const Card(
                        child: Padding(
                          padding: EdgeInsets.all(16.0),
                          child: Center(child: Text("No trips assigned for today.")),
                        ),
                      );
                    }

                    return Column(
                      children: trips.map((trip) {
                        final String status = trip['status'] ?? 'UNKNOWN';
                        final bool inProgress = status == 'IN_PROGRESS';
                        final bool isCompleted = status == 'COMPLETED';
                        return Card(
                          child: ListTile(
                            title: Text('Trip #${trip['trip_id']}'),
                            subtitle: Text('${trip['origin_location'] ?? 'N/A'} -> ${trip['destination_location'] ?? 'N/A'}'),
                            trailing: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: inProgress
                                    ? Colors.blue.withOpacity(0.15)
                                    : isCompleted
                                        ? Colors.green.withOpacity(0.15)
                                        : Colors.grey.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                status,
                                style: TextStyle(
                                  color: inProgress
                                      ? Colors.blue
                                      : isCompleted
                                          ? Colors.green
                                          : Colors.grey,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            onTap: () => context.push('/trip/${trip['id']}'),
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
