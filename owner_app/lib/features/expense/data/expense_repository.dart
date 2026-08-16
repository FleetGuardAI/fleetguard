import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

final fleetExpenseRepositoryProvider = Provider<FleetExpenseRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FleetExpenseRepository(apiClient.dio);
});

class FleetExpenseRepository {
  final Dio _dio;

  FleetExpenseRepository(this._dio);

  Future<List<Map<String, dynamic>>> listFleetExpenses() async {
    try {
      final response = await _dio.get('/api/v1/expenses');
      return List<Map<String, dynamic>>.from(response.data);
    } catch (e) {
      throw Exception('Failed to fetch fleet expenses: $e');
    }
  }
}
