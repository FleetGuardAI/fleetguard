import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/trip_repository.dart';

final tripSearchProvider = StateProvider<String>((ref) => '');
final tripStatusProvider = StateProvider<String>((ref) => 'ALL');

final fleetTripsProvider = StreamProvider.autoDispose<List<OwnerTrip>>((ref) async* {
  final repo = ref.watch(ownerTripRepositoryProvider);
  final search = ref.watch(tripSearchProvider);
  final status = ref.watch(tripStatusProvider);

  // Initial fetch
  yield await repo.getFleetTrips(search: search, status: status);

  // Poll every 10 seconds
  while (true) {
    await Future.delayed(const Duration(seconds: 10));
    try {
      yield await repo.getFleetTrips(search: search, status: status);
    } catch (e) {
      // Continue polling even if a single request fails
      continue;
    }
  }
});
