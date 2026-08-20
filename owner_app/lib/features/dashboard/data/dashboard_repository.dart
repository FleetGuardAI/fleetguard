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
  final int attentionRequired;

  DashboardKPIs({
    required this.totalActiveTrucks,
    required this.totalActiveDrivers,
    required this.activeTrips,
    required this.monthlyExpenses,
    required this.attentionRequired,
  });

  factory DashboardKPIs.fromJson(Map<String, dynamic> json) {
    return DashboardKPIs(
      totalActiveTrucks: json['total_active_trucks'] ?? 0,
      totalActiveDrivers: json['total_active_drivers'] ?? 0,
      activeTrips: json['active_trips'] ?? 0,
      monthlyExpenses: (json['monthly_expenses'] ?? 0).toDouble(),
      attentionRequired: json['attention_required'] ?? 0,
    );
  }
}

class RecentActivityItem {
  final int id;
  final String title;
  final String description;
  final String type;
  final String status;
  final String? timestamp;

  RecentActivityItem({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.status,
    this.timestamp,
  });

  factory RecentActivityItem.fromJson(Map<String, dynamic> json) {
    return RecentActivityItem(
      id: json['id'],
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      type: json['type'] ?? '',
      status: json['status'] ?? '',
      timestamp: json['timestamp'],
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

  Future<List<RecentActivityItem>> getRecentActivity() async {
    try {
      final response = await _dio.get('/api/v1/owner/dashboard/recent-activity');
      final data = response.data as List;
      return data.map((item) => RecentActivityItem.fromJson(item)).toList();
    } catch (e) {
      throw Exception('Failed to load recent activity: $e');
    }
  }
}
