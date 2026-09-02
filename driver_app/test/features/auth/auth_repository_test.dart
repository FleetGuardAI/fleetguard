import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:fleetguard_driver/features/auth/data/auth_repository.dart';

class MockDio extends Fake implements Dio {
  @override
  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  }) async {
    if (path == '/api/v1/driver-app/send-otp') {
      return Response(
        requestOptions: RequestOptions(path: path),
        data: {'message': 'OTP sent successfully', 'demo_otp': '123456'} as T,
      );
    }
    if (path == '/api/v1/driver-app/verify-otp') {
      return Response(
        requestOptions: RequestOptions(path: path),
        data: {'access_token': 'token', 'driver_id': 1} as T,
      );
    }
    if (path == '/api/v1/auth/resend-otp') {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        response: Response(
          requestOptions: RequestOptions(path: path),
          statusCode: 400,
          data: {'detail': 'Invalid request'},
        ),
      );
    }
    throw DioException(requestOptions: RequestOptions(path: path));
  }
}

void main() {
  group('AuthRepository', () {
    late AuthRepository authRepository;
    late MockDio mockDio;

    setUp(() {
      mockDio = MockDio();
      authRepository = AuthRepository(mockDio);
    });

    test('sendOtp returns expected data on success', () async {
      final result = await authRepository.sendOtp('9999999999');
      expect(result['message'], 'OTP sent successfully');
      expect(result['demo_otp'], '123456');
    });

    test('verifyOtp returns access token', () async {
      final result = await authRepository.verifyOtp('9999999999', 'req123', '123456', 'token123');
      expect(result['access_token'], 'token');
      expect(result['driver_id'], 1);
    });
    
    test('API Error handling - resendOtp throws exception', () async {
      expect(
        () => authRepository.resendOtp('req123'),
        throwsException,
      );
    });
  });
}
