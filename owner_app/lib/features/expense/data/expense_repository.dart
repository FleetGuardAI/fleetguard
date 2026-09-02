import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

final fleetExpenseRepositoryProvider = Provider<FleetExpenseRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FleetExpenseRepository(apiClient.dio);
});

class FleetExpenseRepository {
  final Dio _dio;

  FleetExpenseRepository(this._dio);

  Future<List<Map<String, dynamic>>> listFleetExpenses() async {
    try {
      final response = await _dio.get('/api/v1/expenses');
      return List<Map<String, dynamic>>.from(response.data);
    } catch (e) {
      throw Exception('Failed to fetch fleet expenses: $e');
    }
  }

  Future<Map<String, dynamic>> getExpenseAnalytics() async {
    try {
      final response = await _dio.get('/api/v1/owner/dashboard/expense-analytics');
      return response.data;
    } catch (e) {
      throw Exception('Failed to fetch expense analytics: $e');
    }
  }

  Future<void> approveExpense(int expenseId) async {
    try {
      await _dio.patch('/api/v1/owner/dashboard/expenses/$expenseId/approve');
    } catch (e) {
      throw Exception('Failed to approve expense: $e');
    }
  }

  Future<void> rejectExpense(int expenseId) async {
    try {
      await _dio.patch('/api/v1/owner/dashboard/expenses/$expenseId/reject');
    } catch (e) {
      throw Exception('Failed to reject expense: $e');
    }
  }

  Future<Map<String, dynamic>> uploadReceiptForOCR(String filePath) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath, filename: filePath.split('/').last),
      });
      final response = await _dio.post(
        '/api/v1/driver-app/expenses/ocr',
        data: formData,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to process receipt OCR: $e');
    }
  }

  Future<Map<String, dynamic>> createExpense(Map<String, dynamic> payload) async {
    try {
      final response = await _dio.post(
        '/api/v1/expenses',
        data: payload,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to submit expense: $e');
    }
  }

  Future<List<Map<String, dynamic>>> listWalletTransactions() async {
    try {
      final response = await _dio.get('/api/v1/owner/dashboard/wallet-transactions');
      return List<Map<String, dynamic>>.from(response.data);
    } catch (e) {
      throw Exception('Failed to fetch wallet transactions: $e');
    }
  }
}

