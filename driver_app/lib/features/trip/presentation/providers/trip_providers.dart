import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/trip_repository.dart';
import '../../../dashboard/presentation/providers/dashboard_providers.dart';

final singleTripProvider = FutureProvider.family.autoDispose<Map<String, dynamic>, String>((ref, tripId) async {
  final trips = await ref.watch(todayTripsProvider.future);
  final trip = trips.firstWhere((t) => t['id'].toString() == tripId, orElse: () => null);
  if (trip == null) {
    throw Exception('Trip not found');
  }
  return trip;
});
