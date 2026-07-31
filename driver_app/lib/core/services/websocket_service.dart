import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/app_config.dart';
import '../storage/secure_storage.dart';
import '../utils/logger.dart';

/// WebSocket service with automatic reconnection.
/// Receives real-time updates: vehicle assignments, trip changes, notifications.
class WebSocketService {
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  bool _isConnected = false;
  bool _shouldReconnect = true;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 10;

  final StreamController<Map<String, dynamic>> _messageController =
      StreamController<Map<String, dynamic>>.broadcast();

  /// Stream of parsed WebSocket messages
  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  bool get isConnected => _isConnected;

  /// Connect to the driver WebSocket
  Future<void> connect() async {
    final driverId = await SecureStorage.getDriverId();
    final token = await SecureStorage.getAccessToken();

    if (driverId == null || token == null) {
      AppLogger.warning('Cannot connect WS: missing driver ID or token');
      return;
    }

    _shouldReconnect = true;
    _connect(driverId, token);
  }

  void _connect(int driverId, String token) {
    try {
      final uri = Uri.parse(
        '${AppConfig.wsBaseUrl}/api/v1/ws/driver/$driverId?token=$token',
      );

      _channel = WebSocketChannel.connect(uri);

      _channel!.stream.listen(
        (data) {
          _isConnected = true;
          _reconnectAttempts = 0;

          try {
            final message = jsonDecode(data as String) as Map<String, dynamic>;
            _messageController.add(message);
            AppLogger.debug('WS message: ${message['type']}');
          } catch (e) {
            AppLogger.error('WS parse error: $e');
          }
        },
        onDone: () {
          _isConnected = false;
          AppLogger.info('WebSocket disconnected');
          _scheduleReconnect(driverId, token);
        },
        onError: (error) {
          _isConnected = false;
          AppLogger.error('WebSocket error: $error');
          _scheduleReconnect(driverId, token);
        },
      );

      // Start ping timer to keep connection alive
      _pingTimer?.cancel();
      _pingTimer = Timer.periodic(
        const Duration(seconds: 30),
        (_) => _sendPing(),
      );

      AppLogger.info('WebSocket connected to driver $driverId');
    } catch (e) {
      AppLogger.error('WebSocket connection failed: $e');
      _scheduleReconnect(driverId, token);
    }
  }

  void _sendPing() {
    if (_isConnected && _channel != null) {
      try {
        _channel!.sink.add(jsonEncode({'type': 'ping'}));
      } catch (_) {}
    }
  }

  void _scheduleReconnect(int driverId, String token) {
    if (!_shouldReconnect || _reconnectAttempts >= _maxReconnectAttempts) return;

    _reconnectTimer?.cancel();
    _reconnectAttempts++;

    final delay = Duration(
      seconds: AppConfig.wsReconnectDelaySec * _reconnectAttempts,
    );

    AppLogger.info(
      'WS reconnecting in ${delay.inSeconds}s (attempt $_reconnectAttempts/$_maxReconnectAttempts)',
    );

    _reconnectTimer = Timer(delay, () => _connect(driverId, token));
  }

  /// Send a message through the WebSocket
  void send(Map<String, dynamic> message) {
    if (_isConnected && _channel != null) {
      _channel!.sink.add(jsonEncode(message));
    }
  }

  /// Disconnect and stop reconnection
  Future<void> disconnect() async {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    await _channel?.sink.close();
    _isConnected = false;
    AppLogger.info('WebSocket disconnected (manual)');
  }

  void dispose() {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _channel?.sink.close();
    _messageController.close();
  }
}
