import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../dashboard/data/dashboard_repository.dart';
import '../../../trip/data/trip_repository.dart';
import '../../data/expense_repository.dart';

final selectedPeriodProvider = StateProvider<String>((ref) => 'This Month');

bool _isDateInPeriod(DateTime date, String period) {
  final now = DateTime.now();
  DateTime start;
  DateTime end = now;
  switch (period) {
    case 'This Month':
      start = DateTime(now.year, now.month, 1);
      break;
    case 'Last Month':
      start = DateTime(now.year, now.month - 1, 1);
      end = DateTime(now.year, now.month, 0, 23, 59, 59);
      break;
    case 'Last 3 Months':
      start = DateTime(now.year, now.month - 3, 1);
      break;
    case 'Last 6 Months':
      start = DateTime(now.year, now.month - 6, 1);
      break;
    case 'This Year':
      start = DateTime(now.year, 1, 1);
      break;
    default:
      start = DateTime(now.year, now.month, 1);
  }
  return date.isAfter(start.subtract(const Duration(days: 1))) && date.isBefore(end.add(const Duration(days: 1)));
}

final fleetReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final dashboardRepo = ref.watch(dashboardRepositoryProvider);
  final tripRepo = ref.watch(ownerTripRepositoryProvider);
  final expenseRepo = ref.watch(fleetExpenseRepositoryProvider);
  final period = ref.watch(selectedPeriodProvider);

  // Fetch concurrently
  final results = await Future.wait<dynamic>([
    dashboardRepo.getKPIs().catchError((_) => DashboardKPIs(totalActiveTrucks: 0, totalActiveDrivers: 0, activeTrips: 0, monthlyExpenses: 0, attentionRequired: 0)),
    expenseRepo.listFleetExpenses().catchError((_) => []),
    tripRepo.getFleetTrips().catchError((_) => []),
  ]);

  final kpis = results[0] as DashboardKPIs;
  
  // Filter expenses by selected period
  final allExpenses = results[1] as List<dynamic>;
  final expenses = allExpenses.where((e) {
    final dateStr = e['expense_date'];
    if (dateStr == null) return false;
    return _isDateInPeriod(DateTime.parse(dateStr).toLocal(), period);
  }).toList();

  // Filter trips by selected period
  final allTrips = results[2] as List<dynamic>;
  final trips = allTrips.where((t) {
    if (t is OwnerTrip) {
      final dateStr = t.actualStartTime ?? t.plannedStartTime;
      if (dateStr == null || dateStr == 'Not available') return false;
      try {
        return _isDateInPeriod(DateTime.parse(dateStr).toLocal(), period);
      } catch (_) { return false; }
    }
    return false;
  }).toList();


  // Aggregate expenses by category
  final categoryTotals = <String, double>{};
  double totalExpense = 0;
  for (var e in expenses) {
    final cat = (e['category'] ?? 'OTHER').toString().toUpperCase();
    final amt = (e['amount'] ?? 0).toDouble();
    categoryTotals[cat] = (categoryTotals[cat] ?? 0) + amt;
    totalExpense += amt;
  }

  final expenseDistribution = categoryTotals.entries.map((e) {
    return {
      'name': e.key,
      'value': totalExpense > 0 ? ((e.value / totalExpense) * 100).round() : 0,
    };
  }).toList();

  // Compute mileage trend from real trip data (requires both distance and fuel)
  final mileageTrend = <Map<String, dynamic>>[];
  // Since the current OwnerTrip model lacks actualFuelLiters, this will naturally be empty
  // The UI will handle empty mileageTrend by showing "Insufficient data"
  // If actualFuelLiters is added later, we can calculate it here:
  // tripsByMonth[monthKey]['totalFuel'] += t.actualFuelLiters!

  return {
    'kpis': kpis,
    'mileageTrend': mileageTrend, // NEVER fallback to dummy data
    'expenseDistribution': expenseDistribution, // NEVER fallback to dummy data
  };
});
