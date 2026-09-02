import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../storage/secure_storage.dart';
import '../storage/local_database.dart';
import '../network/api_client.dart';
import '../routing/app_router.dart';
import '../../features/trip/data/tracking_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref);
});

class AuthService {

  AuthService(this._ref);
  final Ref _ref;

  Future<void> logout() async {
    // 1. Notify Backend
    try {
      final token = await SecureStorage.getAccessToken();
      if (token != null) {
        await _ref.read(apiClientProvider).post('/api/v1/auth/logout');
      }
    } catch (_) {
      // Ignore if network is down
    }

    // 2. Stop active tracking
    try {
      _ref.read(trackingServiceProvider).stopTracking();
    } catch (_) {}

    // 3. Clear SQLite database (Private Fleet Data)
    try {
      await LocalDatabase.clearAll();
    } catch (_) {}

    // 4. Clear credentials
    await SecureStorage.clearAll();

    // 5. Clear state (invalidate all providers would be ideal, but tracking is the most critical)
    _ref.invalidate(trackingServiceProvider);

    // 6. Force navigation to login
    _ref.read(appRouterProvider).go('/auth/qr-scan');
  }
}
