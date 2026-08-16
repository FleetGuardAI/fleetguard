import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';

final expenseRepositoryProvider = Provider<ExpenseRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ExpenseRepository(apiClient.dio);
});

class ExpenseRepository {
  final Dio _dio;

  ExpenseRepository(this._dio);

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
    } catch (e) {
      throw Exception('Failed to process receipt: $e');
    }
  }

  Future<Map<String, dynamic>> createExpense({
    required String category,
    required double amount,
    required String description,
    required int driverId,
  }) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/expenses', data: {
        'category': category,
        'amount': amount,
        'description': description,
        'driver_id': driverId,
      });
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to create expense: $e');
    }
  }

  Future<List<Map<String, dynamic>>> listDriverExpenses() async {
    try {
      final driverId = await SecureStorage.getDriverId();
      if (driverId == null) throw Exception('Driver not found in storage');

      final response = await _dio.get(
        '/api/v1/driver-app/expenses',
        queryParameters: {'driver_id': driverId},
      );
      return List<Map<String, dynamic>>.from(response.data);
    } catch (e) {
      throw Exception('Failed to fetch expenses: $e');
    }
  }
}
