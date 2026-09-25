import '../utils/logger.dart';
import 'package:flutter_jailbreak_detection_plus/flutter_jailbreak_detection_plus.dart';

/// Root/Jailbreak detection for security hardening
class RootDetection {
  /// Check if device is rooted (Android) or jailbroken (iOS)
  static Future<bool> isDeviceRooted() async {
    try {
      final bool jailbroken = await FlutterJailbreakDetection.jailbroken;
      final bool developerMode = await FlutterJailbreakDetection.developerMode;
      
      if (jailbroken || developerMode) {
        AppLogger.warning('SECURITY RISK: Root/Jailbreak or Developer Mode detected!');
        return true;
      }
      
      AppLogger.info('Root detection check completed: SAFE');
      return false;
    } catch (e) {
      AppLogger.error('Root detection failed: $e');
      return false;
    }
  }
}
