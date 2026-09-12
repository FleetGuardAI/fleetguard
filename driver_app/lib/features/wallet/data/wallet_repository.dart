import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

final walletRepositoryProvider = Provider<WalletRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return WalletRepository(apiClient.dio);
});

class WalletRepository {
  WalletRepository(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> getWalletSummary() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/wallet');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to get wallet summary: $e');
    }
  }

  Future<Map<String, dynamic>> requestAdvance({
    required double amount,
    String? reason,
  }) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/wallet/advance-request', data: {
        'amount': amount,
        if (reason != null) 'reason': reason,
      });
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to request advance: $e');
    }
  }
}
