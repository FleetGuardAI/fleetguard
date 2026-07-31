import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';
import '../storage/secure_storage.dart';
import '../utils/logger.dart';
import 'api_endpoints.dart';

/// Centralized Dio HTTP client with interceptors for auth, logging, and error handling.
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref);
});

class ApiClient {
  final Ref _ref;
  late final Dio _dio;

  ApiClient(this._ref) {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        sendTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.addAll([
      _AuthInterceptor(_ref),
      _LoggingInterceptor(),
      _ErrorInterceptor(),
    ]);
  }

  Dio get dio => _dio;

  // --- Convenience Methods ---

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  /// Upload file with multipart form data
  Future<Response<T>> uploadFile<T>(
    String path, {
    required String filePath,
    required String fieldName,
    Map<String, dynamic>? extraFields,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
  }) async {
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(filePath),
      if (extraFields != null) ...extraFields,
    });

    return _dio.post<T>(
      path,
      data: formData,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
      ),
    );
  }
}

/// Attaches JWT Bearer token to every request
class _AuthInterceptor extends Interceptor {
  final Ref _ref;

  _AuthInterceptor(this._ref);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Skip auth for public endpoints
    final publicPaths = [
      ApiEndpoints.verifyInvite,
      ApiEndpoints.sendOtp,
      ApiEndpoints.verifyOtp,
    ];

    final isPublic = publicPaths.any((p) => options.path.contains(p));
    if (!isPublic) {
      final token = await SecureStorage.getAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token expired — clear storage and let auth guard redirect
      await SecureStorage.clearAll();
      AppLogger.warning('Auth token expired, cleared credentials');
    }
    handler.next(err);
  }
}

/// Logs HTTP requests and responses for debugging
class _LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    AppLogger.debug(
      'HTTP ${options.method} ${options.uri}',
    );
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    AppLogger.debug(
      'HTTP ${response.statusCode} ${response.requestOptions.uri}',
    );
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    AppLogger.error(
      'HTTP ERROR ${err.response?.statusCode} ${err.requestOptions.uri}: ${err.message}',
    );
    handler.next(err);
  }
}

/// Transforms Dio errors into user-friendly messages
class _ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        handler.next(DioException(
          requestOptions: err.requestOptions,
          error: 'Connection timed out. Please check your internet.',
          type: err.type,
          response: err.response,
        ));
        break;
      case DioExceptionType.connectionError:
        handler.next(DioException(
          requestOptions: err.requestOptions,
          error: 'No internet connection. Data will sync when online.',
          type: err.type,
          response: err.response,
        ));
        break;
      default:
        handler.next(err);
    }
  }
}

/// Extract error message from API response or DioException
String extractErrorMessage(dynamic error) {
  if (error is DioException) {
    if (error.response?.data is Map) {
      final data = error.response!.data as Map;
      return data['detail']?.toString() ?? error.message ?? 'An error occurred';
    }
    return error.message ?? 'An error occurred';
  }
  return error.toString();
}
