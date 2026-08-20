import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/dashboard_repository.dart';

final dashboardKPIsProvider = StreamProvider<DashboardKPIs>((ref) async* {
  final repository = ref.watch(dashboardRepositoryProvider);
  
  // Yield initial value
  yield await repository.getKPIs();
  
  // Poll every 15 seconds
  while (true) {
    await Future.delayed(const Duration(seconds: 15));
    try {
      yield await repository.getKPIs();
    } catch (e) {
      // Keep previous state on error
      continue;
    }
  }
});

final recentActivityProvider = StreamProvider<List<RecentActivityItem>>((ref) async* {
  final repository = ref.watch(dashboardRepositoryProvider);
  
  yield await repository.getRecentActivity();
  
  while (true) {
    await Future.delayed(const Duration(seconds: 15));
    try {
      yield await repository.getRecentActivity();
    } catch (e) {
      continue;
    }
  }
});
