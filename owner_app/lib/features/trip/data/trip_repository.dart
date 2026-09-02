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
  final double? revenue;
  final double? plannedCost;
  final double? plannedFuelLiters;
  final double? cargoWeight;
  final double? plannedDistance;
  final double? actualDistance;

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
    this.revenue,
    this.plannedCost,
    this.plannedFuelLiters,
    this.cargoWeight,
    this.plannedDistance,
    this.actualDistance,
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
      revenue: json['revenue'] != null ? (json['revenue'] as num).toDouble() : null,
      plannedCost: json['planned_cost'] != null ? (json['planned_cost'] as num).toDouble() : null,
      plannedFuelLiters: json['planned_fuel_liters'] != null ? (json['planned_fuel_liters'] as num).toDouble() : null,
      cargoWeight: json['cargo_weight'] != null ? (json['cargo_weight'] as num).toDouble() : null,
      plannedDistance: json['planned_distance'] != null ? (json['planned_distance'] as num).toDouble() : null,
      actualDistance: json['actual_distance'] != null ? (json['actual_distance'] as num).toDouble() : null,
    );
  }
}

class OwnerTripRepository {
  final Dio _dio;

  OwnerTripRepository(this._dio);

  Future<List<OwnerTrip>> getFleetTrips({String? search, String? status}) async {
    try {
      final Map<String, dynamic> queryParameters = {};
      if (search != null && search.isNotEmpty) queryParameters['search'] = search;
      if (status != null && status != 'ALL') queryParameters['status'] = status;
      
      final response = await _dio.get(
        '/api/v1/owner/dashboard/trips',
        queryParameters: queryParameters,
      );
      final data = response.data as List;
      return data.map((e) => OwnerTrip.fromJson(e)).toList();
    } catch (e) {
      throw Exception('Failed to load trips: $e');
    }
  }
}
