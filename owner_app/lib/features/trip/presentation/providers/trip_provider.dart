import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/trip_repository.dart';

final fleetTripsProvider = StreamProvider.autoDispose<List<OwnerTrip>>((ref) async* {
  final repo = ref.watch(ownerTripRepositoryProvider);

  // Initial fetch
  yield await repo.getFleetTrips();

  // Poll every 10 seconds
  while (true) {
    await Future.delayed(const Duration(seconds: 10));
    try {
      yield await repo.getFleetTrips();
    } catch (e) {
      // Continue polling even if a single request fails
      continue;
    }
  }
});
