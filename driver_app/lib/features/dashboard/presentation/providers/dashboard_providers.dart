import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/data/auth_repository.dart';
import '../../trip/data/trip_repository.dart';

final driverProfileProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final authRepo = ref.watch(authRepositoryProvider);
  return await authRepo.getProfile();
});

final todayTripsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final tripRepo = ref.watch(tripRepositoryProvider);
  return await tripRepo.getTodayTrips();
});
