import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/fleet_repository.dart';

final vehicleSearchProvider = StateProvider<String>((ref) => '');
final driverSearchProvider = StateProvider<String>((ref) => '');
final hardwareSearchProvider = StateProvider<String>((ref) => '');
final vehicleStatusProvider = StateProvider<String>((ref) => 'ALL');

final vehiclesProvider = FutureProvider<List<Vehicle>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  final search = ref.watch(vehicleSearchProvider);
  final status = ref.watch(vehicleStatusProvider);
  return repository.getVehicles(search: search, status: status);
});

final driversProvider = FutureProvider<List<Driver>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getDrivers();
});

final hardwareAssetsProvider = FutureProvider<List<HardwareAsset>>((ref) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getHardwareAssets();
});

final vehicleInsightsProvider = FutureProvider.family<Map<String, dynamic>, int>((ref, vehicleId) async {
  final repository = ref.watch(fleetRepositoryProvider);
  return repository.getVehicleInsights(vehicleId);
});
