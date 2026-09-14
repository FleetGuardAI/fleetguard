import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/trip_repository.dart';
import '../../data/trip_intelligence_repository.dart';
import '../../data/trip_intelligence_models.dart';
import '../widgets/pre_trip_decision_card.dart';
import '../widgets/live_trip_health_card.dart';
import '../widgets/post_trip_performance_card.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/info_row.dart';
import '../../../../core/widgets/section_header.dart';
import '../../../../core/widgets/status_chip.dart';
import '../../../../core/widgets/empty_state_widget.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../../core/config/app_config.dart';
import '../../../../core/utils/navigation_safe_area.dart';
import '../../../../core/utils/formatters.dart';

class TripDetailScreen extends ConsumerStatefulWidget {
  final OwnerTrip trip;

  const TripDetailScreen({super.key, required this.trip});

  @override
  ConsumerState<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends ConsumerState<TripDetailScreen> with SingleTickerProviderStateMixin {
  PreTripIntelligenceResponse? _preIntel;
  LiveTripIntelligenceResponse? _liveIntel;
  PostTripIntelligenceResponse? _postIntel;
  bool _isLoadingIntel = false;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadIntelligence();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadIntelligence() async {
    setState(() => _isLoadingIntel = true);
    try {
      final intelRepo = ref.read(tripIntelligenceRepositoryProvider);
      if (widget.trip.status == 'CREATED') {
        final data = await intelRepo.getPreTripIntelligenceSnapshot(widget.trip.id);
        if (mounted) setState(() => _preIntel = data);
      } else if (widget.trip.status == 'IN_PROGRESS' || widget.trip.status == 'PAUSED') {
        final data = await intelRepo.getLiveTripIntelligence(widget.trip.id);
        if (mounted) setState(() => _liveIntel = data);
      } else if (widget.trip.status == 'COMPLETED') {
        final data = await intelRepo.getTripIntelligence(widget.trip.id);
        if (mounted) setState(() => _postIntel = data);
      }
    } catch (e) {
      debugPrint('Failed to load intelligence: $e');
    } finally {
      if (mounted) setState(() => _isLoadingIntel = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    Color statusColor;
    switch (widget.trip.status) {
      case 'COMPLETED': statusColor = AppColors.statusGreen; break;
      case 'IN_PROGRESS': statusColor = AppColors.statusBlue; break;
      case 'PAUSED':
      case 'DELAYED': statusColor = AppColors.statusAmber; break;
      case 'CANCELLED': statusColor = AppColors.statusRed; break;
      case 'CREATED':
      default: statusColor = AppColors.coolGray; break;
    }

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(widget.trip.tripId, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 18, fontWeight: FontWeight.bold)),
            Text('${widget.trip.originLocation ?? "Unknown"} → ${widget.trip.destinationLocation ?? "Unknown"}', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12)),
          ],
        ),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
            child: StatusChip(label: widget.trip.status.replaceAll('_', ' '), color: statusColor),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
          indicatorColor: AppColors.primary,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Map'),
            Tab(text: 'Intelligence'),
            Tab(text: 'Documents'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOverviewTab(isDark, statusColor),
          _buildMapTab(isDark),
          _buildIntelligenceTab(isDark),
          _buildDocumentsTab(isDark),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          context.push('/copilot?contextType=trip&contextId=${widget.trip.tripId}&contextLabel=${widget.trip.tripId}');
        },
        backgroundColor: AppColors.info,
        icon: const Icon(Icons.auto_awesome, color: Colors.white),
        label: const Text('Ask Copilot', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildOverviewTab(bool isDark, Color statusColor) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Trip Details'),
              const SizedBox(height: 12),
              InfoRow(label: 'Origin', value: widget.trip.originLocation ?? 'N/A'),
              InfoRow(label: 'Destination', value: widget.trip.destinationLocation ?? 'N/A'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Assignments'),
              const SizedBox(height: 12),
              InfoRow(label: 'Truck', value: widget.trip.vehicle?['registration_number'] ?? 'Unassigned'),
              InfoRow(label: 'Driver', value: widget.trip.driver?['name'] ?? 'Unassigned'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Schedule & Stats'),
              const SizedBox(height: 12),
              InfoRow(label: 'Scheduled Start', value: Formatters.formatDate(widget.trip.plannedStartTime)),
              InfoRow(label: 'Actual Start', value: Formatters.formatDate(widget.trip.actualStartTime)),
              const Divider(),
              InfoRow(label: 'Planned Distance', value: widget.trip.plannedDistance != null ? '${widget.trip.plannedDistance} km' : 'Not available'),
              InfoRow(label: 'Cargo Weight', value: widget.trip.cargoWeight != null ? '${widget.trip.cargoWeight} kg' : 'Not available'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Financials'),
              const SizedBox(height: 12),
              InfoRow(label: 'Revenue', value: widget.trip.revenue != null ? Formatters.formatCurrency(widget.trip.revenue) : 'Not available'),
              InfoRow(label: 'Planned Cost', value: widget.trip.plannedCost != null ? Formatters.formatCurrency(widget.trip.plannedCost) : 'Not available'),
              InfoRow(label: 'Planned Fuel', value: widget.trip.plannedFuelLiters != null ? '${widget.trip.plannedFuelLiters} L' : 'Not available'),
            ],
          ),
        ),
        SizedBox(height: context.scrollContentClearance),
      ],
    );
  }

  Widget _buildMapTab(bool isDark) {
    final geoapifyKey = AppConfig.geoapifyApiKey;
    final hasOrigin = widget.trip.originLat != null && widget.trip.originLng != null;
    final hasDest = widget.trip.destinationLat != null && widget.trip.destinationLng != null;
    
    if (geoapifyKey.isEmpty || (!hasOrigin && !hasDest)) {
      return Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                ),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.location_off, color: AppColors.warning, size: 48),
                      const SizedBox(height: 16),
                      Text(
                        geoapifyKey.isEmpty ? 'Map configuration missing' : 'Route Map Unavailable',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        geoapifyKey.isEmpty ? 'Please configure Geoapify API key.' : 'Location data is not available for this trip.',
                        style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    final markers = <Marker>[];
    LatLng? center;
    if (hasOrigin) {
      center = LatLng(widget.trip.originLat!, widget.trip.originLng!);
      markers.add(
        Marker(
          point: center,
          width: 40,
          height: 40,
          child: const Icon(Icons.location_on, color: AppColors.primary, size: 36),
        ),
      );
    }
    if (hasDest) {
      final dest = LatLng(widget.trip.destinationLat!, widget.trip.destinationLng!);
      center ??= dest;
      markers.add(
        Marker(
          point: dest,
          width: 40,
          height: 40,
          child: const Icon(Icons.location_on, color: AppColors.statusGreen, size: 36),
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: FlutterMap(
          options: MapOptions(
            initialCenter: center!,
            initialZoom: (hasOrigin && hasDest) ? 5.0 : 12.0,
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png?apiKey={apiKey}',
              additionalOptions: {
                'apiKey': geoapifyKey,
              },
              userAgentPackageName: 'com.example.fleetguard_owner',
            ),
            MarkerLayer(markers: markers),
          ],
        ),
      ),
    );
  }

  Widget _buildIntelligenceTab(bool isDark) {
    if (_isLoadingIntel) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        if (widget.trip.status == 'CREATED' && _preIntel != null) ...[
          const SectionHeader(title: 'Pre-Trip Intelligence'),
          const SizedBox(height: 12),
          PreTripDecisionCard(data: _preIntel!),
        ],
        if ((widget.trip.status == 'IN_PROGRESS' || widget.trip.status == 'PAUSED') && _liveIntel != null) ...[
          const SectionHeader(title: 'Live Trip Health'),
          const SizedBox(height: 12),
          LiveTripHealthCard(data: _liveIntel!),
          const SizedBox(height: 24),
          const SectionHeader(title: 'Live Insights'),
          const SizedBox(height: 12),
          GlassCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _buildInsightRow('Weather Alert', 'Heavy rain expected on NH48 in 2 hours.', Icons.cloud, AppColors.warning, isDark),
                const Divider(),
                _buildInsightRow('Traffic Update', 'Clear route ahead for the next 100km.', Icons.traffic, AppColors.statusGreen, isDark),
              ],
            ),
          ),
        ],
        if (widget.trip.status == 'COMPLETED' && _postIntel != null) ...[
          const SectionHeader(title: 'Post-Trip Intelligence'),
          const SizedBox(height: 12),
          PostTripPerformanceCard(data: _postIntel!),
        ],
        if ((widget.trip.status == 'CREATED' && _preIntel == null) ||
            ((widget.trip.status == 'IN_PROGRESS' || widget.trip.status == 'PAUSED') && _liveIntel == null) ||
            (widget.trip.status == 'COMPLETED' && _postIntel == null))
          const EmptyStateWidget(
            icon: Icons.analytics,
            title: 'No Intelligence Data',
            message: 'Trip intelligence could not be loaded or is not available.',
          ),
        const SizedBox(height: 80),
      ],
    );
  }

  Widget _buildInsightRow(String title, String description, IconData icon, Color color, bool isDark) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: color.withValues(alpha: 0.1), shape: BoxShape.circle),
          child: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 4),
              Text(description, style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDocumentsTab(bool isDark) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        const SectionHeader(title: 'Document Verification'),
        const SizedBox(height: 12),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              _buildDocItem('E-Way Bill', 'Verified', Icons.description, AppColors.statusGreen, isDark),
              const Divider(),
              _buildDocItem('LR Copy', 'Pending Upload', Icons.inventory, AppColors.warning, isDark),
              const Divider(),
              _buildDocItem('POD (Proof of Delivery)', 'Not Required Yet', Icons.verified, AppColors.coolGray, isDark),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDocItem(String name, String status, IconData icon, Color statusColor, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(icon, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
          const SizedBox(width: 12),
          Expanded(child: Text(name, style: TextStyle(fontWeight: FontWeight.w500, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface))),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(status, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: statusColor)),
          ),
        ],
      ),
    );
  }
}
