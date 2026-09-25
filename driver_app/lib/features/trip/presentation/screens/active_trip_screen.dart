import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart';
import '../../data/tracking_service.dart';
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
  
  GoogleMapController? _mapController;
  Position? _currentPosition;
  Set<Marker> _markers = {};
  Set<Polyline> _polylines = {};
  
  StreamSubscription<Position>? _positionSubscription;
  late final TrackingService _trackingService;

  @override
  void initState() {
    super.initState();
    _trackingService = ref.read(trackingServiceProvider);
    _setupMapAndTracking();
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
          if (_mapController != null && _origin != null) {
            _mapController!.animateCamera(
              CameraUpdate.newLatLng(LatLng(position.latitude, position.longitude)),
            );
          }
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
        ),
      if (_destination != null)
        Marker(
          markerId: const MarkerId('destination'),
          position: _destination!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
        ),
      if (_currentPosition != null)
        Marker(
          markerId: const MarkerId('current'),
          position: LatLng(_currentPosition!.latitude, _currentPosition!.longitude),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
          infoWindow: const InfoWindow(title: 'You are here'),
        ),
    };

    if (_origin != null && _destination != null) {
      _polylines = {
        Polyline(
          polylineId: const PolylineId('route'),
          points: [_origin!, _destination!],
          color: Colors.blue,
          width: 4,
        )
      };
    }
  }

  @override
  void dispose() {
    _positionSubscription?.cancel();
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not launch Google Maps app')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final tripAsync = ref.watch(singleTripProvider(widget.tripId.toString()));

    return tripAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: Text('Live Map — Trip #${widget.tripId}')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (err, stack) => Scaffold(
        appBar: AppBar(title: Text('Live Map — Trip #${widget.tripId}')),
        body: Center(child: Text('Error: $err')),
      ),
      data: (trip) {
        // Only set these once if they haven't been set yet
        if (_origin == null && trip['origin_lat'] != null && trip['origin_lng'] != null) {
          _origin = LatLng(trip['origin_lat'], trip['origin_lng']);
          _destination = LatLng(trip['destination_lat'] ?? _origin!.latitude, trip['destination_lng'] ?? _origin!.longitude);
          _distanceLeft = trip['distance_remaining_km'] != null ? '${trip['distance_remaining_km']} km' : '-- km';
          _eta = trip['eta_minutes'] != null ? '${trip['eta_minutes']} min' : '-- min';
          // Trigger a re-render so the map updates with new markers
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted) setState(() => _updateMarkers());
          });
        }

        return Scaffold(
          appBar: AppBar(
            title: Text('Live Map — Trip #${widget.tripId}'),
            actions: [
              IconButton(
                icon: const Icon(Icons.directions),
                tooltip: 'Open in Google Maps App',
                onPressed: _origin != null && _destination != null ? _launchExternalGoogleMaps : null,
              ),
            ],
          ),
          body: Stack(
            children: [
              // --- Google Maps Display ---
              if (_origin != null)
                GoogleMap(
                  initialCameraPosition: CameraPosition(
                    target: _origin!,
                    zoom: 9.5,
                  ),
                  markers: _markers,
                  polylines: _polylines,
                  myLocationEnabled: true,
                  myLocationButtonEnabled: true,
                  onMapCreated: (GoogleMapController controller) {
                    _mapController = controller;
                    _updateMarkers(); // Initial setup
                  },
                )
              else
                const Center(
                  child: Text('No coordinates available for this trip.', style: TextStyle(color: Colors.grey)),
                ),

              // --- Bottom Floating Navigation Control Overlay ---
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
                            Text('Distance Left: $_distanceLeft', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            Text('ETA: $_eta', style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const LinearProgressIndicator(value: 0.78),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                onPressed: _origin != null && _destination != null ? _launchExternalGoogleMaps : null,
                                icon: const Icon(Icons.navigation, color: Colors.white),
                                label: const Text('Open Google Maps App', style: TextStyle(color: Colors.white)),
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
