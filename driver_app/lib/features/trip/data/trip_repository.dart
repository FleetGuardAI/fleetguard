import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

final tripRepositoryProvider = Provider<TripRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TripRepository(apiClient.dio);
});

class TripRepository {
  final Dio _dio;

  TripRepository(this._dio);

  Future<List<dynamic>> getTodayTrips() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/trips/today');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get today trips: $e');
    }
  }

  Future<Map<String, dynamic>> uploadTripStartSelfie(int tripId, File file) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path),
      });
      final response = await _dio.post(
        '/api/v1/driver-app/trips/$tripId/start-selfie',
        data: formData,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to upload start selfie: $e');
    }
  }

  Future<Map<String, dynamic>> startTrip(int tripId) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/trips/$tripId/start');
      return response.data;
    } catch (e) {
      throw Exception('Failed to start trip: $e');
    }
  }

  Future<Map<String, dynamic>> completeTrip(int tripId, [double? actualDistance]) async {
    try {
      final response = await _dio.post(
        '/api/v1/driver-app/trips/$tripId/complete',
        queryParameters: actualDistance != null ? {'actual_distance': actualDistance} : null,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to complete trip: $e');
    }
  }

  Future<Map<String, dynamic>> pauseTrip(int tripId) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/trips/$tripId/pause');
      return response.data;
    } catch (e) {
      throw Exception('Failed to pause trip: $e');
    }
  }

  Future<Map<String, dynamic>> resumeTrip(int tripId) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/trips/$tripId/resume');
      return response.data;
    } catch (e) {
      throw Exception('Failed to resume trip: $e');
    }
  }

  Future<Map<String, dynamic>> getTripDetail(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/driver-app/trips/$tripId');
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to get trip details: $e');
    }
  }

  Future<Map<String, dynamic>> reportDeviationExplanation(
    int tripId, {
    required String reason,
    String? notes,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/driver-app/trips/$tripId/deviation-explanation',
        data: {
          'reason': reason,
          if (notes != null && notes.isNotEmpty) 'notes': notes,
        },
      );
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to report deviation explanation: $e');
    }
  }

  Future<Map<String, dynamic>> getActiveRoute(int tripId) async {
    try {
      final response = await _dio.get('/api/v1/trips/$tripId/routes/active');
      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      throw Exception('Failed to get active route: $e');
    }
  }
}

