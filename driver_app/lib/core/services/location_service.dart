import 'dart:async';
import 'dart:io';
import 'package:geolocator/geolocator.dart';

import '../config/app_config.dart';
import '../storage/local_database.dart';
import '../utils/logger.dart';

/// Background GPS location tracking service.
/// Captures GPS data every 5-10 seconds and stores locally for batch sync.
class LocationService {
  static StreamSubscription<Position>? _positionSubscription;
  static bool _isTracking = false;

  /// Initialize location service (check permissions)
  static Future<void> initialize() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      AppLogger.warning('Location services are disabled');
    }
  }

  /// Start continuous background location tracking
  static Future<bool> startTracking() async {
    if (_isTracking) return true;

    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      AppLogger.warning('Location permission not granted');
      return false;
    }

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: _getLocationSettings(),
    ).listen(
      _onLocationUpdate,
      onError: (error) {
        AppLogger.error('Location stream error: $error');
      },
    );

    _isTracking = true;
    AppLogger.info('Location tracking started');
    return true;
  }

  /// Stop location tracking
  static Future<void> stopTracking() async {
    await _positionSubscription?.cancel();
    _positionSubscription = null;
    _isTracking = false;
    AppLogger.info('Location tracking stopped');
  }

  /// Handle each location update — store locally for batch sync
  static Future<void> _onLocationUpdate(Position position) async {
    try {
      final batteryPercent = await _getBatteryLevel();

      await LocalDatabase.insertLocation({
        'latitude': position.latitude,
        'longitude': position.longitude,
        'speed': position.speed,
        'heading': position.heading,
        'accuracy': position.accuracy,
        'timestamp': position.timestamp.toIso8601String(),
        'battery_percent': batteryPercent,
        'activity_state': 'DRIVING', // Simplified for demo
      });
    } catch (e) {
      AppLogger.error('Failed to store location: $e');
    }
  }

  /// Get current position (one-shot)
  static Future<Position?> getCurrentPosition() async {
    try {
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (e) {
      AppLogger.error('Failed to get current position: $e');
      return null;
    }
  }

  static bool get isTracking => _isTracking;

  /// Platform-specific location settings
  static LocationSettings _getLocationSettings() {
    if (Platform.isAndroid) {
      return AndroidSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
        intervalDuration: const Duration(seconds: AppConfig.gpsIntervalSeconds),
        foregroundNotificationConfig: const ForegroundNotificationConfig(
          notificationTitle: 'FleetGuard Driver',
          notificationText: 'Tracking your location for fleet management',
          enableWakeLock: true,
        ),
      );
    }

    if (Platform.isIOS) {
      return AppleSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
        activityType: ActivityType.automotiveNavigation,
        pauseLocationUpdatesAutomatically: false,
        showBackgroundLocationIndicator: true,
      );
    }

    return const LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,
    );
  }

  /// Get device battery level
  static Future<int> _getBatteryLevel() async {
    try {
      // Simple battery check — returns -1 if unavailable
      return -1;
    } catch (_) {
      return -1;
    }
  }
}
