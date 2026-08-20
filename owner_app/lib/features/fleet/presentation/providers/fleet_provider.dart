import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/fleet_repository.dart';

final vehiclesProvider = FutureProvider<List<Vehicle>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getVehicles();
});

final driversProvider = FutureProvider<List<Driver>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getDrivers();
});

final hardwareAssetsProvider = FutureProvider<List<HardwareAsset>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getHardwareAssets();
});
