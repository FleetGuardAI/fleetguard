
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../storage/secure_storage.dart';

import '../router/app_router.dart';

import 'package:flutter/foundation.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref);
});

class ApiClient {
  late final Dio dio;
  
// Handles emulator vs iOS simulator localhost and production overrides
final String _baseUrl = const String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://fleetguard-hpip.onrender.com',
);

  final Ref ref;

  ApiClient(this.ref) {
    if (kReleaseMode && _baseUrl == 'http://127.0.0.1:8000') {
      throw Exception('CRITICAL: API_BASE_URL must be explicitly provided in release mode. Localhost fallback is prohibited in production.');
    }
    
    dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    dio.interceptors.add(LogInterceptor(responseBody: true, requestBody: true));
    dio.interceptors.add(_AuthInterceptor(ref, dio));
  }
}

class _AuthInterceptor extends Interceptor {
  final Ref ref;
  final Dio dio;
  bool _isRefreshing = false;

  _AuthInterceptor(this.ref, this.dio);
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await SecureStorage.getAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 || err.response?.statusCode == 403) {
      if (err.requestOptions.path.contains('/auth/refresh')) {
        await _logout();
        return handler.next(err);
      }

      if (_isRefreshing) {
        return handler.next(err);
      }

      _isRefreshing = true;
      try {
        final refreshToken = await SecureStorage.getRefreshToken();
        if (refreshToken == null || refreshToken.isEmpty) {
          await _logout();
          return handler.next(err);
        }

        final response = await Dio(BaseOptions(baseUrl: err.requestOptions.baseUrl)).post(
          '/api/v1/auth/refresh',
          data: {'refresh_token': refreshToken},
        );

        final newAccessToken = response.data['access_token'];
        final newRefreshToken = response.data['refresh_token'];
        
        await SecureStorage.setAccessToken(newAccessToken);
        if (newRefreshToken != null) {
          await SecureStorage.setRefreshToken(newRefreshToken);
        }

        // Retry the original request
        final options = err.requestOptions;
        options.headers['Authorization'] = 'Bearer $newAccessToken';
        final cloneReq = await dio.request(
          options.path,
          options: Options(
            method: options.method,
            headers: options.headers,
          ),
          data: options.data,
          queryParameters: options.queryParameters,
        );
        return handler.resolve(cloneReq);
      } catch (e) {
        await _logout();
      } finally {
        _isRefreshing = false;
      }
    }
    return handler.next(err);
  }

  Future<void> _logout() async {
    await SecureStorage.clearAuth();
    ref.read(authStateProvider.notifier).state = false;
  }
}
