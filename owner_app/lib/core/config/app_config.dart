import 'package:flutter/services.dart';

class AppConfig {
  static const MethodChannel _channel = MethodChannel('com.example.fleetguard_owner/config');
  static String? _geoapifyApiKey;

  static Future<void> initialize() async {
    try {
      _geoapifyApiKey = await _channel.invokeMethod('getGeoapifyKey');
    } on PlatformException catch (e) {
      print("Failed to get Geoapify Key: '${e.message}'.");
    }
  }

  static String get geoapifyApiKey => _geoapifyApiKey ?? '';
}
