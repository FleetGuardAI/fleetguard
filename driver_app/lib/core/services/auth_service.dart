import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../storage/secure_storage.dart';
import '../routing/app_router.dart';
import '../../features/trip/data/tracking_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref);
});

class AuthService {
  final Ref _ref;

  AuthService(this._ref);

  Future<void> logout() async {
    // 1. Stop active tracking
    try {
      _ref.read(trackingServiceProvider).stopTracking();
    } catch (_) {}

    // 2. Clear credentials
    await SecureStorage.clearAll();

    // 3. Clear state (invalidate all providers would be ideal, but tracking is the most critical)
    _ref.invalidate(trackingServiceProvider);

    // 4. Force navigation to login
    _ref.read(appRouterProvider).go('/auth/qr-scan');
  }
}
