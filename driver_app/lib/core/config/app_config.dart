/// FleetGuard Driver App Configuration
///
/// Central configuration constants loaded from environment or compile-time flags.
/// For demo mode, defaults point to localhost backend.
class AppConfig {
  AppConfig._();

  /// Backend API base URL
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://fleetguard-hpip.onrender.com',
  );

  /// WebSocket URL
  static String get wsBaseUrl {
    final uri = Uri.parse(apiBaseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return '$scheme://${uri.host}:${uri.port}';
  }

  /// API version prefix
  static const String apiPrefix = '/api/v1';

  /// Driver app API prefix
  static const String driverApiPrefix = '/api/v1/driver-app';

  static const String msg91MobileWidgetId = String.fromEnvironment(
    'MSG91_MOBILE_WIDGET_ID',
  );

  static const String msg91MobileWidgetToken = String.fromEnvironment(
    'MSG91_MOBILE_WIDGET_TOKEN',
  );

  /// GPS tracking interval in seconds
  static const int gpsIntervalSeconds = 5;

  /// GPS batch upload size
  static const int gpsBatchSize = 20;

  /// Location sync interval in seconds
  static const int locationSyncIntervalSeconds = 30;

  /// WebSocket reconnect delay in seconds
  static const int wsReconnectDelaySec = 3;

  /// Maximum offline queue size
  static const int maxOfflineQueueSize = 1000;

  /// Image compression quality (0-100)
  static const int imageCompressionQuality = 75;

  /// Maximum image dimension in pixels
  static const int maxImageDimension = 1920;

  /// Token refresh threshold in minutes
  static const int tokenRefreshThresholdMinutes = 5;
}
