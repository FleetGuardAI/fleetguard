import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

final fleetRepositoryProvider = Provider<FleetRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FleetRepository(apiClient.dio);
});

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
}
