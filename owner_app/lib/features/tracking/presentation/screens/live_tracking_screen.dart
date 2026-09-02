import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/tracking_provider.dart';
import 'dart:async';

class LiveTrackingScreen extends ConsumerStatefulWidget {
  const LiveTrackingScreen({super.key});

  @override
  ConsumerState<LiveTrackingScreen> createState() => _LiveTrackingScreenState();
}

class _LiveTrackingScreenState extends ConsumerState<LiveTrackingScreen> {
  final Completer<GoogleMapController> _controller = Completer<GoogleMapController>();
  bool _isMapReady = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final locationsAsync = ref.watch(fleetLocationsProvider);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Live Tracking', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 2,
      ),
      body: locationsAsync.when(
        data: (locations) {
          final markers = locations.map((loc) {
            return Marker(
              markerId: MarkerId(loc.driverId.toString()),
              position: LatLng(loc.latitude, loc.longitude),
              infoWindow: InfoWindow(
                title: loc.driverName, 
                snippet: 'Status: ${loc.dutyStatus ?? 'Unknown'}',
              ),
              icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
            );
          }).toSet();

          // Calculate center and bounds if map is ready
          LatLng center = locations.isNotEmpty ? LatLng(locations.first.latitude, locations.first.longitude) : const LatLng(28.6139, 77.2090);

          return Stack(
            children: [
              GoogleMap(
                initialCameraPosition: CameraPosition(target: center, zoom: locations.isNotEmpty ? 6 : 10),
                markers: markers,
                myLocationEnabled: true,
                myLocationButtonEnabled: true,
                mapToolbarEnabled: false,
                zoomControlsEnabled: false,
                onMapCreated: (GoogleMapController controller) {
                  _controller.complete(controller);
                  setState(() {
                    _isMapReady = true;
                  });
                  if (locations.isNotEmpty) {
                    _fitAllMarkers(locations);
                  }
                },
              ),
              if (_isMapReady)
                Positioned(
                  top: 16,
                  left: 16,
                  right: 16,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground).withValues(alpha: 0.9),
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 8, offset: const Offset(0, 4)),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${locations.length} Vehicles Online',
                          style: TextStyle(fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                        ),
                        Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            color: locations.isNotEmpty ? AppColors.statusGreen : AppColors.statusRed,
                            shape: BoxShape.circle,
                          ),
                        )
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppColors.statusRed),
              const SizedBox(height: 16),
              const Text('Could not load tracking data', style: TextStyle(color: AppColors.statusRed, fontSize: 16)),
              const SizedBox(height: 8),
              Text(err.toString(), style: const TextStyle(color: AppColors.statusRed, fontSize: 12)),
            ],
          ),
        ),
      ),
      floatingActionButton: _isMapReady 
          ? FloatingActionButton(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              onPressed: () {
                final locs = ref.read(fleetLocationsProvider).value;
                if (locs != null && locs.isNotEmpty) {
                  _fitAllMarkers(locs);
                }
              },
              child: const Icon(Icons.my_location),
            )
          : null,
    );
  }

  Future<void> _fitAllMarkers(List locations) async {
    if (locations.isEmpty) return;
    
    final controller = await _controller.future;
    
    double minLat = locations.first.latitude;
    double minLong = locations.first.longitude;
    double maxLat = locations.first.latitude;
    double maxLong = locations.first.longitude;

    for (var loc in locations) {
      if (loc.latitude < minLat) minLat = loc.latitude;
      if (loc.longitude < minLong) minLong = loc.longitude;
      if (loc.latitude > maxLat) maxLat = loc.latitude;
      if (loc.longitude > maxLong) maxLong = loc.longitude;
    }

    controller.animateCamera(CameraUpdate.newLatLngBounds(
      LatLngBounds(
        southwest: LatLng(minLat, minLong),
        northeast: LatLng(maxLat, maxLong),
      ),
      50.0, // padding
    ));
  }
}
