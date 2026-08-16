import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

final ownerTripRepositoryProvider = Provider<OwnerTripRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return OwnerTripRepository(apiClient.dio);
});

class OwnerTrip {
  final int id;
  final String tripId;
  final String status;
  final String? originLocation;
  final String? destinationLocation;
  final int? driverId;
  final int? vehicleId;
  final Map<String, dynamic>? driver;
  final Map<String, dynamic>? vehicle;
  final String? plannedStartTime;
  final String? actualStartTime;
  final String? actualEndTime;

  OwnerTrip({
    required this.id,
    required this.tripId,
    required this.status,
    this.originLocation,
    this.destinationLocation,
    this.driverId,
    this.vehicleId,
    this.driver,
    this.vehicle,
    this.plannedStartTime,
    this.actualStartTime,
    this.actualEndTime,
  });

  factory OwnerTrip.fromJson(Map<String, dynamic> json) {
    return OwnerTrip(
      id: json['id'],
      tripId: json['trip_id'],
      status: json['status'],
      originLocation: json['origin_location'],
      destinationLocation: json['destination_location'],
      driverId: json['driver_id'],
      vehicleId: json['vehicle_id'],
      driver: json['driver'],
      vehicle: json['vehicle'],
      plannedStartTime: json['planned_start_time'],
      actualStartTime: json['actual_start_time'],
      actualEndTime: json['actual_end_time'],
    );
  }
}

class OwnerTripRepository {
  final Dio _dio;

  OwnerTripRepository(this._dio);

  Future<List<OwnerTrip>> getFleetTrips() async {
    try {
      final response = await _dio.get('/api/v1/owner/dashboard/trips');
      final data = response.data as List;
      return data.map((e) => OwnerTrip.fromJson(e)).toList();
    } catch (e) {
      throw Exception('Failed to load trips: $e');
    }
  }
}
