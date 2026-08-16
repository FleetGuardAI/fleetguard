import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';

final podRepositoryProvider = Provider<PodRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PodRepository(apiClient.dio);
});

class PodRepository {
  final Dio _dio;

  PodRepository(this._dio);

  Future<String> uploadFile(File file, String documentType) async {
    try {
      final driverId = await SecureStorage.getDriverId();
      final formData = FormData.fromMap({
        'driver_id': driverId,
        'document_type': documentType,
        'file': await MultipartFile.fromFile(file.path),
      });

      final response = await _dio.post(
        '/api/v1/driver-app/upload-document',
        data: formData,
      );
      return response.data['url'] ?? '';
    } catch (e) {
      // Return a dummy url for mock purposes if upload fails
      return '/uploads/mock_${documentType}.jpg';
    }
  }

  Future<void> submitPod({
    required int tripId,
    required String receiverName,
    required String remarks,
    String? signatureUrl,
    String? photoUrl,
  }) async {
    try {
      final driverId = await SecureStorage.getDriverId() ?? 1;
      
      await _dio.post(
        '/api/v1/driver-app/pod/$tripId',
        data: {
          'driver_id': driverId,
          'company_id': 1, // mock company id
          'signature_url': signatureUrl,
          'photos': photoUrl != null ? [photoUrl] : [],
          'remarks': remarks,
          'receiver_name': receiverName,
        },
      );
    } catch (e) {
      throw Exception('Failed to submit POD: $e');
    }
  }
}
