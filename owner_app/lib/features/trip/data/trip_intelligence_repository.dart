import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import 'trip_intelligence_models.dart';

final tripIntelligenceRepositoryProvider = Provider<TripIntelligenceRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TripIntelligenceRepository(apiClient.dio);
});

class TripIntelligenceRepository {
  final Dio _dio;

  TripIntelligenceRepository(this._dio);

  Future<PreTripIntelligenceResponse> evaluateTripIntelligence(Map<String, dynamic> payload) async {
    try {
      final response = await _dio.post(
        '/api/v1/trips/intelligence/evaluate',
        data: payload,
      );
      return PreTripIntelligenceResponse.fromJson(response.data);
    } catch (e) {
      if (e is DioException) {
        throw Exception('Failed to evaluate trip intelligence [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}');
      }
      throw Exception('Failed to evaluate trip intelligence: $e');
    }
  }

  Future<LiveTripIntelligenceResponse> getLiveTripIntelligence(int tripId) async {
    try {
      final response = await _dio.get(
        '/api/v1/trips/$tripId/intelligence/live',
      );
      return LiveTripIntelligenceResponse.fromJson(response.data);
    } catch (e) {
      if (e is DioException) {
        throw Exception('Failed to load live intelligence [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}');
      }
      throw Exception('Failed to load live intelligence: $e');
    }
  }

  Future<PostTripIntelligenceResponse> getTripIntelligence(int tripId) async {
    try {
      final response = await _dio.get(
        '/api/v1/trips/$tripId/intelligence',
      );
      return PostTripIntelligenceResponse.fromJson(response.data);
    } catch (e) {
      if (e is DioException) {
        throw Exception('Failed to load post-trip intelligence [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}');
      }
      throw Exception('Failed to load post-trip intelligence: $e');
    }
  }

  Future<PreTripIntelligenceResponse> getPreTripIntelligenceSnapshot(int tripId) async {
    try {
      final response = await _dio.get(
        '/api/v1/trips/$tripId/intelligence/snapshot',
      );
      return PreTripIntelligenceResponse.fromJson(response.data);
    } catch (e) {
      if (e is DioException) {
        throw Exception('Failed to load pre-trip intelligence snapshot [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}');
      }
      throw Exception('Failed to load pre-trip intelligence snapshot: $e');
    }
  }
}
