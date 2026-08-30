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
  final Dio _dio;

  AuthRepository(this._dio);

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
      return response.data; // { "message": "OTP sent successfully", "demo_otp": "123456" }
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

  Future<Map<String, dynamic>> verifyOtp(String phoneNumber, String reqId, String otp, String inviteToken, [String? msg91Token]) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/verify-otp', data: {
        'phone_number': phoneNumber,
        'req_id': reqId,
        'otp_code': otp,
        'invite_token': inviteToken,
        if (msg91Token != null) 'msg91_token': msg91Token,
      });
      return response.data; 
    } on DioException catch (e) {
      final errorData = e.response?.data;
      debugPrint('[AUTH REPO] HTTP ${e.response?.statusCode}: ${e.response?.statusMessage}');
      debugPrint('[AUTH REPO] Endpoint: ${e.requestOptions.path}');
      debugPrint('[AUTH REPO] Request keys: ${e.requestOptions.data.keys.toList()}');
      if (errorData is Map) {
        debugPrint('[AUTH REPO] Error body: $errorData');
      } else {
        debugPrint('[AUTH REPO] Error data string: $errorData');
      }
      throw Exception('Verification failed: ${errorData?['detail'] ?? e.message}');
    } catch (e) {
      throw Exception('Failed to verify OTP: $e');
    }
  }

  Future<Map<String, dynamic>> registerProfile(String name, String licenseNumber, String aadhaarNumber) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/register', data: {
        'name': name,
        'license_number': licenseNumber,
        'aadhaar_number': aadhaarNumber,
      });
      return response.data;
    } catch (e) {
      throw Exception('Failed to register profile: $e');
    }
  }

  Future<Map<String, dynamic>> uploadDocument(File file, String documentType, int driverId) async {
    try {
      final formData = FormData.fromMap({
        'document_type': documentType,
        'driver_id': driverId,
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

  Future<Map<String, dynamic>> verifyFace(int driverId) async {
    try {
      final formData = FormData.fromMap({
        'driver_id': driverId,
      });

      final response = await _dio.post(
        '/api/v1/driver-app/face-verify',
        data: formData,
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to verify face: $e');
    }
  }
}
