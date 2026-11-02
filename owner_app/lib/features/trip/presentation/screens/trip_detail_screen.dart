import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/polyline_decoder.dart';
import '../../data/trip_repository.dart';
import '../../data/trip_intelligence_repository.dart';
import '../../data/trip_intelligence_models.dart';
import '../widgets/pre_trip_decision_card.dart';
import '../widgets/live_trip_health_card.dart';
import '../widgets/post_trip_performance_card.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/info_row.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/widgets/section_header.dart';
import '../../../../core/widgets/status_chip.dart';

class TripDetailScreen extends ConsumerStatefulWidget {
  final OwnerTrip trip;

  const TripDetailScreen({super.key, required this.trip});

  @override
  ConsumerState<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends ConsumerState<TripDetailScreen> {
  final _intelRepo = TripIntelligenceRepository();
  late final OwnerTripRepository _tripRepo;

  PreTripIntelligenceResponse? _preIntel;
  LiveTripIntelligenceResponse? _liveIntel;
  PostTripIntelligenceResponse? _postIntel;
  bool _isLoadingIntel = false;

  // Routing and Telemetry state
  Map<String, dynamic>? _activeRoute;
  List<dynamic> _deviations = [];
  List<dynamic> _routeVersions = [];
  List<dynamic> _locationTrail = [];
  bool _isLoadingRouteData = false;

  GoogleMapController? _mapController;
  Set<Marker> _mapMarkers = {};
  Set<Polyline> _mapPolylines = {};
  LatLng? _mapCenter;

  @override
  void initState() {
    super.initState();
    _tripRepo = ref.read(ownerTripRepositoryProvider);
    _loadIntelligence();
    _loadRoutingAndTelemetry();
  }

  Future<void> _loadIntelligence() async {
    setState(() => _isLoadingIntel = true);
    try {
      if (widget.trip.status == 'CREATED') {
        final data = await _intelRepo.getPreTripIntelligenceSnapshot(widget.trip.id);
        setState(() => _preIntel = data);
      } else if (widget.trip.status == 'IN_PROGRESS' || widget.trip.status == 'PAUSED') {
        final data = await _intelRepo.getLiveTripIntelligence(widget.trip.id);
        setState(() => _liveIntel = data);
      } else if (widget.trip.status == 'COMPLETED') {
        final data = await _intelRepo.getTripIntelligence(widget.trip.id);
        setState(() => _postIntel = data);
      }
    } catch (e) {
      debugPrint('Failed to load intelligence: $e');
    } finally {
      setState(() => _isLoadingIntel = false);
    }
  }

  Future<void> _loadRoutingAndTelemetry() async {
    setState(() => _isLoadingRouteData = true);
    try {
      // Fetch active route, deviations, versions, and telemetry in parallel
      final activeRouteFuture = _tripRepo.getActiveRoute(widget.trip.id).catchError((_) => <String, dynamic>{});
      final deviationsFuture = _tripRepo.getDeviations(widget.trip.id).catchError((_) => <dynamic>[]);
      final versionsFuture = _tripRepo.getRouteVersions(widget.trip.id).catchError((_) => <dynamic>[]);
      final locationsFuture = widget.trip.driverId != null
          ? _tripRepo.getDriverLocations(widget.trip.driverId!).catchError((_) => <dynamic>[])
          : Future.value(<dynamic>[]);

      final results = await Future.wait([
        activeRouteFuture,
        deviationsFuture,
        versionsFuture,
        locationsFuture,
      ]);

      if (mounted) {
        setState(() {
          _activeRoute = results[0] as Map<String, dynamic>;
          _deviations = results[1] as List<dynamic>;
          _routeVersions = results[2] as List<dynamic>;
          _locationTrail = results[3] as List<dynamic>;
          _buildMapElements();
        });
      }
    } catch (e) {
      debugPrint('Error loading route telemetry: $e');
    } finally {
      if (mounted) setState(() => _isLoadingRouteData = false);
    }
  }

  void _buildMapElements() {
    final markers = <Marker>{};
    final polylines = <Polyline>{};

    // 1. Decode Approved Route Polyline
    final polylineStr = _activeRoute?['route_polyline'] as String? ?? widget.trip.routePolyline;
    List<LatLng> approvedPoints = [];
    if (polylineStr != null && polylineStr.isNotEmpty) {
      try {
        approvedPoints = decodePolyline(polylineStr);
        if (approvedPoints.isNotEmpty) {
          polylines.add(
            Polyline(
              polylineId: const PolylineId('approved_route'),
              points: approvedPoints,
              color: const Color(0xFF1B5E20), // Dark green corridor
              width: 5,
            ),
          );
        }
      } catch (e) {
        debugPrint('Polyline decode error: $e');
      }
    }

    // 2. Decode Actual Recorded GPS Trail
    final trailPoints = <LatLng>[];
    for (final loc in _locationTrail) {
      if (loc['latitude'] != null && loc['longitude'] != null) {
        trailPoints.add(LatLng((loc['latitude'] as num).toDouble(), (loc['longitude'] as num).toDouble()));
      }
    }
    if (trailPoints.isNotEmpty) {
      polylines.add(
        Polyline(
          polylineId: const PolylineId('actual_gps_trail'),
          points: trailPoints,
          color: Colors.blueAccent,
          width: 4,
        ),
      );
    }

    // 3. Pickup Marker
    if (widget.trip.originLat != null && widget.trip.originLng != null) {
      markers.add(
        Marker(
          markerId: const MarkerId('origin'),
          position: LatLng(widget.trip.originLat!, widget.trip.originLng!),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          infoWindow: InfoWindow(title: 'Origin: ${widget.trip.originLocation ?? ""}'),
        ),
      );
    } else if (approvedPoints.isNotEmpty) {
      markers.add(
        Marker(
          markerId: const MarkerId('origin'),
          position: approvedPoints.first,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          infoWindow: InfoWindow(title: 'Origin: ${widget.trip.originLocation ?? ""}'),
        ),
      );
    }

    // 4. Destination Marker
    if (widget.trip.destinationLat != null && widget.trip.destinationLng != null) {
      markers.add(
        Marker(
          markerId: const MarkerId('destination'),
          position: LatLng(widget.trip.destinationLat!, widget.trip.destinationLng!),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: InfoWindow(title: 'Destination: ${widget.trip.destinationLocation ?? ""}'),
        ),
      );
    } else if (approvedPoints.isNotEmpty) {
      markers.add(
        Marker(
          markerId: const MarkerId('destination'),
          position: approvedPoints.last,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: InfoWindow(title: 'Destination: ${widget.trip.destinationLocation ?? ""}'),
        ),
      );
    }

    // 5. Current Vehicle Marker
    if (trailPoints.isNotEmpty) {
      markers.add(
        Marker(
          markerId: const MarkerId('current_location'),
          position: trailPoints.last,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure),
          infoWindow: const InfoWindow(title: 'Latest Vehicle Location'),
        ),
      );
      _mapCenter = trailPoints.last;
    } else if (approvedPoints.isNotEmpty) {
      _mapCenter = approvedPoints.first;
    } else {
      _mapCenter = const LatLng(28.6139, 77.2090); // Default benchmark New Delhi
    }

    // 6. Deviation Incident Markers
    for (int i = 0; i < _deviations.length; i++) {
      final dev = _deviations[i];
      if (dev['detected_latitude'] != null && dev['detected_longitude'] != null) {
        final dist = dev['distance_from_route_meters'] != null
            ? '${(dev['distance_from_route_meters'] as num).round()}m'
            : '';
        markers.add(
          Marker(
            markerId: MarkerId('deviation_${dev['id'] ?? i}'),
            position: LatLng(
              (dev['detected_latitude'] as num).toDouble(),
              (dev['detected_longitude'] as num).toDouble(),
            ),
            icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange),
            infoWindow: InfoWindow(
              title: 'Deviation Alert ($dist off route)',
              snippet: dev['driver_notes'] ?? dev['obstruction_reason'] ?? 'Corridor breach',
            ),
          ),
        );
      }
    }

    _mapMarkers = markers;
    _mapPolylines = polylines;
  }

  Future<void> _acknowledgeDeviation(int eventId) async {
    try {
      await _tripRepo.acknowledgeDeviation(widget.trip.id, eventId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Deviation incident acknowledged.')),
        );
        _loadRoutingAndTelemetry();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(backgroundColor: Colors.red, content: Text('Error: $e')),
        );
      }
    }
  }

  Future<void> _showResolveDialog(int eventId) async {
    final notesCtrl = TextEditingController(text: 'Operational detour reviewed and cleared');
    await showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Resolve Deviation Incident'),
        content: TextField(
          controller: notesCtrl,
          maxLines: 2,
          decoration: const InputDecoration(
            labelText: 'Resolution Notes',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogCtx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(dialogCtx);
              try {
                await _tripRepo.resolveDeviation(
                  widget.trip.id,
                  eventId,
                  resolutionNotes: notesCtrl.text.trim(),
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Incident marked resolved.')),
                  );
                  _loadRoutingAndTelemetry();
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(backgroundColor: Colors.red, content: Text('Error: $e')),
                  );
                }
              }
            },
            child: const Text('Resolve'),
          ),
        ],
      ),
    );
  }

  Future<void> _showRecalculateDialog() async {
    final lastLat = _mapCenter?.latitude ?? 28.6139;
    final lastLng = _mapCenter?.longitude ?? 77.2090;
    bool isRecalculating = false;

    await showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Recalculate Route from Current Position'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Calculates fresh truck-safe route options from vehicle location (${lastLat.toStringAsFixed(4)}, ${lastLng.toStringAsFixed(4)}) to destination.',
                style: const TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 12),
              if (isRecalculating)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: CircularProgressIndicator(),
                  ),
                ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: isRecalculating ? null : () => Navigator.pop(dialogCtx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1B5E20), foregroundColor: Colors.white),
              onPressed: isRecalculating
                  ? null
                  : () async {
                      setDlgState(() => isRecalculating = true);
                      try {
                        final result = await _tripRepo.recalculateRoute(
                          widget.trip.id,
                          currentLat: lastLat,
                          currentLng: lastLng,
                          reason: 'Owner initiated re-optimization from vehicle position',
                        );
                        if (mounted) {
                          Navigator.pop(dialogCtx);
                          final routes = result['routes'] as List<dynamic>? ?? [];
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              backgroundColor: Colors.green,
                              content: Text('Calculated ${routes.length} detour options. Route updated.'),
                            ),
                          );
                          _loadRoutingAndTelemetry();
                        }
                      } catch (e) {
                        setDlgState(() => isRecalculating = false);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(backgroundColor: Colors.red, content: Text('Recalculation error: $e')),
                          );
                        }
                      }
                    },
              child: const Text('Calculate Alternatives'),
            ),
          ],
        ),
      ),
    );
  }

  void _showVersionsDialog() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Route Version History', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 12),
            if (_routeVersions.isEmpty)
              const Text('No previous versions recorded.', style: TextStyle(color: Colors.grey))
            else
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: _routeVersions.length,
                  separatorBuilder: (_, __) => const Divider(),
                  itemBuilder: (_, idx) {
                    final v = _routeVersions[idx];
                    final isActive = v['is_active'] == true;
                    return ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: CircleAvatar(
                        backgroundColor: isActive ? Colors.green : Colors.grey.shade400,
                        foregroundColor: Colors.white,
                        child: Text('V${v['version_number'] ?? idx + 1}'),
                      ),
                      title: Text(
                        '${v['route_type'] ?? "STANDARD"} — ${v['distance_km']} km (${v['duration_hours'] != null ? '${(v['duration_hours'] * 60).round()} min' : ''})',
                        style: TextStyle(fontWeight: isActive ? FontWeight.bold : FontWeight.normal),
                      ),
                      subtitle: Text(
                        'Status: ${v['status']} | ${v['approval_reason'] ?? "Initial route"}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      trailing: isActive
                          ? const Chip(
                              label: Text('ACTIVE', style: TextStyle(fontSize: 10, color: Colors.white)),
                              backgroundColor: Colors.green,
                            )
                          : null,
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    Color statusColor;
    switch (widget.trip.status) {
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

    final routeStatus = _activeRoute?['route_status'] as String? ?? widget.trip.routeStatus ?? 'APPROVED';
    final hasDeviation = routeStatus == 'DEVIATION_SUSPECTED' || routeStatus == 'DEVIATION_CONFIRMED' || _deviations.isNotEmpty;

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(widget.trip.tripId, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'Route Versions',
            onPressed: _showVersionsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.alt_route),
            tooltip: 'Recalculate Route',
            onPressed: _showRecalculateDialog,
          ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          // --- Interactive Route & Telemetry Map Header ---
          SliverToBoxAdapter(
            child: SizedBox(
              height: 280,
              child: Stack(
                children: [
                  GoogleMap(
                    initialCameraPosition: CameraPosition(
                      target: _mapCenter ?? const LatLng(28.6139, 77.2090),
                      zoom: 10.5,
                    ),
                    markers: _mapMarkers,
                    polylines: _mapPolylines,
                    myLocationEnabled: false,
                    myLocationButtonEnabled: false,
                    zoomControlsEnabled: true,
                    mapToolbarEnabled: false,
                    onMapCreated: (controller) {
                      _mapController = controller;
                      if (_mapCenter != null) {
                        _mapController?.animateCamera(CameraUpdate.newLatLng(_mapCenter!));
                      }
                    },
                  ),
                  if (_isLoadingRouteData)
                    Container(
                      color: Colors.black26,
                      child: const Center(child: CircularProgressIndicator()),
                    ),
                  // Top overlay badges
                  Positioned(
                    top: 10,
                    left: 12,
                    right: 12,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: isDark ? Colors.black87 : Colors.white.withValues(alpha: 0.95),
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(color: Colors.black.withValues(alpha: 0.15), blurRadius: 4),
                            ],
                          ),
                          child: Row(
                            children: [
                              Icon(
                                hasDeviation ? Icons.warning_amber_rounded : Icons.check_circle,
                                size: 16,
                                color: hasDeviation ? Colors.orange : Colors.green,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                routeStatus,
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                  color: hasDeviation ? Colors.orange.shade800 : Colors.green.shade800,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1B5E20),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Version ${_activeRoute?['version_number'] ?? widget.trip.approvedRouteVersionId ?? 1}',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          SliverPadding(
            padding: const EdgeInsets.all(16.0),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // --- Deviation Incident Panel (if deviations exist) ---
                if (hasDeviation) ...[
                  GlassCard(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.warning, color: Colors.amber, size: 22),
                            const SizedBox(width: 8),
                            const Expanded(
                              child: Text(
                                'Route Deviation Incident',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                            ),
                            OutlinedButton.icon(
                              onPressed: _showRecalculateDialog,
                              icon: const Icon(Icons.refresh, size: 14),
                              label: const Text('Recalculate', style: TextStyle(fontSize: 12)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        if (_deviations.isNotEmpty) ...[
                          for (final dev in _deviations.take(2)) ...[
                            Container(
                              margin: const EdgeInsets.only(top: 8),
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: Colors.orange.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'Severity: ${dev['severity'] ?? "MEDIUM"}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                      ),
                                      Text(
                                        dev['distance_from_route_meters'] != null
                                            ? '${(dev['distance_from_route_meters'] as num).round()} m off corridor'
                                            : '',
                                        style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 12),
                                      ),
                                    ],
                                  ),
                                  if (dev['obstruction_reason'] != null) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      'Driver Report: ${dev['obstruction_reason']}${dev['driver_notes'] != null ? ' - ${dev['driver_notes']}' : ''}',
                                      style: const TextStyle(fontSize: 12, color: Colors.black87),
                                    ),
                                  ],
                                  const SizedBox(height: 8),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.end,
                                    children: [
                                      if (dev['is_acknowledged'] != true)
                                        TextButton(
                                          onPressed: () => _acknowledgeDeviation(dev['id']),
                                          child: const Text('Acknowledge', style: TextStyle(fontSize: 12)),
                                        ),
                                      ElevatedButton(
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: Colors.green,
                                          foregroundColor: Colors.white,
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                        ),
                                        onPressed: () => _showResolveDialog(dev['id']),
                                        child: const Text('Resolve', style: TextStyle(fontSize: 12)),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ] else
                          const Text(
                            'Vehicle is outside approved corridor buffer. Monitoring real-time telemetry.',
                            style: TextStyle(fontSize: 12, color: Colors.grey),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // --- Route Optimization & Economics Card ---
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Route Intelligence & Economics'),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          Column(
                            children: [
                              const Text('Planned Distance', style: TextStyle(fontSize: 11, color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                _activeRoute?['distance_km'] != null
                                    ? '${_activeRoute!['distance_km']} km'
                                    : (widget.trip.plannedDistance != null ? '${widget.trip.plannedDistance} km' : '--'),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                              ),
                            ],
                          ),
                          Column(
                            children: [
                              const Text('Est. Duration', style: TextStyle(fontSize: 11, color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                _activeRoute?['duration_hours'] != null
                                    ? '${(_activeRoute!['duration_hours'] * 60).round()} min'
                                    : '--',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                              ),
                            ],
                          ),
                          Column(
                            children: [
                              const Text('Toll Estimate', style: TextStyle(fontSize: 11, color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                _activeRoute?['toll_cost_estimate'] != null
                                    ? '₹${_activeRoute!['toll_cost_estimate']}'
                                    : (widget.trip.routeTollEstimate != null ? '₹${widget.trip.routeTollEstimate}' : 'N/A'),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.teal),
                              ),
                            ],
                          ),
                          Column(
                            children: [
                              const Text('Fuel Estimate', style: TextStyle(fontSize: 11, color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                _activeRoute?['fuel_cost_estimate'] != null
                                    ? '₹${_activeRoute!['fuel_cost_estimate']}'
                                    : (widget.trip.plannedCost != null ? '₹${widget.trip.plannedCost}' : 'N/A'),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.indigo),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // --- Existing Decision Cards ---
                if (widget.trip.status == 'CREATED') ...[
                  if (_isLoadingIntel)
                    const Center(child: CircularProgressIndicator())
                  else if (_preIntel != null)
                    PreTripDecisionCard(data: _preIntel!),
                  const SizedBox(height: 16),
                ],
                if (widget.trip.status == 'IN_PROGRESS' || widget.trip.status == 'PAUSED') ...[
                  if (_isLoadingIntel)
                    const Center(child: CircularProgressIndicator())
                  else if (_liveIntel != null)
                    LiveTripHealthCard(data: _liveIntel!),
                  const SizedBox(height: 16),
                ],
                if (widget.trip.status == 'COMPLETED') ...[
                  if (_isLoadingIntel)
                    const Center(child: CircularProgressIndicator())
                  else if (_postIntel != null)
                    PostTripPerformanceCard(data: _postIntel!),
                  const SizedBox(height: 16),
                ],

                // --- Route Info ---
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Route Locations'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Origin', value: widget.trip.originLocation ?? 'N/A'),
                      InfoRow(label: 'Destination', value: widget.trip.destinationLocation ?? 'N/A'),
                      const SizedBox(height: 12),
                      const Divider(),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Trip Status', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                          StatusChip(label: widget.trip.status.replaceAll('_', ' '), color: statusColor),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // --- Assignments ---
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

                // --- Schedule ---
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Schedule'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Scheduled Start', value: widget.trip.plannedStartTime ?? 'N/A'),
                      InfoRow(label: 'Actual Start', value: widget.trip.actualStartTime ?? 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // --- Statistics ---
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Statistics'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Planned Distance', value: widget.trip.plannedDistance != null ? '${widget.trip.plannedDistance} km' : 'N/A'),
                      InfoRow(label: 'Actual Distance', value: widget.trip.actualDistance != null ? '${widget.trip.actualDistance} km' : 'N/A'),
                      InfoRow(label: 'Cargo Weight', value: widget.trip.cargoWeight != null ? '${widget.trip.cargoWeight} kg' : 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // --- Financials ---
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SectionHeader(title: 'Financials'),
                      const SizedBox(height: 12),
                      InfoRow(label: 'Revenue', value: widget.trip.revenue != null ? '₹${widget.trip.revenue}' : 'N/A'),
                      InfoRow(label: 'Planned Cost', value: widget.trip.plannedCost != null ? '₹${widget.trip.plannedCost}' : 'N/A'),
                      InfoRow(label: 'Planned Fuel', value: widget.trip.plannedFuelLiters != null ? '${widget.trip.plannedFuelLiters} L' : 'N/A'),
                    ],
                  ),
                ),
                const SizedBox(height: 80),
              ]),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          context.push('/copilot?contextType=trip&contextId=${widget.trip.tripId}&contextLabel=${widget.trip.tripId}');
        },
        backgroundColor: AppColors.info,
        icon: const Icon(Icons.auto_awesome, color: Colors.white),
        label: const Text('Ask Copilot', style: TextStyle(color: Colors.white)),
      ),
    );
  }
}
