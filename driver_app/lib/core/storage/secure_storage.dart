import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value storage for sensitive data (JWT tokens, credentials)
class SecureStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  // --- Keys ---
  static const _keyAccessToken = 'access_token';
  static const _keyDriverId = 'driver_id';
  static const _keyUserId = 'user_id';
  static const _keyCompanyId = 'company_id';
  static const _keyDriverName = 'driver_name';
  static const _keyPhoneNumber = 'phone_number';
  static const _keyVerificationStatus = 'verification_status';
  static const _keyDutyStatus = 'duty_status';
  static const _keyCompanyName = 'company_name';
  static const _keyInviteToken = 'invite_token';

  // --- Access Token ---
  static Future<void> setAccessToken(String token) async {
    await _storage.write(key: _keyAccessToken, value: token);
  }

  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _keyAccessToken);
  }

  // --- Driver ID ---
  static Future<void> setDriverId(int id) async {
    await _storage.write(key: _keyDriverId, value: id.toString());
  }

  static Future<int?> getDriverId() async {
    final val = await _storage.read(key: _keyDriverId);
    return val != null ? int.tryParse(val) : null;
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

  // --- Driver Name ---
  static Future<void> setDriverName(String name) async {
    await _storage.write(key: _keyDriverName, value: name);
  }

  static Future<String?> getDriverName() async {
    return await _storage.read(key: _keyDriverName);
  }

  // --- Phone Number ---
  static Future<void> setPhoneNumber(String phone) async {
    await _storage.write(key: _keyPhoneNumber, value: phone);
  }

  static Future<String?> getPhoneNumber() async {
    return await _storage.read(key: _keyPhoneNumber);
  }

  // --- Verification Status ---
  static Future<void> setVerificationStatus(String status) async {
    await _storage.write(key: _keyVerificationStatus, value: status);
  }

  static Future<String?> getVerificationStatus() async {
    return await _storage.read(key: _keyVerificationStatus);
  }

  // --- Duty Status ---
  static Future<void> setDutyStatus(String status) async {
    await _storage.write(key: _keyDutyStatus, value: status);
  }

  static Future<String?> getDutyStatus() async {
    return await _storage.read(key: _keyDutyStatus);
  }

  // --- Company Name ---
  static Future<void> setCompanyName(String name) async {
    await _storage.write(key: _keyCompanyName, value: name);
  }

  static Future<String?> getCompanyName() async {
    return await _storage.read(key: _keyCompanyName);
  }

  // --- Invite Token ---
  static Future<void> setInviteToken(String token) async {
    await _storage.write(key: _keyInviteToken, value: token);
  }

  static Future<String?> getInviteToken() async {
    return await _storage.read(key: _keyInviteToken);
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
