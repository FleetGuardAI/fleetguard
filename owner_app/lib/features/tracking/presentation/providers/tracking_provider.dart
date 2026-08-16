import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/tracking_repository.dart';

final fleetLocationsProvider = StreamProvider<List<LiveDriverLocation>>((ref) async* {
  final repository = ref.watch(trackingRepositoryProvider);
  
  // Yield initial value
  yield await repository.getFleetLiveLocations();
  
  // Poll every 5 seconds for live tracking
  while (true) {
    await Future.delayed(const Duration(seconds: 5));
    try {
      yield await repository.getFleetLiveLocations();
    } catch (e) {
      // Keep previous state on error
      continue;
    }
  }
});
