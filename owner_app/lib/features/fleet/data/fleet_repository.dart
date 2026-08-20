import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

final fleetRepositoryProvider = Provider<FleetRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FleetRepository(apiClient.dio);
});

class Vehicle {
  final int id;
  final String licensePlate;
  final String make;
  final String model;
  final String status;

  Vehicle({required this.id, required this.licensePlate, required this.make, required this.model, required this.status});

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'],
      licensePlate: json['license_plate'] ?? '',
      make: json['make'] ?? '',
      model: json['model'] ?? '',
      status: json['status'] ?? 'UNKNOWN',
    );
  }
}

class Driver {
  final int id;
  final String name;
  final String phoneNumber;
  final String status;

  Driver({required this.id, required this.name, required this.phoneNumber, required this.status});

  factory Driver.fromJson(Map<String, dynamic> json) {
    return Driver(
      id: json['id'],
      name: json['name'] ?? '',
      phoneNumber: json['phone_number'] ?? '',
      status: json['status'] ?? 'UNKNOWN',
    );
  }
}

class FleetRepository {
  final Dio _dio;

  FleetRepository(this._dio);

  Future<String> generateInviteQR(String label) async {
    try {
      final response = await _dio.post('/api/v1/fleet/invite', data: {
        'label': label,
        'expires_in_days': 30,
      });
      return response.data['qr_data']; // This is the fleetguard://invite?token=... URL
    } catch (e) {
      throw Exception('Failed to generate invite: $e');
    }
  }

  Future<List<Vehicle>> getVehicles() async {
    try {
      final response = await _dio.get('/api/v1/vehicles');
      return (response.data as List).map((x) => Vehicle.fromJson(x)).toList();
    } catch (e) {
      throw Exception('Failed to load vehicles: $e');
    }
  }

  Future<List<Driver>> getDrivers() async {
    try {
      final response = await _dio.get('/api/v1/drivers');
      return (response.data as List).map((x) => Driver.fromJson(x)).toList();
    } catch (e) {
      throw Exception('Failed to load drivers: $e');
    }
  }

  Future<List<HardwareAsset>> getHardwareAssets() async {
    try {
      final response = await _dio.get('/api/v1/assets');
      return (response.data as List).map((x) => HardwareAsset.fromJson(x)).toList();
    } catch (e) {
      throw Exception('Failed to load hardware assets: $e');
    }
  }
}

class HardwareAsset {
  final int id;
  final String businessId;
  final String model;
  final String assetType;
  final String operationalStatus;
  final String installationStatus;
  final int? currentVehicleId;

  HardwareAsset({
    required this.id,
    required this.businessId,
    required this.model,
    required this.assetType,
    required this.operationalStatus,
    required this.installationStatus,
    this.currentVehicleId,
  });

  factory HardwareAsset.fromJson(Map<String, dynamic> json) {
    return HardwareAsset(
      id: json['id'],
      businessId: json['business_id'] ?? 'N/A',
      model: json['model'] ?? 'Unknown',
      assetType: json['asset_type'] ?? 'HARDWARE',
      operationalStatus: json['operational_status'] ?? 'UNKNOWN',
      installationStatus: json['installation_status'] ?? 'UNKNOWN',
      currentVehicleId: json['current_vehicle_id'],
    );
  }
}
