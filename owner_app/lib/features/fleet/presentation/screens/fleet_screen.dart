import 'package:flutter/material.dart';
import 'dart:async';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_colors.dart';
import 'package:go_router/go_router.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/fleet_provider.dart';
import '../../data/fleet_repository.dart';
import 'vehicle_detail_screen.dart';
import 'driver_detail_screen.dart';
import '../../../../core/widgets/empty_state_widget.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/glass_text_field.dart';
import '../../../../core/widgets/status_chip.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/error_state_widget.dart';

class FleetScreen extends ConsumerStatefulWidget {
  const FleetScreen({super.key});

  @override
  ConsumerState<FleetScreen> createState() => _FleetScreenState();
}

class _FleetScreenState extends ConsumerState<FleetScreen> with SingleTickerProviderStateMixin {

  late TabController _tabController;
  final TextEditingController _truckSearchController = TextEditingController();
  final TextEditingController _driverSearchController = TextEditingController();
  final TextEditingController _hardwareSearchController = TextEditingController();
  Timer? _truckDebounce;
  Timer? _driverDebounce;
  Timer? _hardwareDebounce;


  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

@override
  void dispose() {
    _tabController.dispose();
    _truckSearchController.dispose();
    _driverSearchController.dispose();
    _hardwareSearchController.dispose();
    _truckDebounce?.cancel();
    _driverDebounce?.cancel();
    _hardwareDebounce?.cancel();
    super.dispose();
  }

  String _selectedTruckStatus = 'ALL';
  String _selectedDriverStatus = 'ALL';
  String _selectedHardwareStatus = 'ALL';

  void _showFilterBottomSheet() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final int currentTab = _tabController.index;
    
    String title = 'Filter Trucks';
    List<String> options = ['ALL', 'ACTIVE', 'IN_SHOP', 'IDLE', 'OUT_OF_SERVICE'];
    String currentSelection = _selectedTruckStatus;
    
    if (currentTab == 1) {
      title = 'Filter Drivers';
      options = ['ALL', 'ACTIVE', 'ON_LEAVE', 'OFF_DUTY'];
      currentSelection = _selectedDriverStatus;
    } else if (currentTab == 2) {
      title = 'Filter Hardware';
      options = ['ALL', 'INSTALLED', 'UNINSTALLED'];
      currentSelection = _selectedHardwareStatus;
    }

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
              Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 16),
              Wrap(
                spacing: 8.0,
                runSpacing: 8.0,
                children: options.map((status) {
                  final isSelected = currentSelection == status;
                  return ChoiceChip(
                    label: Text(status.replaceAll('_', ' ')),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        if (currentTab == 0) {
                          ref.read(vehicleStatusProvider.notifier).state = status;
                        } else if (currentTab == 1) {
                          setState(() => _selectedDriverStatus = status);
                        } else if (currentTab == 2) {
                          setState(() => _selectedHardwareStatus = status);
                        }
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
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: const Text('Fleet'),
        actions: [
          IconButton(
            icon: Icon(Icons.filter_list, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
            onPressed: _showFilterBottomSheet,
          ),
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
            icon: const Icon(Icons.add, color: AppColors.primary),
            label: const Text('Add', style: TextStyle(color: AppColors.primary)),
          ),
          const SizedBox(width: 8),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: isDark ? AppColors.darkOnSurface : AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray,
          indicatorColor: AppColors.primary,
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
      data: (allAssets) {
        final search = ref.watch(hardwareSearchProvider).toLowerCase();
        final filteredAssets = allAssets.where((a) {
          final matchesStatus = _selectedHardwareStatus == 'ALL' || a.installationStatus.toUpperCase() == _selectedHardwareStatus;
          final matchesSearch = a.model.toLowerCase().contains(search) || a.businessId.toLowerCase().contains(search);
          return matchesStatus && matchesSearch;
        }).toList();

        if (filteredAssets.isEmpty) {
          return EmptyStateWidget(
            icon: Icons.memory,
            title: 'No Hardware Found',
            message: _selectedHardwareStatus == 'ALL'
                ? 'You have not added any hardware devices.'
                : 'No hardware devices found with status "$_selectedHardwareStatus".',
          );
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar(
              hint: 'Search hardware...',
              controller: _hardwareSearchController,
              onSearchChanged: (value) {
                if (_hardwareDebounce?.isActive ?? false) _hardwareDebounce!.cancel();
                _hardwareDebounce = Timer(const Duration(milliseconds: 500), () {
                  ref.read(hardwareSearchProvider.notifier).state = value;
                });
              },
            ),
            const SizedBox(height: 16),
            ...filteredAssets.map((a) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildHardwareCard(a),
            )),
          ],
        );
      },
      loading: () => ListView.separated(
        padding: const EdgeInsets.all(16.0),
        itemCount: 4,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (_, __) => const SkeletonLoader(height: 80, borderRadius: 12),
      ),
      error: (e, st) => ErrorStateWidget(
        message: 'Failed to load hardware.',
        onRetry: () => ref.refresh(hardwareAssetsProvider),
      ),
    );
  }

  Widget _buildHardwareCard(HardwareAsset asset) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isInstalled = asset.installationStatus.toLowerCase() == 'installed';
    return InkWell(
      onTap: () {},
      child: GlassCard(
        
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkBackground : AppColors.lightBackground,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.memory, color: AppColors.primary),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(asset.model, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                  Text(asset.businessId, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(asset.operationalStatus, style: TextStyle(fontWeight: FontWeight.w500, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                const SizedBox(height: 4),
                StatusChip(
                  label: asset.installationStatus,
                  color: isInstalled ? AppColors.statusGreen : AppColors.statusAmber,
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
    final status = ref.watch(vehicleStatusProvider);
    return vehiclesAsync.when(
      data: (vehicles) {
        if (vehicles.isEmpty) {
          return EmptyStateWidget(
            icon: Icons.local_shipping,
            title: 'No Trucks Found',
            message: status == 'ALL'
                ? 'Your fleet has no trucks registered.'
                : 'No trucks found with status "$status".',
          );
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar(
              hint: 'Search truck...',
              controller: _truckSearchController,
              onSearchChanged: (value) {
                if (_truckDebounce?.isActive ?? false) _truckDebounce!.cancel();
                _truckDebounce = Timer(const Duration(milliseconds: 500), () {
                  ref.read(vehicleSearchProvider.notifier).state = value;
                });
              },
            ),
            const SizedBox(height: 16),
            ...vehicles.map((v) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildTruckCard(v.licensePlate, '${v.make} ${v.model}', v.status, 'Healthy', AppColors.primary, () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => VehicleDetailScreen(vehicle: v)));
              }),
            )),
          ],
        );
      },
      loading: () => ListView.separated(
        padding: const EdgeInsets.all(16.0),
        itemCount: 4,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (_, __) => const SkeletonLoader(height: 80, borderRadius: 12),
      ),
      error: (e, st) => ErrorStateWidget(
        message: 'Failed to load trucks.',
        onRetry: () => ref.refresh(vehiclesProvider),
      ),
    );
  }

  Widget _buildDriversList() {
    final driversAsync = ref.watch(driversProvider);
    return driversAsync.when(
      data: (allDrivers) {
        final search = ref.watch(driverSearchProvider).toLowerCase();
        final drivers = _selectedDriverStatus == 'ALL' 
            ? allDrivers 
            : allDrivers.where((d) => d.status.toUpperCase() == _selectedDriverStatus).toList();
        
        final filteredDrivers = drivers.where((d) {
          return d.name.toLowerCase().contains(search) || d.phoneNumber.toLowerCase().contains(search);
        }).toList();

        if (filteredDrivers.isEmpty) {
          return EmptyStateWidget(
            icon: Icons.person_off,
            title: 'No Drivers Found',
            message: _selectedDriverStatus == 'ALL'
                ? 'Your fleet has no drivers added.'
                : 'No drivers found with status "$_selectedDriverStatus".',
          );
        }
        return ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            _buildSearchBar(
              hint: 'Search driver...',
              controller: _driverSearchController,
              onSearchChanged: (value) {
                if (_driverDebounce?.isActive ?? false) _driverDebounce!.cancel();
                _driverDebounce = Timer(const Duration(milliseconds: 500), () {
                  ref.read(driverSearchProvider.notifier).state = value;
                });
              },
            ),
            const SizedBox(height: 16),
            ...filteredDrivers.map((d) => Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: _buildDriverCard(d.name, d.phoneNumber, d.status, 'Good', AppColors.primary, () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => DriverDetailScreen(driver: d)));
              }),
            )),
          ],
        );
      },
      loading: () => ListView.separated(
        padding: const EdgeInsets.all(16.0),
        itemCount: 4,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (_, __) => const SkeletonLoader(height: 80, borderRadius: 12),
      ),
      error: (e, st) => ErrorStateWidget(
        message: 'Failed to load drivers.',
        onRetry: () => ref.refresh(driversProvider),
      ),
    );
  }

Widget _buildSearchBar({
    required String hint, 
    required TextEditingController controller, 
    required void Function(String) onSearchChanged,
  }) {
    return GlassTextField(
      
      controller: controller,
      hintText: hint,
      prefixIcon: Icons.search,
      onChanged: onSearchChanged,
      onClear: () {
        controller.clear();
        onSearchChanged('');
      },
    );
  }

  Widget _buildTruckCard(String plate, String driver, String status, String health, Color healthColor, [VoidCallback? onTap]) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final Color statusColor = status.toUpperCase() == 'ACTIVE' ? AppColors.statusGreen : AppColors.statusAmber;

    return InkWell(
      onTap: onTap,
      child: GlassCard(
        
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Text('🚛', style: TextStyle(fontSize: 32)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(plate, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                  Text(driver, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                StatusChip(
                  label: status,
                  color: statusColor,
                ),
                const SizedBox(height: 4),
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

  Widget _buildDriverCard(String name, String plate, String status, String health, Color healthColor, [VoidCallback? onTap]) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final Color statusColor = status.toUpperCase() == 'ACTIVE' ? AppColors.statusGreen : AppColors.statusAmber;

    return InkWell(
      onTap: onTap,
      child: GlassCard(
        
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
              child: Icon(Icons.person, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                  Text(plate, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                StatusChip(
                  label: status,
                  color: statusColor,
                ),
                const SizedBox(height: 4),
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
