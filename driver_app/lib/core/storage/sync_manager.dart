import 'dart:async';
import 'dart:convert';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../network/api_client.dart';
import '../utils/logger.dart';
import 'local_database.dart';

/// Manages offline-to-online data synchronization.
/// Watches connectivity and automatically syncs pending items when online.
class SyncManager {
  final ApiClient _apiClient;
  Timer? _syncTimer;
  bool _isSyncing = false;
  final Connectivity _connectivity = Connectivity();

  SyncManager(this._apiClient) {
    _connectivity.onConnectivityChanged.listen((dynamic results) {
      final isOnline = results is List
          ? results.any((r) => r != ConnectivityResult.none)
          : results != ConnectivityResult.none;
      if (isOnline) {
        AppLogger.info('Back online — triggering sync');
        syncAll();
      }
    });
  }

  /// Start periodic sync timer
  void startPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(
      Duration(seconds: AppConfig.locationSyncIntervalSeconds),
      (_) => syncAll(),
    );
    AppLogger.info('Periodic sync started (every ${AppConfig.locationSyncIntervalSeconds}s)');
  }

  /// Stop periodic sync
  void stopPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }

  /// Sync all pending data
  Future<void> syncAll() async {
    if (_isSyncing) return;
    _isSyncing = true;

    try {
      await _syncLocations();
      await _syncQueuedItems();
    } catch (e) {
      AppLogger.error('Sync error: $e');
    } finally {
      _isSyncing = false;
    }
  }

  /// Sync buffered GPS locations
  Future<void> _syncLocations() async {
    final locations = await LocalDatabase.getUnSyncedLocations(
      limit: AppConfig.gpsBatchSize,
    );

    if (locations.isEmpty) return;

    try {
      final response = await _apiClient.post(
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
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final ids = locations.map((l) => l['id'] as int).toList();
        await LocalDatabase.markLocationsSynced(ids);
        AppLogger.debug('Synced ${ids.length} locations');
      }
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError) {
        AppLogger.debug('Offline — locations queued for later');
      } else {
        AppLogger.error('Location sync failed: ${e.message}');
      }
    }
  }

  /// Process generic sync queue items (expenses, inspections, etc.)
  Future<void> _syncQueuedItems() async {
    final items = await LocalDatabase.getPendingSyncItems();
    if (items.isEmpty) return;

    for (final item in items) {
      try {
        final payload = jsonDecode(item['payload'] as String) as Map<String, dynamic>;
        final action = item['action'] as String;
        final endpoint = item['endpoint'] as String;

        Response response;
        switch (action) {
          case 'POST':
            response = await _apiClient.post(endpoint, data: payload);
            break;
          case 'PUT':
            response = await _apiClient.put(endpoint, data: payload);
            break;
          case 'PATCH':
            response = await _apiClient.patch(endpoint, data: payload);
            break;
          default:
            response = await _apiClient.post(endpoint, data: payload);
        }

        if (response.statusCode == 200 || response.statusCode == 201) {
          await LocalDatabase.markSyncItemCompleted(item['id'] as int);
          AppLogger.debug('Synced ${item['entity_type']} item #${item['id']}');
        }
      } on DioException catch (e) {
        if (e.type == DioExceptionType.connectionError) {
          break; // Stop trying if offline
        }
        await LocalDatabase.markSyncItemFailed(
          item['id'] as int,
          e.message ?? 'Unknown error',
        );
      }
    }
  }

  void dispose() {
    _syncTimer?.cancel();
  }
}
