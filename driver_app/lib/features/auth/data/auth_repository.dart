import 'dart:io';
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

  Future<Map<String, dynamic>> verifyOtp(String phoneNumber, String otp, String inviteToken) async {
    try {
      final response = await _dio.post('/api/v1/driver-app/verify-otp', data: {
        'phone_number': phoneNumber,
        'otp_code': otp,
        'invite_token': inviteToken,
      });
      return response.data; 
      // { "access_token": "...", "driver_id": 1, "is_new_driver": bool, "verification_status": "..." }
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
