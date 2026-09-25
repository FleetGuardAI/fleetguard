import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../../models/offline_record.dart';
import '../../../services/sync_service.dart';

final podRepositoryProvider = Provider<PodRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PodRepository(apiClient.dio);
});

class PodRepository {

  PodRepository(this._dio);
  final Dio _dio;

  Future<String> uploadFile(File file, String documentType) async {
    try {
      final formData = FormData.fromMap({
        'document_type': documentType,
        'file': await MultipartFile.fromFile(file.path),
      });

      final response = await _dio.post(
        '/api/v1/driver-app/upload-document',
        data: formData,
      );
      return response.data['url'] ?? '';
    } catch (e) {
      throw Exception('Failed to upload $documentType: $e');
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
      final connectivityResult = await (Connectivity().checkConnectivity());
      if (connectivityResult == ConnectivityResult.none) {
        // Offline -> Save to Isar
        final syncService = await SyncService.init();
        final pod = OfflinePOD()
          ..tripId = tripId.toString()
          ..base64Image = photoUrl ?? ''
          ..notes = remarks
          ..isSynced = false
          ..createdAt = DateTime.now();
          
        await syncService.isar.writeTxn(() async {
          await syncService.isar.offlinePODs.put(pod);
        });
        return;
      }

      // Online
      await _dio.post(
        '/api/v1/driver-app/pod/$tripId',
        data: {
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
