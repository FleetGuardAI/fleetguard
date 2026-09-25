import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../../models/offline_record.dart';
import '../../../services/sync_service.dart';
import 'package:isar/isar.dart';

final expenseRepositoryProvider = Provider<ExpenseRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ExpenseRepository(apiClient.dio);
});

class ExpenseRepository {

  ExpenseRepository(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> processReceiptOcr(File file) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path, filename: 'receipt.jpg'),
      });
      final response = await _dio.post(
        '/api/v1/driver-app/expenses/ocr',
        data: formData,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      final detail = e.response?.data?['detail'] ?? 'Failed to process receipt (HTTP ${e.response?.statusCode})';
      throw Exception(detail);
    } catch (e) {
      throw Exception('Failed to process receipt: $e');
    }
  }

  Future<Map<String, dynamic>> createExpense({
    required String category,
    required double amount,
    required String description,
    String? base64ReceiptImage,
  }) async {
    try {
      final connectivityResult = await (Connectivity().checkConnectivity());
      if (connectivityResult == ConnectivityResult.none) {
        // Offline -> Save to Isar
        final syncService = await SyncService.init();
        final expense = OfflineExpense()
          ..amount = amount
          ..category = category
          ..description = description
          ..isSynced = false
          ..base64ReceiptImage = base64ReceiptImage ?? ''
          ..createdAt = DateTime.now();
          
        await syncService.isar.writeTxn(() async {
          await syncService.isar.offlineExpenses.put(expense);
        });
        
        return {'status': 'queued', 'message': 'Saved offline. Will sync when connected.'};
      }

      // Online
      final response = await _dio.post('/api/v1/driver-app/expenses', data: {
        'category': category,
        'amount': amount,
        'description': description,
      });
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to create expense: $e');
    }
  }

  Future<List<Map<String, dynamic>>> listDriverExpenses() async {
    try {
      final syncService = await SyncService.init();
      final offlineExpenses = await syncService.isar.offlineExpenses.filter().isSyncedEqualTo(false).findAll();
      
      final localData = offlineExpenses.map((e) => {
        'id': 'offline_${e.id}',
        'category': e.category,
        'amount': e.amount,
        'description': e.description,
        'expense_date': e.createdAt.toIso8601String(),
        'status': 'PENDING SYNC',
      }).toList();

      List<Map<String, dynamic>> remoteData = [];
      try {
        final connectivityResult = await (Connectivity().checkConnectivity());
        if (connectivityResult != ConnectivityResult.none) {
          final response = await _dio.get('/api/v1/driver-app/expenses');
          remoteData = List<Map<String, dynamic>>.from(response.data);
        }
      } catch (_) {}

      return [...localData, ...remoteData];
    } catch (e) {
      throw Exception('Failed to fetch expenses: $e');
    }
  }
}
