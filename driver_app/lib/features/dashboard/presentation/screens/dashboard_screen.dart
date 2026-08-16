import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/theme/app_colors.dart';
import '../../../../core/services/notification_service.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/services/auth_service.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  String _dutyStatus = 'OFF_DUTY'; // OFF_DUTY, ON_DUTY, ON_BREAK

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final dio = ref.read(apiClientProvider).dio;
      NotificationService.registerFcmToken(dio);
    });
  }

  Color _getDutyColor() {
    switch (_dutyStatus) {
      case 'ON_DUTY':
        return AppColors.onDuty;
      case 'ON_BREAK':
        return AppColors.onBreak;
      default:
        return AppColors.offDuty;
    }
  }

  @override
  Widget build(BuildContext context) {
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
              ),
            ),
            const SizedBox(width: 8),
            const Text('FleetGuard Driver', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notification_add, color: Colors.blue),
            onPressed: () {
              NotificationService.showTripNotification(
                title: 'New Trip Assigned',
                body: 'TRIP-9999: Delhi to Mumbai. Start journey at 08:00 AM.',
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => context.push('/notifications'),
          ),
          IconButton(
            icon: const Icon(Icons.folder_outlined),
            onPressed: () => context.push('/documents'),
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
      body: SingleChildScrollView(
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
                        const CircleAvatar(
                          radius: 28,
                          backgroundColor: AppColors.primaryLight,
                          child: Icon(Icons.person, size: 36, color: Colors.white),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Rajesh Kumar',
                                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'MH-12 Fleet • DL-9876543210',
                                style: TextStyle(color: Theme.of(context).colorScheme.outline, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppColors.driverScoreColor(92).withOpacity(0.15),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.star, size: 16, color: AppColors.driverScoreColor(92)),
                              const SizedBox(width: 4),
                              Text(
                                '92',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.driverScoreColor(92),
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
                        Row(
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                color: _getDutyColor(),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Duty Status: ${_dutyStatus.replaceAll('_', ' ')}',
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                        PopupMenuButton<String>(
                          onSelected: (status) => setState(() => _dutyStatus = status),
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
            Card(
              child: ListTile(
                leading: const Icon(Icons.directions_bus, size: 36, color: AppColors.primary),
                title: const Text('Assigned Vehicle: MH-12-FG-2026', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: const Text('Tata Prima 3530.K • Diesel • Insurance: Valid'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('/vehicle'),
              ),
            ),
            const SizedBox(height: 16),

            // --- Today's Active Trip Card ---
            Text('Today\'s Active Trip', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Text('IN PROGRESS', style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 12)),
                        ),
                        const Text('Trip #TRIP-8492', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Row(
                      children: [
                        Icon(Icons.location_on, color: Colors.green, size: 20),
                        SizedBox(width: 8),
                        Expanded(child: Text('Origin: JNPT Port, Navi Mumbai', style: TextStyle(fontWeight: FontWeight.w600))),
                      ],
                    ),
                    const Padding(
                      padding: EdgeInsets.only(left: 9),
                      child: SizedBox(height: 16, child: VerticalDivider(thickness: 2)),
                    ),
                    const Row(
                      children: [
                        Icon(Icons.flag, color: Colors.red, size: 20),
                        SizedBox(width: 8),
                        Expanded(child: Text('Destination: Logistics Hub, Pune', style: TextStyle(fontWeight: FontWeight.w600))),
                      ],
                    ),
                    const Divider(height: 24),
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Column(
                          children: [
                            Text('Remaining', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Text('28.5 km', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          ],
                        ),
                        Column(
                          children: [
                            Text('ETA', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Text('45 mins', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          ],
                        ),
                        Column(
                          children: [
                            Text('Stops', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Text('3 stops', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () => context.push('/trip/8492/active'),
                            icon: const Icon(Icons.navigation),
                            label: const Text('Live Navigation'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton(
                          onPressed: () => context.push('/inspection'),
                          child: const Text('Inspection'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
