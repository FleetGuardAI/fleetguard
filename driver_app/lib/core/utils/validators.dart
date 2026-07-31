/// Input validation utilities
class Validators {
  Validators._();

  /// Validate Indian phone number
  static String? phoneNumber(String? value) {
    if (value == null || value.isEmpty) {
      return 'Phone number is required';
    }
    // Remove spaces, dashes, and country code prefix
    final cleaned = value.replaceAll(RegExp(r'[\s\-]'), '');
    final withoutPrefix = cleaned.startsWith('+91') ? cleaned.substring(3) : cleaned;

    if (withoutPrefix.length != 10 || !RegExp(r'^[6-9]\d{9}$').hasMatch(withoutPrefix)) {
      return 'Enter a valid 10-digit mobile number';
    }
    return null;
  }

  /// Validate OTP
  static String? otp(String? value) {
    if (value == null || value.isEmpty) {
      return 'OTP is required';
    }
    if (value.length != 6 || !RegExp(r'^\d{6}$').hasMatch(value)) {
      return 'Enter a valid 6-digit OTP';
    }
    return null;
  }

  /// Validate name
  static String? name(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Name is required';
    }
    if (value.trim().length < 2) {
      return 'Name must be at least 2 characters';
    }
    return null;
  }

  /// Validate license number
  static String? licenseNumber(String? value) {
    if (value == null || value.isEmpty) {
      return 'License number is required';
    }
    if (value.length < 5) {
      return 'Enter a valid license number';
    }
    return null;
  }

  /// Validate amount
  static String? amount(String? value) {
    if (value == null || value.isEmpty) {
      return 'Amount is required';
    }
    final parsed = double.tryParse(value);
    if (parsed == null || parsed <= 0) {
      return 'Enter a valid amount';
    }
    return null;
  }

  /// Validate required field
  static String? required(String? value, [String fieldName = 'This field']) {
    if (value == null || value.trim().isEmpty) {
      return '$fieldName is required';
    }
    return null;
  }

  /// Format Indian phone number with +91 prefix
  static String formatPhoneNumber(String phone) {
    final cleaned = phone.replaceAll(RegExp(r'[\s\-]'), '');
    if (cleaned.startsWith('+91')) return cleaned;
    if (cleaned.startsWith('91') && cleaned.length == 12) return '+$cleaned';
    return '+91$cleaned';
  }
}
