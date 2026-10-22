import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthRepository(apiClient.dio);
});

class AuthRepository {

  AuthRepository(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> resolveQr(String qrData, [String? phoneNumber]) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/qr/resolve', data: {
        'qr_data': qrData,
        if (phoneNumber != null && phoneNumber.isNotEmpty) 'phone_number': phoneNumber,
      });
      final data = response.data;
      if (data is Map<String, dynamic>) return data;
      return Map<String, dynamic>.from(data as Map);
    } on DioException catch (e) {
      final err = e.response?.data;
      final msg = err is Map ? (err['detail'] ?? err['message']) : e.message;
      throw Exception(msg ?? 'Failed to resolve QR credential');
    } catch (e) {
      throw Exception('Failed to resolve QR: $e');
    }
  }

  Future<Map<String, dynamic>> requestFleetTransfer(String inviteToken, int targetCompanyId) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/fleet-transfer', data: {
        'invite_token': inviteToken,
        'target_company_id': targetCompanyId,
      });
      final data = response.data;
      if (data is Map<String, dynamic>) return data;
      return Map<String, dynamic>.from(data as Map);
    } on DioException catch (e) {
      final err = e.response?.data;
      final msg = err is Map ? (err['detail'] ?? err['message']) : e.message;
      throw Exception(msg ?? 'Failed to request fleet transfer');
    } catch (e) {
      throw Exception('Failed to request fleet transfer: $e');
    }
  }

  Future<Map<String, dynamic>> cancelFleetTransfer(int transferId) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/fleet-transfer/$transferId/cancel');
      final data = response.data;
      if (data is Map<String, dynamic>) return data;
      return Map<String, dynamic>.from(data as Map);
    } catch (e) {
      throw Exception('Failed to cancel fleet transfer: $e');
    }
  }

  Future<Map<String, dynamic>> getMe() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/me');
      final data = response.data;
      if (data is Map<String, dynamic>) return data;
      return Map<String, dynamic>.from(data as Map);
    } catch (e) {
      throw Exception('Failed to get driver details: $e');
    }
  }

  Future<Map<String, dynamic>> verifyInvite(String token) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/verify-invite', data: {
        'invite_token': token
      });
      return response.data; // { "valid": bool, "company_name": str, "company_id": int }
    } catch (e) {
      throw Exception('Failed to verify invite: $e');
    }
  }

  Future<Map<String, dynamic>> sendOtp(String phoneNumber) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/send-otp', data: {
        'phone_number': phoneNumber
      });
      return response.data;
    } catch (e) {
      throw Exception('Failed to send OTP: $e');
    }
  }

  Future<Map<String, dynamic>> resendOtp(String reqId) async {
    try {
      final response = await _dio.post('/api/v1/auth/resend-otp', data: {
        'req_id': reqId
      });
      return response.data; 
    } catch (e) {
      throw Exception('Failed to resend OTP: $e');
    }
  }

  Future<Map<String, dynamic>> verifyOtp(String phoneNumber, String reqId, String otp, [String? inviteToken, String? msg91Token]) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/verify-otp', data: {
        'phone_number': phoneNumber,
        'req_id': reqId,
        'otp_code': otp,
        if (inviteToken != null && inviteToken.isNotEmpty) 'invite_token': inviteToken,
        if (msg91Token != null) 'msg91_token': msg91Token,
      });
      final data = response.data;
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
      if (data is String) return {'message': data};
      if (data is List) return {'data': data};
      return {'data': data?.toString() ?? 'Success'};
    } on DioException catch (e) {
      final errorData = e.response?.data;
      debugPrint('[AUTH REPO] HTTP ${e.response?.statusCode}: ${e.response?.statusMessage}');
      debugPrint('[AUTH REPO] Endpoint: ${e.requestOptions.path}');
      debugPrint('[AUTH REPO] Request keys: ${e.requestOptions.data.keys.toList()}');
      
      String errorDetail = 'Unknown error';
      if (errorData is Map) {
        debugPrint('[AUTH REPO] Error body: $errorData');
        errorDetail = errorData['detail']?.toString() ?? errorData['message']?.toString() ?? e.message ?? errorDetail;
      } else if (errorData is String) {
        debugPrint('[AUTH REPO] Error data string: $errorData');
        errorDetail = errorData.isNotEmpty ? errorData : (e.message ?? errorDetail);
      } else if (errorData is List) {
        debugPrint('[AUTH REPO] Error data list: $errorData');
        errorDetail = errorData.join(', ');
      } else {
        debugPrint('[AUTH REPO] Error data unknown: $errorData');
        errorDetail = e.message ?? errorDetail;
      }
      throw Exception('Verification failed: $errorDetail');
    } catch (e) {
      throw Exception('Failed to verify OTP: $e');
    }
  }

  Future<Map<String, dynamic>> registerProfile(String name, String licenseNumber, String aadhaarNumber, int age) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/register', data: {
        'name': name,
        'license_number': licenseNumber,
        'aadhaar_number': aadhaarNumber,
        'age': age,
      });
      return response.data;
    } catch (e) {
      throw Exception('Failed to register profile: $e');
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/profile');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get profile: $e');
    }
  }

  Future<Map<String, dynamic>> getAssignedVehicle() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/vehicle');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get assigned vehicle: $e');
    }
  }

  Future<Map<String, dynamic>> uploadDocument(File file, String documentType) async {
    try {
      final formData = FormData.fromMap({
        'document_type': documentType,
        'file': await MultipartFile.fromFile(file.path),
      });

      final response = await _dio.post(
        '/api/v1/driver-app/upload-document',
        data: formData,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to upload $documentType: $e');
    }
  }

  Future<List<dynamic>> getDocuments() async {
    try {
      final response = await _dio.get('/api/v1/driver-app/documents');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get documents: $e');
    }
  }

  Future<Map<String, dynamic>> verifyFace() async {
    try {
      final response = await _dio.post(
        '/api/v1/driver-app/face-verify',
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to verify face: $e');
    }
  }
}
