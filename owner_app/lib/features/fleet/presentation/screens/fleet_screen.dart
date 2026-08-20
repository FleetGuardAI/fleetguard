import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import 'package:go_router/go_router.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/fleet_provider.dart';
import '../../data/fleet_repository.dart';
import 'vehicle_detail_screen.dart';

class FleetScreen extends ConsumerStatefulWidget {
  const FleetScreen({super.key});

  @override
  ConsumerState<FleetScreen> createState() => _FleetScreenState();
}

class _FleetScreenState extends ConsumerState<FleetScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(
        title: const Text('Fleet'),
        actions: [
          TextButton.icon(
            onPressed: () {
              if (_tabController.index == 0) {
                context.push('/fleet/add-truck');
              } else if (_tabController.index == 1) {
                context.push('/fleet/invite-driver'); 
              } else {
                context.push('/fleet/add-device');
              }
            },
            icon: const Icon(Icons.add, color: AppTheme.primaryGreen),
            label: const Text('Add', style: TextStyle(color: AppTheme.primaryGreen)),
          ),
          const SizedBox(width: 8),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryGreen,
          unselectedLabelColor: AppTheme.textSecondary,
          indicatorColor: AppTheme.primaryGreen,
          tabs: const [
            Tab(text: 'TRUCKS'),
            Tab(text: 'DRIVERS'),
            Tab(text: 'HARDWARE'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTrucksList(),
          _buildDriversList(),
          _buildHardwareList(),
        ],
      ),
    );
  }

  Widget _buildHardwareList() {
    final hardwareAsync = ref.watch(hardwareAssetsProvider);
    return hardwareAsync.when(
      data: (assets) {
        if (assets.isEmpty) {
          return const Center(child: Text("No hardware devices found.", style: TextStyle(color: Colors.white70)));
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar('Search hardware...'),
            const SizedBox(height: 16),
            ...assets.map((a) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildHardwareCard(a),
            )),
          ],
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text("Error: $e", style: const TextStyle(color: Colors.red))),
    );
  }

  Widget _buildHardwareCard(HardwareAsset asset) {
    final isInstalled = asset.installationStatus.toLowerCase() == 'installed';
    return InkWell(
      onTap: () {},
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.backgroundCream,
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.memory, color: AppTheme.primaryGreen),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(asset.model, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(asset.businessId, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(asset.operationalStatus, style: const TextStyle(fontWeight: FontWeight.w500)),
                Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: isInstalled ? AppTheme.primaryGreen : Colors.orange),
                    const SizedBox(width: 4),
                    Text(asset.installationStatus, style: TextStyle(color: isInstalled ? AppTheme.primaryGreen : Colors.orange, fontSize: 12)),
                  ],
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildTrucksList() {
    final vehiclesAsync = ref.watch(vehiclesProvider);
    return vehiclesAsync.when(
      data: (vehicles) {
        if (vehicles.isEmpty) {
          return const Center(child: Text("No vehicles found.", style: TextStyle(color: Colors.white70)));
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar('Search truck...'),
            const SizedBox(height: 16),
            ...vehicles.map((v) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildTruckCard(v.licensePlate, '${v.make} ${v.model}', v.status, 'Healthy', AppTheme.primaryGreen, () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => VehicleDetailScreen(vehicle: v)));
              }),
            )),
          ],
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text("Error: $e", style: const TextStyle(color: Colors.red))),
    );
  }

  Widget _buildDriversList() {
    final driversAsync = ref.watch(driversProvider);
    return driversAsync.when(
      data: (drivers) {
        if (drivers.isEmpty) {
          return const Center(child: Text("No drivers found.", style: TextStyle(color: Colors.white70)));
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar('Search driver...'),
            const SizedBox(height: 16),
            ...drivers.map((d) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildDriverCard(d.name, d.phoneNumber, d.status, 'Good', AppTheme.primaryGreen),
            )),
          ],
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text("Error: $e", style: const TextStyle(color: Colors.red))),
    );
  }

  Widget _buildSearchBar(String hint) {
    return TextField(
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: const Icon(Icons.search, color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.cardLight,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(vertical: 0),
      ),
    );
  }

  Widget _buildTruckCard(String plate, String driver, String status, String health, Color healthColor, [VoidCallback? onTap]) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const Text('🚛', style: TextStyle(fontSize: 32)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(plate, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(driver, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(status, style: const TextStyle(fontWeight: FontWeight.w500)),
                Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: healthColor),
                    const SizedBox(width: 4),
                    Text(health, style: TextStyle(color: healthColor, fontSize: 12)),
                  ],
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildDriverCard(String name, String plate, String status, String health, Color healthColor) {
    return InkWell(
      onTap: () {},
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const CircleAvatar(
              backgroundColor: AppTheme.backgroundCream,
              child: Icon(Icons.person, color: AppTheme.textSecondary),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(plate, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(status, style: const TextStyle(fontWeight: FontWeight.w500)),
                Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: healthColor),
                    const SizedBox(width: 4),
                    Text(health, style: TextStyle(color: healthColor, fontSize: 12)),
                  ],
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}
