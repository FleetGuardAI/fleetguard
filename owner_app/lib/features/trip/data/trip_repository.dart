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
  final double? originLat;
  final double? originLng;
  final double? destinationLat;
  final double? destinationLng;
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
  final String? routePolyline;
  final String? routeStatus;
  final double? routeDistanceKm;
  final double? routeDurationHours;
  final double? routeTollEstimate;
  final int? approvedRouteVersionId;

  OwnerTrip({
    required this.id,
    required this.tripId,
    required this.status,
    this.originLocation,
    this.destinationLocation,
    this.originLat,
    this.originLng,
    this.destinationLat,
    this.destinationLng,
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
    this.routePolyline,
    this.routeStatus,
    this.routeDistanceKm,
    this.routeDurationHours,
    this.routeTollEstimate,
    this.approvedRouteVersionId,
  });

  factory OwnerTrip.fromJson(Map<String, dynamic> json) {
    return OwnerTrip(
      id: json['id'],
      tripId: json['trip_id'],
      status: json['status'],
      originLocation: json['origin_location'],
      destinationLocation: json['destination_location'],
      originLat: json['origin_lat'] != null ? (json['origin_lat'] as num).toDouble() : null,
      originLng: json['origin_lng'] != null ? (json['origin_lng'] as num).toDouble() : null,
      destinationLat: json['destination_lat'] != null ? (json['destination_lat'] as num).toDouble() : null,
      destinationLng: json['destination_lng'] != null ? (json['destination_lng'] as num).toDouble() : null,
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
      routePolyline: json['route_polyline'],
      routeStatus: json['route_status'],
      routeDistanceKm: json['route_distance_km'] != null ? (json['route_distance_km'] as num).toDouble() : null,
      routeDurationHours: json['route_duration_hours'] != null ? (json['route_duration_hours'] as num).toDouble() : null,
      routeTollEstimate: json['route_toll_estimate'] != null ? (json['route_toll_estimate'] as num).toDouble() : null,
      approvedRouteVersionId: json['approved_route_version_id'],
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

  Future<OwnerTrip> getTripDetail(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/driver-app/trips/$tripId');
      return OwnerTrip.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load trip detail: $e');
    }
  }

  Future<Map<String, dynamic>> calculateRoutes(int tripId) async {
    try {
      final response = await _dio.post('/api/v1/trips/$tripId/routes/calculate');
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to calculate routes: $e');
    }
  }

  Future<Map<String, dynamic>> approveRoute(int tripId, {required String routeId, String? reason}) async {
    try {
      final response = await _dio.post(
        '/api/v1/trips/$tripId/routes/approve',
        data: {
          'route_id': routeId,
          if (reason != null) 'approval_reason': reason,
        },
      );
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to approve route: $e');
    }
  }

  Future<Map<String, dynamic>> getActiveRoute(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/trips/$tripId/routes/active');
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to fetch active route: $e');
    }
  }

  Future<List<dynamic>> getRouteVersions(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/trips/$tripId/routes/versions');
      return response.data as List<dynamic>;
    } catch (e) {
      throw Exception('Failed to fetch route versions: $e');
    }
  }

  Future<Map<String, dynamic>> recalculateRoute(
    int tripId, {
    required double currentLat,
    required double currentLng,
    String? reason,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/trips/$tripId/routes/recalculate',
        data: {
          'current_latitude': currentLat,
          'current_longitude': currentLng,
          if (reason != null) 'reason': reason,
        },
      );
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to recalculate route: $e');
    }
  }

  Future<List<dynamic>> getDeviations(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/trips/$tripId/deviations');
      return response.data as List<dynamic>;
    } catch (e) {
      throw Exception('Failed to fetch deviation incidents: $e');
    }
  }

  Future<Map<String, dynamic>> acknowledgeDeviation(int tripId, int eventId, {String? notes}) async {
    try {
      final response = await _dio.post(
        '/api/v1/trips/$tripId/deviations/$eventId/acknowledge',
        data: {if (notes != null) 'notes': notes},
      );
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to acknowledge deviation: $e');
    }
  }

  Future<Map<String, dynamic>> resolveDeviation(int tripId, int eventId, {required String resolutionNotes}) async {
    try {
      final response = await _dio.post(
        '/api/v1/trips/$tripId/deviations/$eventId/resolve',
        data: {'resolution_notes': resolutionNotes},
      );
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to resolve deviation: $e');
    }
  }

  Future<List<dynamic>> getDriverLocations(int driverId) async {
    try {
      final response = await _dio.get('/api/v1/tracking/driver/$driverId/locations');
      return response.data as List<dynamic>;
    } catch (e) {
      return [];
    }
  }
}
