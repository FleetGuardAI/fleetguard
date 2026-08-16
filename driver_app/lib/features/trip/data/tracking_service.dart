import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import '../../../core/config/app_config.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';

final trackingServiceProvider = Provider<TrackingService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TrackingService(apiClient.dio);
});

class TrackingService {
  final Dio _dio;
  WebSocketChannel? _channel;
  StreamSubscription<Position>? _positionSubscription;

  TrackingService(this._dio);

  Future<void> startTracking() async {
    // 1. Request Permission
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions are denied');
      }
    }
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions are permanently denied');
    }

    final driverId = await SecureStorage.getDriverId() ?? 1;
    final token = await SecureStorage.getAccessToken() ?? "demo_token";

    // 2. Connect to WebSocket
    final wsUrl = '${AppConfig.wsBaseUrl}/api/v1/ws/driver/$driverId?token=$token';
    
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

    // 3. Start Location Updates
    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10, // Update every 10 meters
    );

    _positionSubscription = Geolocator.getPositionStream(locationSettings: locationSettings).listen(
      (Position position) {
        // Send to WebSocket
        _sendLocation(position, driverId);
        // Also upload batch (or handle it depending on backend preference)
        _uploadLocationBatch(position, driverId);
      },
      onError: (e) => print('Geolocator error: $e'),
    );
  }

  void _sendLocation(Position position, int driverId) {
    if (_channel != null) {
      final message = {
        'type': 'location_update',
        'driver_id': driverId,
        'lat': position.latitude,
        'lng': position.longitude,
      };
      _channel!.sink.add(jsonEncode(message));
    }
  }

  Future<void> _uploadLocationBatch(Position position, int driverId) async {
    try {
      await _dio.post('/api/v1/driver-app/location/batch', data: {
        'driver_id': driverId,
        'locations': [
          {
            'latitude': position.latitude,
            'longitude': position.longitude,
            'speed': position.speed,
            'heading': position.heading,
            'accuracy': position.accuracy,
            'timestamp': DateTime.now().toUtc().toIso8601String(),
            'source': 'PHONE_GPS'
          }
        ]
      });
    } catch (e) {
      print('Batch upload error: $e');
    }
  }

  void stopTracking() {
    _positionSubscription?.cancel();
    _channel?.sink.close();
  }
}
