import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

class ApiClient {
  late final Dio dio;

  // Handles emulator vs iOS simulator localhost
  final String _baseUrl = Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

  ApiClient() {
    dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    // Add interceptor for basic logging
    dio.interceptors.add(LogInterceptor(responseBody: true, requestBody: true));
    dio.interceptors.add(OwnerMockInterceptor());
  }
}

class OwnerMockInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final path = err.requestOptions.path;
    dynamic mockData;

    if (path.contains('/vehicles') || path.contains('/trucks')) {
      mockData = [
        {'id': 1, 'license_plate': 'MH-12-AB-1234', 'make': 'Tata', 'model': 'Prima 5530.S', 'status': 'active', 'current_fuel_level': 65, 'location': 'Mumbai'},
        {'id': 2, 'license_plate': 'MH-14-CD-5678', 'make': 'Ashok Leyland', 'model': 'U-3518', 'status': 'maintenance', 'current_fuel_level': 20, 'location': 'Pune'},
      ];
    } else if (path.contains('/drivers')) {
      mockData = [
        {'id': 101, 'name': 'Ramesh Kumar', 'phone_number': '+91 9876543210', 'status': 'active', 'risk_score': 25, 'rating': 4.8},
        {'id': 102, 'name': 'Suresh Singh', 'phone_number': '+91 9876543211', 'status': 'inactive', 'risk_score': 45, 'rating': 4.2},
      ];
    } else if (path.contains('/trips')) {
      mockData = [
        {'id': 1001, 'trip_id': 'TRP-1001', 'origin_location': 'Mumbai', 'destination_location': 'Delhi', 'status': 'IN_PROGRESS', 'progress': 45, 'driver_name': 'Ramesh Kumar'},
        {'id': 1002, 'trip_id': 'TRP-1002', 'origin_location': 'Pune', 'destination_location': 'Bangalore', 'status': 'COMPLETED', 'progress': 100, 'driver_name': 'Suresh Singh'},
      ];
    } else if (path.contains('/dashboard') || path.contains('/stats')) {
      mockData = {'active_trips': 1, 'active_vehicles': 1, 'total_revenue': 45000, 'pending_alerts': 2};
    } else if (path.contains('/alerts')) {
      mockData = [
        {'id': 401, 'type': 'Fuel Theft', 'message': 'Sudden fuel drop on MH-12-AB-1234', 'severity': 'high'},
      ];
    } else {
      mockData = [];
    }

    if (err.type == DioExceptionType.connectionTimeout || err.type == DioExceptionType.connectionError || err.response == null) {
      // Fallback to mock data on network error
      return handler.resolve(Response(
        requestOptions: err.requestOptions,
        data: mockData,
        statusCode: 200,
      ));
    }
    
    handler.next(err);
  }
}
