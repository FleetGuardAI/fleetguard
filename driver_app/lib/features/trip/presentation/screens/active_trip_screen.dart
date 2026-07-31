import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';

class ActiveTripScreen extends StatefulWidget {
  final int tripId;

  const ActiveTripScreen({super.key, required this.tripId});

  @override
  State<ActiveTripScreen> createState() => _ActiveTripScreenState();
}

class _ActiveTripScreenState extends State<ActiveTripScreen> {
  // Mumbai to Pune Highway sample coordinates for OSM Map
  final LatLng _origin = const LatLng(18.9500, 72.9500); // JNPT Navi Mumbai
  final LatLng _destination = const LatLng(18.5204, 73.8567); // Pune

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
          // --- OpenStreetMap Display ---
          FlutterMap(
            options: MapOptions(
              initialCenter: const LatLng(18.75, 73.40),
              initialZoom: 9.5,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.fleetguard.driver',
              ),
              PolylineLayer(
                polylines: [
                  Polyline(
                    points: [_origin, const LatLng(18.78, 73.30), _destination],
                    strokeWidth: 4.0,
                    color: Colors.blue,
                  ),
                ],
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: _origin,
                    width: 40,
                    height: 40,
                    child: const Icon(Icons.location_on, color: Colors.green, size: 40),
                  ),
                  Marker(
                    point: _destination,
                    width: 40,
                    height: 40,
                    child: const Icon(Icons.flag, color: Colors.red, size: 40),
                  ),
                ],
              ),
            ],
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
