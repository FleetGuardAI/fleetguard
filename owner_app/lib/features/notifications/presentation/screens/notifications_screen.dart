import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/api_client.dart';
import 'package:dio/dio.dart';

final notificationsProvider = FutureProvider<List<dynamic>>((ref) async {
  final dio = ref.watch(apiClientProvider).dio;
  try {
    final response = await dio.get('/api/v1/notifications/');
    return response.data as List<dynamic>;
  } on DioException catch (e) {
    if (e.response?.statusCode == 404) {
      return []; // Return empty if not found
    }
    throw e;
  }
});

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  
  Future<void> _markAsRead(int notificationId) async {
    final dio = ref.read(apiClientProvider).dio;
    try {
      await dio.put('/api/v1/notifications/$notificationId/read');
      ref.invalidate(notificationsProvider);
    } catch (e) {
      if (mounted) {
        String msg = 'Failed to mark as read';
        if (e is DioException) {
          msg = e.response?.data?['detail']?.toString() ?? msg;
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  Future<void> _markAllAsRead() async {
    final dio = ref.read(apiClientProvider).dio;
    try {
      await dio.put('/api/v1/notifications/read-all');
      ref.invalidate(notificationsProvider);
    } catch (e) {
      if (mounted) {
        String msg = 'Failed to mark all as read';
        if (e is DioException) {
          msg = e.response?.data?['detail']?.toString() ?? msg;
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final notificationsAsync = ref.watch(notificationsProvider);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Notifications', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        actions: [
          IconButton(
            icon: const Icon(Icons.done_all),
            onPressed: _markAllAsRead,
            tooltip: 'Mark all as read',
          ),
        ],
      ),
      body: notificationsAsync.when(
        data: (notifications) {
          if (notifications.isEmpty) {
            return Center(
              child: Text(
                'No new notifications',
                style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(notificationsProvider),
            child: ListView.separated(
              itemCount: notifications.length,
              separatorBuilder: (context, index) => Divider(
                color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                height: 1,
              ),
              itemBuilder: (context, index) {
                final notif = notifications[index];
                final isRead = notif['is_read'] == true;
                final dateStr = notif['created_at'];
                final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
                
                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  tileColor: isRead ? Colors.transparent : (isDark ? AppColors.primary.withValues(alpha: 0.1) : AppColors.primary.withValues(alpha: 0.05)),
                  leading: CircleAvatar(
                    backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                    child: Icon(
                      Icons.notifications,
                      color: isRead ? (isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant) : AppColors.primary,
                    ),
                  ),
                  title: Text(
                    notif['title'] ?? 'Notification',
                    style: TextStyle(
                      color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                      fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
                    ),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text(
                        notif['message'] ?? '',
                        style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        formattedDate,
                        style: TextStyle(fontSize: 12, color: (isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant).withValues(alpha: 0.7)),
                      ),
                    ],
                  ),
                  onTap: () {
                    if (!isRead) {
                      _markAsRead(notif['id']);
                    }
                  },
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) {
          String msg = 'Failed to load notifications';
          if (err is DioException) {
             msg = err.response?.data?['detail']?.toString() ?? msg;
          }
          return Center(child: Text(msg, style: TextStyle(color: AppColors.statusRed)));
        }
      ),
    );
  }
}
