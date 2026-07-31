import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../utils/logger.dart';

/// Provides reactive connectivity state across the app
final connectivityProvider = StreamProvider<bool>((ref) {
  return ConnectivityService().connectivityStream;
});

/// Current connectivity state (synchronous)
final isOnlineProvider = StateProvider<bool>((ref) => true);

class ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  final StreamController<bool> _controller = StreamController<bool>.broadcast();

  Stream<bool> get connectivityStream => _controller.stream;

  ConnectivityService() {
    _connectivity.onConnectivityChanged.listen((results) {
      final isOnline = results.any((r) => r != ConnectivityResult.none);
      _controller.add(isOnline);
      AppLogger.info('Connectivity changed: ${isOnline ? "ONLINE" : "OFFLINE"}');
    });
  }

  Future<bool> checkConnectivity() async {
    final results = await _connectivity.checkConnectivity();
    return results.any((r) => r != ConnectivityResult.none);
  }

  void dispose() {
    _controller.close();
  }
}
