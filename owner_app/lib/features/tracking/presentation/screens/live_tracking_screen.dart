import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/config/app_config.dart';
import '../providers/tracking_provider.dart';
import 'dart:async';

class LiveTrackingScreen extends ConsumerStatefulWidget {
  const LiveTrackingScreen({super.key});

  @override
  ConsumerState<LiveTrackingScreen> createState() => _LiveTrackingScreenState();
}

class _LiveTrackingScreenState extends ConsumerState<LiveTrackingScreen> {
  final MapController _mapController = MapController();
  bool _isMapReady = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final locationsAsync = ref.watch(fleetLocationsProvider);
    final geoapifyKey = AppConfig.geoapifyApiKey;

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
          if (geoapifyKey.isEmpty) {
            return Center(
              child: Text(
                'Map unavailable - API key is missing.',
                style: TextStyle(color: AppColors.statusRed, fontSize: 16),
              ),
            );
          }

          final markers = locations.map((loc) {
            return Marker(
              point: LatLng(loc.latitude, loc.longitude),
              width: 40,
              height: 40,
              child: const Icon(
                Icons.local_shipping,
                color: AppColors.statusGreen,
                size: 30,
              ),
            );
          }).toList();

          LatLng center = locations.isNotEmpty ? LatLng(locations.first.latitude, locations.first.longitude) : const LatLng(28.6139, 77.2090);

          return Stack(
            children: [
              FlutterMap(
                mapController: _mapController,
                options: MapOptions(
                  initialCenter: center,
                  initialZoom: locations.isNotEmpty ? 6.0 : 10.0,
                  onMapReady: () {
                    setState(() {
                      _isMapReady = true;
                    });
                    if (locations.isNotEmpty) {
                      _fitAllMarkers(locations);
                    }
                  },
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
    if (locations.isEmpty || !_isMapReady) return;
    
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

    _mapController.fitCamera(
      CameraFit.bounds(
        bounds: LatLngBounds(
          LatLng(minLat, minLong),
          LatLng(maxLat, maxLong),
        ),
        padding: const EdgeInsets.all(50.0),
      ),
    );
  }
}
