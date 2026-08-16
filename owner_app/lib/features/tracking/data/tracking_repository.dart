import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

final trackingRepositoryProvider = Provider<TrackingRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TrackingRepository(apiClient.dio);
});

class LiveDriverLocation {
  final int driverId;
  final String driverName;
  final double latitude;
  final double longitude;
  final String? dutyStatus;

  LiveDriverLocation({
    required this.driverId,
    required this.driverName,
    required this.latitude,
    required this.longitude,
    this.dutyStatus,
  });

  factory LiveDriverLocation.fromJson(Map<String, dynamic> json) {
    return LiveDriverLocation(
      driverId: json['driver_id'] ?? 0,
      driverName: json['driver_name'] ?? 'Unknown',
      latitude: json['latitude']?.toDouble() ?? 0.0,
      longitude: json['longitude']?.toDouble() ?? 0.0,
      dutyStatus: json['duty_status'],
    );
  }
}

class TrackingRepository {
  final Dio _dio;

  TrackingRepository(this._dio);

  Future<List<LiveDriverLocation>> getFleetLiveLocations() async {
    try {
      final response = await _dio.get('/api/v1/tracking/fleet/live');
      final data = response.data as List;
      return data.map((e) => LiveDriverLocation.fromJson(e)).toList();
    } catch (e) {
      throw Exception('Failed to fetch live locations: $e');
    }
  }
}
