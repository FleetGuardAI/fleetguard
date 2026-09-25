import 'dart:async';
import 'dart:io';
import 'dart:ui';
import 'package:flutter/widgets.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_background_service_android/flutter_background_service_android.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:geolocator/geolocator.dart';

import '../config/app_config.dart';
import '../storage/local_database.dart';
import '../utils/logger.dart';

import 'package:activity_recognition_flutter/activity_recognition_flutter.dart';
import 'package:dio/dio.dart';
import '../storage/secure_storage.dart';

@pragma('vm:entry-point')
void onStart(ServiceInstance service) async {
  DartPluginRegistrant.ensureInitialized();
  WidgetsFlutterBinding.ensureInitialized();

  if (service is AndroidServiceInstance) {
    service.on('setAsForeground').listen((event) {
      service.setAsForegroundService();
    });
    service.on('setAsBackground').listen((event) {
      service.setAsBackgroundService();
    });
  }

  service.on('stopService').listen((event) {
    service.stopSelf();
  });

  LocationSettings locationSettings;
  if (Platform.isAndroid) {
    locationSettings = AndroidSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,
      intervalDuration: const Duration(seconds: AppConfig.gpsIntervalSeconds),
      foregroundNotificationConfig: const ForegroundNotificationConfig(
        notificationTitle: 'the vahan Driver',
        notificationText: 'Tracking your location for fleet management',
        enableWakeLock: true,
      ),
    );
  } else if (Platform.isIOS) {
    locationSettings = AppleSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,
      activityType: ActivityType.automotiveNavigation,
      pauseLocationUpdatesAutomatically: false,
      showBackgroundLocationIndicator: true,
    );
  } else {
    locationSettings = const LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,
    );
  }

  StreamSubscription<Position>? positionStream;
  
  void startLocationStream() {
    if (positionStream != null && !positionStream!.isPaused) return;
    
    if (positionStream != null && positionStream!.isPaused) {
      positionStream!.resume();
      return;
    }

    positionStream = Geolocator.getPositionStream(locationSettings: locationSettings).listen((Position position) async {
      try {
        if (service is AndroidServiceInstance) {
          service.setForegroundNotificationInfo(
            title: "the vahan Driver",
            content: "Tracking location: ${position.latitude.toStringAsFixed(4)}, ${position.longitude.toStringAsFixed(4)}",
          );
        }
        
        await LocalDatabase.insertLocation({
          'latitude': position.latitude,
          'longitude': position.longitude,
          'speed': position.speed,
          'heading': position.heading,
          'accuracy': position.accuracy,
          'timestamp': position.timestamp.toIso8601String(),
          'battery_percent': -1,
          'activity_state': 'ACTIVE',
        });
        
        service.invoke('update', {
          "latitude": position.latitude,
          "longitude": position.longitude,
        });
      } catch (e) {
        print('Failed to store location in background: $e');
      }
    });
  }

  void stopLocationStream() {
    positionStream?.pause();
    if (service is AndroidServiceInstance) {
      service.setForegroundNotificationInfo(
        title: "the vahan Driver (Paused)",
        content: "Vehicle stationary. Battery saving mode active.",
      );
    }
  }

  // Initial start
  startLocationStream();

  // Smart Polling based on Activity
  final activityRecognition = ActivityRecognition.activityStream(runForegroundService: true);
  activityRecognition.listen((Activity activity) {
    if (activity.type == ActivityType.STILL) {
      stopLocationStream();
    } else if (activity.type == ActivityType.IN_VEHICLE || 
               activity.type == ActivityType.ON_BICYCLE || 
               activity.type == ActivityType.ON_FOOT || 
               activity.type == ActivityType.WALKING || 
               activity.type == ActivityType.RUNNING) {
      startLocationStream();
    }
  });

  // Background network sync
  Timer.periodic(const Duration(seconds: AppConfig.locationSyncIntervalSeconds), (_) async {
    try {
      final locations = await LocalDatabase.getUnSyncedLocations(limit: AppConfig.gpsBatchSize);
      if (locations.isEmpty) return;

      final token = await SecureStorage.getAccessToken();
      if (token == null) return;

      final dio = Dio(BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
      ));

      final response = await dio.post(
        '/api/v1/driver-app/location/batch',
        data: {
          'locations': locations.map((l) => {
            'latitude': l['latitude'],
            'longitude': l['longitude'],
            'speed': l['speed'],
            'heading': l['heading'],
            'accuracy': l['accuracy'],
            'timestamp': l['timestamp'],
            'battery_percent': l['battery_percent'],
            'activity_state': l['activity_state'],
          }).toList(),
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final ids = locations.map((l) => l['id'] as int).toList();
        await LocalDatabase.markLocationsSynced(ids);
      }
    } catch (e) {
      print('Background sync failed: $e');
    }
  });
}

/// Background GPS location tracking service.
class LocationService {
  static final _service = FlutterBackgroundService();
  static bool _isTracking = false;

  /// Initialize location service (check permissions)
  static Future<void> initialize() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      AppLogger.warning('Location services are disabled');
    }

    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'location_service',
      'Location Tracking',
      description: 'Used for background location tracking',
      importance: Importance.high,
    );

    final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();
    if (Platform.isAndroid) {
      await flutterLocalNotificationsPlugin
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(channel);
    }

    await _service.configure(
      androidConfiguration: AndroidConfiguration(
        onStart: onStart,
        autoStart: false,
        isForegroundMode: true,
        notificationChannelId: 'location_service',
        initialNotificationTitle: 'the vahan Driver',
        initialNotificationContent: 'Initializing Tracking',
        foregroundServiceNotificationId: 888,
      ),
      iosConfiguration: IosConfiguration(
        autoStart: false,
        onForeground: onStart,
        onBackground: onIosBackground,
      ),
    );
  }

  @pragma('vm:entry-point')
  static Future<bool> onIosBackground(ServiceInstance service) async {
    WidgetsFlutterBinding.ensureInitialized();
    DartPluginRegistrant.ensureInitialized();
    return true;
  }

  /// Start continuous background location tracking
  static Future<bool> startTracking() async {
    if (await _service.isRunning()) return true;

    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      AppLogger.warning('Location permission not granted');
      return false;
    }

    await _service.startService();
    _isTracking = true;
    AppLogger.info('Location tracking started in background');
    return true;
  }

  /// Stop location tracking
  static Future<void> stopTracking() async {
    _service.invoke("stopService");
    _isTracking = false;
    AppLogger.info('Location tracking stopped');
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
}
