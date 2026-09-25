import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../data/tracking_repository.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/config/app_config.dart';

final fleetLocationsProvider = StreamProvider.autoDispose<List<LiveDriverLocation>>((ref) async* {
  final repository = ref.watch(trackingRepositoryProvider);
  
  // Yield initial value via REST
  final initialLocations = await repository.getFleetLiveLocations();
  yield initialLocations;
  
  final token = await SecureStorage.getToken();
  final companyId = await SecureStorage.getCompanyId();
  if (token == null || companyId == null) return;
  
  // Convert http/https to ws/wss
  final wsUrl = AppConfig.baseUrl.replaceFirst('http', 'ws') + '/api/v1/ws/fleet/$companyId?token=$token';
  
  final channel = WebSocketChannel.connect(Uri.parse(wsUrl));
  
  ref.onDispose(() => channel.sink.close());
  
  // Keep local map to update on WS events
  final locationsMap = {for (var loc in initialLocations) loc.driverId: loc};
  
  await for (final message in channel.stream) {
    try {
      final data = json.decode(message);
      if (data['type'] == 'location_update') {
        final updatedLoc = LiveDriverLocation.fromJson(data);
        locationsMap[updatedLoc.driverId] = updatedLoc;
        yield locationsMap.values.toList();
      }
    } catch (_) {}
  }
});
