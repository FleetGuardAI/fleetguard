import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../storage/secure_storage.dart';
import '../../router/app_router.dart';
import '../../network/api_client.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref);
});

class AuthService {
  final Ref _ref;

  AuthService(this._ref);

  Future<void> logout() async {
    // Notify Backend
    try {
      final token = await SecureStorage.getAccessToken();
      if (token != null) {
        await _ref.read(apiClientProvider).dio.post('/api/v1/auth/logout');
      }
    } catch (_) {}

    // Clear credentials
    await SecureStorage.clearAll();

    // Update state
    _ref.read(authStateProvider.notifier).state = false;
    
    // Router should automatically redirect based on authStateProvider change
  }
}
