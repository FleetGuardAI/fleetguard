import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart';
import '../../data/tracking_service.dart';

class ActiveTripScreen extends ConsumerStatefulWidget {

  const ActiveTripScreen({super.key, required this.tripId});
  final int tripId;

  @override
  ConsumerState<ActiveTripScreen> createState() => _ActiveTripScreenState();
}

class _ActiveTripScreenState extends ConsumerState<ActiveTripScreen> {
  // Mumbai to Pune Highway sample coordinates
  final LatLng _origin = const LatLng(18.9500, 72.9500); // JNPT Navi Mumbai
  final LatLng _destination = const LatLng(18.5204, 73.8567); // Pune
  
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
          if (_mapController != null) {
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
      Marker(
        markerId: const MarkerId('origin'),
        position: _origin,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
      ),
      Marker(
        markerId: const MarkerId('destination'),
        position: _destination,
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

    _polylines = {
      Polyline(
        polylineId: const PolylineId('route'),
        points: [_origin, _destination],
        color: Colors.blue,
        width: 4,
      )
    };
  }

  @override
  void dispose() {
    _positionSubscription?.cancel();
    _trackingService.stopTracking();
    super.dispose();
  }

  void _launchExternalGoogleMaps() async {
    final googleMapsUrl = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&origin=${_origin.latitude},${_origin.longitude}&destination=${_destination.latitude},${_destination.longitude}&travelmode=driving',
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
    return Scaffold(
      appBar: AppBar(
        title: Text('Live Map — Trip #${widget.tripId}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.directions),
            tooltip: 'Open in Google Maps App',
            onPressed: _launchExternalGoogleMaps,
          ),
        ],
      ),
      body: Stack(
        children: [
          // --- Google Maps Display ---
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: _origin,
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
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Distance Left: 28.5 km', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Text('ETA: 45 min', style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
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
                            onPressed: _launchExternalGoogleMaps,
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
  }
}
