import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value storage for sensitive data (JWT tokens, credentials)
class SecureStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  // --- Keys ---
  static const _keyAccessToken = 'access_token';
  static const _keyRefreshToken = 'refresh_token';
  static const _keyUserId = 'user_id';
  static const _keyCompanyId = 'company_id';

  // --- Access Token ---
  static Future<void> setAccessToken(String token) async {
    try {
      await _storage.write(key: _keyAccessToken, value: token);
    } catch (e) {
      debugPrint('[SecureStorage] Error writing access token: $e');
    }
  }

  static Future<String?> getAccessToken() async {
    try {
      return await _storage.read(key: _keyAccessToken);
    } catch (e) {
      debugPrint('[SecureStorage] Error reading access token: $e');
      await clearAuth();
      return null;
    }
  }

  // --- Refresh Token ---
  static Future<void> setRefreshToken(String token) async {
    try {
      await _storage.write(key: _keyRefreshToken, value: token);
    } catch (e) {
      debugPrint('[SecureStorage] Error writing refresh token: $e');
    }
  }

  static Future<String?> getRefreshToken() async {
    try {
      return await _storage.read(key: _keyRefreshToken);
    } catch (e) {
      debugPrint('[SecureStorage] Error reading refresh token: $e');
      return null;
    }
  }

  // --- User ID ---
  static Future<void> setUserId(int id) async {
    try {
      await _storage.write(key: _keyUserId, value: id.toString());
    } catch (e) {
      debugPrint('[SecureStorage] Error writing user ID: $e');
    }
  }

  static Future<int?> getUserId() async {
    try {
      final val = await _storage.read(key: _keyUserId);
      return val != null ? int.tryParse(val) : null;
    } catch (e) {
      debugPrint('[SecureStorage] Error reading user ID: $e');
      return null;
    }
  }

  // --- Company ID ---
  static Future<void> setCompanyId(int id) async {
    try {
      await _storage.write(key: _keyCompanyId, value: id.toString());
    } catch (e) {
      debugPrint('[SecureStorage] Error writing company ID: $e');
    }
  }

  static Future<int?> getCompanyId() async {
    try {
      final val = await _storage.read(key: _keyCompanyId);
      return val != null ? int.tryParse(val) : null;
    } catch (e) {
      debugPrint('[SecureStorage] Error reading company ID: $e');
      return null;
    }
  }

  // --- Clear Auth ---
  static Future<void> clearAuth() async {
    debugPrint('[SecureStorage] Clearing authentication keys');
    try {
      await _storage.delete(key: _keyAccessToken);
      await _storage.delete(key: _keyRefreshToken);
      await _storage.delete(key: _keyUserId);
      await _storage.delete(key: _keyCompanyId);
    } catch (e) {
      debugPrint('[SecureStorage] Error clearing auth keys: $e');
    }
  }

  // --- Clear All ---
  static Future<void> clearAll() async {
    debugPrint('[SecureStorage] Clearing all secure storage');
    try {
      await _storage.deleteAll();
    } catch (e) {
      debugPrint('[SecureStorage] Error clearing all storage: $e');
    }
  }

  /// Check if user is logged in
  static Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }
}
