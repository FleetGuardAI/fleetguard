import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../storage/local_database.dart';
import '../utils/logger.dart';

/// Local notification service — works without Firebase for demo.
/// Architecture is identical to production FCM integration.
class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static bool _initialized = false;

  /// Initialize notification channels and settings
  static Future<void> initialize() async {
    if (_initialized) return;

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _plugin.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Create Android notification channels
    await _createNotificationChannels();

    _initialized = true;
    AppLogger.info('Notification service initialized');
  }

  /// Show a local notification
  static Future<void> show({
    required String title,
    required String body,
    String? type,
    Map<String, dynamic>? data,
    String channelId = 'general',
  }) async {
    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          _channelName(channelId),
          importance: _channelImportance(channelId),
          priority: Priority.high,
          showWhen: true,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
      payload: type,
    );

    // Also store in local DB
    await LocalDatabase.insertNotification(
      title: title,
      body: body,
      type: type ?? 'general',
      data: data,
    );
  }

  /// Show trip-related notification
  static Future<void> showTripNotification({
    required String title,
    required String body,
    Map<String, dynamic>? data,
  }) async {
    await show(
      title: title,
      body: body,
      type: 'trip',
      data: data,
      channelId: 'trips',
    );
  }

  /// Show emergency notification
  static Future<void> showEmergencyNotification({
    required String title,
    required String body,
  }) async {
    await show(
      title: title,
      body: body,
      type: 'emergency',
      channelId: 'emergency',
    );
  }

  /// Show expense notification
  static Future<void> showExpenseNotification({
    required String title,
    required String body,
  }) async {
    await show(
      title: title,
      body: body,
      type: 'expense',
      channelId: 'expenses',
    );
  }

  static void _onNotificationTapped(NotificationResponse response) {
    AppLogger.info('Notification tapped: ${response.payload}');
    // Navigation is handled by the app router based on notification type
  }

  static Future<void> _createNotificationChannels() async {
    final androidPlugin =
        _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();

    if (androidPlugin == null) return;

    final channels = [
      const AndroidNotificationChannel(
        'general',
        'General',
        description: 'General notifications',
        importance: Importance.defaultImportance,
      ),
      const AndroidNotificationChannel(
        'trips',
        'Trip Updates',
        description: 'Trip assignment and status notifications',
        importance: Importance.high,
      ),
      const AndroidNotificationChannel(
        'emergency',
        'Emergency Alerts',
        description: 'SOS and emergency notifications',
        importance: Importance.max,
      ),
      const AndroidNotificationChannel(
        'expenses',
        'Expense Updates',
        description: 'Expense approval and rejection notifications',
        importance: Importance.defaultImportance,
      ),
      const AndroidNotificationChannel(
        'tracking',
        'Location Tracking',
        description: 'Background location tracking service',
        importance: Importance.low,
      ),
    ];

    for (final channel in channels) {
      await androidPlugin.createNotificationChannel(channel);
    }
  }

  static String _channelName(String channelId) {
    switch (channelId) {
      case 'trips':
        return 'Trip Updates';
      case 'emergency':
        return 'Emergency Alerts';
      case 'expenses':
        return 'Expense Updates';
      case 'tracking':
        return 'Location Tracking';
      default:
        return 'General';
    }
  }

  static Importance _channelImportance(String channelId) {
    switch (channelId) {
      case 'emergency':
        return Importance.max;
      case 'trips':
        return Importance.high;
      default:
        return Importance.defaultImportance;
    }
  }
}
