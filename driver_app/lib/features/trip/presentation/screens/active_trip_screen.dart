import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../../../core/utils/polyline_decoder.dart';
import '../../data/tracking_service.dart';
import '../../data/trip_repository.dart';
import '../providers/trip_providers.dart';

class ActiveTripScreen extends ConsumerStatefulWidget {
  const ActiveTripScreen({super.key, required this.tripId});
  final int tripId;

  @override
  ConsumerState<ActiveTripScreen> createState() => _ActiveTripScreenState();
}

class _ActiveTripScreenState extends ConsumerState<ActiveTripScreen> {
  LatLng? _origin;
  LatLng? _destination;
  String _distanceLeft = '-- km';
  String _eta = '-- min';
  List<LatLng> _routePoints = [];

  GoogleMapController? _mapController;
  Position? _currentPosition;
  Set<Marker> _markers = {};
  Set<Polyline> _polylines = {};

  StreamSubscription<Position>? _positionSubscription;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  bool _isOffline = false;
  late final TrackingService _trackingService;

  @override
  void initState() {
    super.initState();
    _trackingService = ref.read(trackingServiceProvider);
    _setupMapAndTracking();
    _checkConnectivity();
  }

  void _checkConnectivity() {
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((results) {
      if (mounted) {
        final isConnected = results.any((r) => r != ConnectivityResult.none);
        setState(() {
          _isOffline = !isConnected;
        });
      }
    });
  }

  Future<void> _setupMapAndTracking() async {
    try {
      await _trackingService.startTracking();

      _positionSubscription = Geolocator.getPositionStream().listen((Position position) {
        if (mounted) {
          setState(() {
            _currentPosition = position;
            _updateMarkers();
          });
          _mapController?.animateCamera(
            CameraUpdate.newLatLng(LatLng(position.latitude, position.longitude)),
          );
        }
      });
    } catch (e) {
      debugPrint('Error starting tracking: $e');
    }
  }

  void _updateMarkers() {
    _markers = {
      if (_origin != null)
        Marker(
          markerId: const MarkerId('origin'),
          position: _origin!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          infoWindow: const InfoWindow(title: 'Pickup Location'),
        ),
      if (_destination != null)
        Marker(
          markerId: const MarkerId('destination'),
          position: _destination!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: const InfoWindow(title: 'Destination'),
        ),
      if (_currentPosition != null)
        Marker(
          markerId: const MarkerId('current'),
          position: LatLng(_currentPosition!.latitude, _currentPosition!.longitude),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure),
          infoWindow: const InfoWindow(title: 'Current Vehicle Position'),
        ),
    };

    if (_routePoints.isNotEmpty) {
      _polylines = {
        Polyline(
          polylineId: const PolylineId('approved_route'),
          points: _routePoints,
          color: const Color(0xFF1B5E20), // Rich forest green approved corridor
          width: 5,
        ),
      };
    } else if (_origin != null && _destination != null) {
      _polylines = {
        Polyline(
          polylineId: const PolylineId('route_direct'),
          points: [_origin!, _destination!],
          color: Colors.blueAccent,
          width: 3,
        ),
      };
    }
  }

  @override
  void dispose() {
    _positionSubscription?.cancel();
    _connectivitySubscription?.cancel();
    _trackingService.stopTracking();
    super.dispose();
  }

  void _launchExternalGoogleMaps() async {
    if (_origin == null || _destination == null) return;
    final googleMapsUrl = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&origin=${_origin!.latitude},${_origin!.longitude}&destination=${_destination!.latitude},${_destination!.longitude}&travelmode=driving',
    );
    if (await canLaunchUrl(googleMapsUrl)) {
      await launchUrl(googleMapsUrl, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not launch external Google Maps navigation')),
        );
      }
    }
  }

  Future<void> _showObstructionReportDialog() async {
    String selectedReason = 'ROAD_CLOSED';
    final notesController = TextEditingController();
    bool isSubmitting = false;

    final reasons = [
      {'value': 'ROAD_CLOSED', 'label': 'Road Closed / Construction'},
      {'value': 'TRAFFIC_DIVERSION', 'label': 'Traffic Police Diversion'},
      {'value': 'ACCIDENT', 'label': 'Accident Ahead'},
      {'value': 'VEHICLE_BREAKDOWN', 'label': 'Vehicle Issue / Breakdown'},
      {'value': 'CUSTOMER_INSTRUCTION', 'label': 'Customer Route Request'},
      {'value': 'NAVIGATION_ERROR', 'label': 'Navigation Reroute Needed'},
      {'value': 'OTHER', 'label': 'Other Operational Reason'},
    ];

    await showDialog(
      context: context,
      barrierDismissible: !isSubmitting,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.report_problem, color: Colors.amber),
              SizedBox(width: 8),
              Text('Report Obstruction / Detour', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Select the reason for taking an alternate path. This updates fleet dispatch and prevents unwarranted deviation alerts.',
                  style: TextStyle(fontSize: 13, color: Colors.grey),
                ),
                const SizedBox(height: 16),
                const Text('Reason', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: selectedReason,
                  isExpanded: true,
                  decoration: InputDecoration(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  items: reasons.map((r) {
                    return DropdownMenuItem<String>(
                      value: r['value'],
                      child: Text(r['label']!, style: const TextStyle(fontSize: 13)),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setDialogState(() => selectedReason = val);
                    }
                  },
                ),
                const SizedBox(height: 16),
                const Text('Additional Notes (Optional)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 8),
                TextField(
                  controller: notesController,
                  maxLines: 2,
                  decoration: InputDecoration(
                    hintText: 'e.g., Highway bridge blocked, diverted via state toll road',
                    hintStyle: const TextStyle(fontSize: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: isSubmitting ? null : () => Navigator.pop(dialogCtx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
              ),
              onPressed: isSubmitting
                  ? null
                  : () async {
                      setDialogState(() => isSubmitting = true);
                      try {
                        final tripRepo = ref.read(tripRepositoryProvider);
                        await tripRepo.reportDeviationExplanation(
                          widget.tripId,
                          reason: selectedReason,
                          notes: notesController.text.trim(),
                        );
                        if (dialogCtx.mounted) {
                          Navigator.pop(dialogCtx);
                        }
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              backgroundColor: Colors.green,
                              content: Text('Reason recorded. Fleet manager notified of detour.'),
                            ),
                          );
                          ref.invalidate(singleTripProvider(widget.tripId.toString()));
                        }
                      } catch (err) {
                        setDialogState(() => isSubmitting = false);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              backgroundColor: Colors.red,
                              content: Text('Failed to submit report: $err'),
                            ),
                          );
                        }
                      }
                    },
              child: isSubmitting
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Submit Report'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tripAsync = ref.watch(singleTripProvider(widget.tripId.toString()));

    return tripAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: Text('Live Navigation — Trip #${widget.tripId}')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (err, stack) => Scaffold(
        appBar: AppBar(title: Text('Live Navigation — Trip #${widget.tripId}')),
        body: Center(child: Text('Error: $err')),
      ),
      data: (trip) {
        if (_origin == null && trip['origin_lat'] != null && trip['origin_lng'] != null) {
          _origin = LatLng(trip['origin_lat'], trip['origin_lng']);
          _destination = LatLng(
            trip['destination_lat'] ?? _origin!.latitude,
            trip['destination_lng'] ?? _origin!.longitude,
          );
          _distanceLeft = trip['route_distance_km'] != null
              ? '${trip['route_distance_km']} km'
              : (trip['total_distance_km'] != null ? '${trip['total_distance_km']} km' : '-- km');
          _eta = trip['route_duration_hours'] != null
              ? '${(trip['route_duration_hours'] * 60).round()} min'
              : (trip['eta_minutes'] != null ? '${trip['eta_minutes']} min' : '-- min');

          final polylineStr = trip['route_polyline'] as String?;
          if (polylineStr != null && polylineStr.isNotEmpty) {
            try {
              _routePoints = decodePolyline(polylineStr);
            } catch (e) {
              debugPrint('Error decoding polyline: $e');
            }
          }

          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted) setState(() => _updateMarkers());
          });
        }

        final routeStatus = trip['route_status'] as String? ?? 'APPROVED';
        final isDeviated = routeStatus == 'DEVIATION_SUSPECTED' || routeStatus == 'DEVIATION_CONFIRMED';

        return Scaffold(
          appBar: AppBar(
            title: Text('Trip #${widget.tripId} Navigation'),
            actions: [
              IconButton(
                icon: const Icon(Icons.directions),
                tooltip: 'Turn-by-Turn Guidance in Google Maps',
                onPressed: _origin != null && _destination != null ? _launchExternalGoogleMaps : null,
              ),
            ],
          ),
          body: Stack(
            children: [
              // --- Google Map ---
              if (_origin != null)
                GoogleMap(
                  initialCameraPosition: CameraPosition(
                    target: _currentPosition != null
                        ? LatLng(_currentPosition!.latitude, _currentPosition!.longitude)
                        : _origin!,
                    zoom: 12.0,
                  ),
                  markers: _markers,
                  polylines: _polylines,
                  myLocationEnabled: true,
                  myLocationButtonEnabled: true,
                  compassEnabled: true,
                  mapToolbarEnabled: false,
                  onMapCreated: (GoogleMapController controller) {
                    _mapController = controller;
                    _updateMarkers();
                  },
                )
              else
                const Center(
                  child: Text('No coordinates available for this trip.', style: TextStyle(color: Colors.grey)),
                ),

              // --- Top Alerts: Offline / Deviation Status Banner ---
              Positioned(
                top: 8,
                left: 12,
                right: 12,
                child: Column(
                  children: [
                    if (_isOffline)
                      Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.black87,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.cloud_off, color: Colors.orangeAccent, size: 18),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Offline Mode: Showing cached route. Live updates queued.',
                                style: TextStyle(color: Colors.white, fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                    if (isDeviated)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.red.shade700,
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: [
                            BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 4, offset: const Offset(0, 2)),
                          ],
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 22),
                            const SizedBox(width: 8),
                            const Expanded(
                              child: Text(
                                'Off Approved Corridor! Maintain course or report detour.',
                                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                            ),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: Colors.red.shade900,
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                minimumSize: Size.zero,
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              onPressed: _showObstructionReportDialog,
                              child: const Text('Report', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),

              // --- Bottom Floating Navigation Card ---
              Positioned(
                bottom: 24,
                left: 16,
                right: 16,
                child: Card(
                  elevation: 8,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Distance', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                Text(_distanceLeft, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                const Text('Status', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: isDeviated ? Colors.red.shade50 : Colors.green.shade50,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    routeStatus,
                                    style: TextStyle(
                                      color: isDeviated ? Colors.red.shade800 : Colors.green.shade800,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                const Text('Est. Time', style: TextStyle(fontSize: 11, color: Colors.grey)),
                                Text(_eta, style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 16)),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              flex: 3,
                              child: ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF1B5E20),
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: _origin != null && _destination != null ? _launchExternalGoogleMaps : null,
                                icon: const Icon(Icons.navigation, size: 18),
                                label: const Text('Start Turn-by-Turn', style: TextStyle(fontSize: 13)),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              flex: 2,
                              child: OutlinedButton.icon(
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: _showObstructionReportDialog,
                                icon: const Icon(Icons.traffic, size: 16, color: Colors.amber),
                                label: const Text('Detour', style: TextStyle(fontSize: 12)),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
