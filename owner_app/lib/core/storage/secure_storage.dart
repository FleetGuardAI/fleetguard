import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value storage for sensitive data (JWT tokens, credentials)
class SecureStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  // --- Keys ---
  static const _keyAccessToken = 'access_token';
  static const _keyUserId = 'user_id';
  static const _keyCompanyId = 'company_id';

  // --- Access Token ---
  static Future<void> setAccessToken(String token) async {
    await _storage.write(key: _keyAccessToken, value: token);
  }

  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _keyAccessToken);
  }

  // --- User ID ---
  static Future<void> setUserId(int id) async {
    await _storage.write(key: _keyUserId, value: id.toString());
  }

  static Future<int?> getUserId() async {
    final val = await _storage.read(key: _keyUserId);
    return val != null ? int.tryParse(val) : null;
  }

  // --- Company ID ---
  static Future<void> setCompanyId(int id) async {
    await _storage.write(key: _keyCompanyId, value: id.toString());
  }

  static Future<int?> getCompanyId() async {
    final val = await _storage.read(key: _keyCompanyId);
    return val != null ? int.tryParse(val) : null;
  }

  // --- Clear All ---
  static Future<void> clearAll() async {
    await _storage.deleteAll();
  }

  /// Check if user is logged in
  static Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }
}
