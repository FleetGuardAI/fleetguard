import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../storage/secure_storage.dart';
import '../router/app_router.dart';
import '../network/api_client.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref);
});

class UserProfile {
  final int id;
  final String fullName;
  final String role;
  final String? email;
  final String? phone;
  final String? companyId;
  
  UserProfile({
    required this.id, 
    required this.fullName, 
    required this.role,
    this.email,
    this.phone,
    this.companyId,
  });
  
  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['user']['id'],
      fullName: json['user']['full_name'] ?? 'Owner',
      role: json['user']['role'] ?? 'COMPANY_ADMIN',
      email: json['user']['email'],
      phone: json['user']['mobile_number'],
      companyId: json['user']['company_id']?.toString(),
    );
  }
}

final userProfileProvider = FutureProvider<UserProfile?>((ref) async {
  final isLoggedIn = ref.watch(authStateProvider);
  if (!isLoggedIn) return null;
  
  try {
    final response = await ref.read(apiClientProvider).dio.get('/api/v1/auth/me');
    return UserProfile.fromJson(response.data);
  } catch (e) {
    return null;
  }
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
