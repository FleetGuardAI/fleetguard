import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

class NotificationRepository {
  final ApiClient _apiClient;

  NotificationRepository(this._apiClient);

  Future<List<dynamic>> getNotifications() async {
    final response = await _apiClient.dio.get('/api/v1/notifications');
    return response.data;
  }

  Future<void> markAsRead(int notificationId) async {
    await _apiClient.dio.put('/api/v1/notifications/$notificationId/read');
  }

  Future<void> markAllAsRead() async {
    await _apiClient.dio.put('/api/v1/notifications/read-all');
  }
}

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return NotificationRepository(apiClient);
});

final notificationsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final repository = ref.watch(notificationRepositoryProvider);
  return repository.getNotifications();
});

final unreadNotificationsCountProvider = FutureProvider.autoDispose<int>((ref) async {
  final notifications = await ref.watch(notificationsProvider.future);
  return notifications.where((n) => n['is_read'] == false).length;
});
