import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return DashboardRepository(apiClient.dio);
});

class DashboardKPIs {
  final int totalActiveTrucks;
  final int totalActiveDrivers;
  final int activeTrips;
  final double monthlyExpenses;

  DashboardKPIs({
    required this.totalActiveTrucks,
    required this.totalActiveDrivers,
    required this.activeTrips,
    required this.monthlyExpenses,
  });

  factory DashboardKPIs.fromJson(Map<String, dynamic> json) {
    return DashboardKPIs(
      totalActiveTrucks: json['total_active_trucks'] ?? 0,
      totalActiveDrivers: json['total_active_drivers'] ?? 0,
      activeTrips: json['active_trips'] ?? 0,
      monthlyExpenses: (json['monthly_expenses'] ?? 0).toDouble(),
    );
  }
}

class DashboardRepository {
  final Dio _dio;

  DashboardRepository(this._dio);

  Future<DashboardKPIs> getKPIs() async {
    try {
      final response = await _dio.get('/api/v1/owner/dashboard/kpis');
      return DashboardKPIs.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load KPIs: $e');
    }
  }
}
