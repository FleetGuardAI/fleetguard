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
    rethrow;
  }
});

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  String _selectedFilter = 'ALL';

  Future<void> _markAsRead(int notificationId) async {
    final dio = ref.read(apiClientProvider).dio;
    try {
      await dio.put('/api/v1/notifications/$notificationId/read');
      ref.invalidate(notificationsProvider);
    } catch (e) {
      if (mounted) {
        String msg = 'Failed to mark as read';
        if (e is DioException) {
          msg = 'Failed to mark as read [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}';
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
          msg = 'Failed to mark all as read [${e.response?.statusCode}]: ${e.response?.data?['detail'] ?? e.message}';
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  Widget _buildFilterTabs() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final filters = ['ALL', 'ALERTS', 'TRIPS', 'FINANCE', 'SYSTEM'];
    return SizedBox(
      height: 56,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        itemCount: filters.length,
        itemBuilder: (context, index) {
          final filter = filters[index];
          final isSelected = _selectedFilter == filter;
          return Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: ChoiceChip(
              label: Text(filter),
              selected: isSelected,
              onSelected: (selected) {
                if (selected) {
                  setState(() => _selectedFilter = filter);
                }
              },
              selectedColor: AppColors.primary.withValues(alpha: 0.15),
              backgroundColor: isDark ? AppColors.darkCardBackground : Colors.white,
              labelStyle: TextStyle(
                color: isSelected ? AppColors.primary : (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
              side: BorderSide(
                color: isSelected ? AppColors.primary.withValues(alpha: 0.5) : (isDark ? AppColors.darkBorder : AppColors.lightBorder),
              ),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            ),
          );
        },
      ),
    );
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
        data: (allNotifications) {
          final notifications = _selectedFilter == 'ALL' 
              ? allNotifications 
              : allNotifications.where((n) {
                  final t = (n['type'] ?? 'SYSTEM').toString().toUpperCase();
                  if (_selectedFilter == 'ALERTS' && t == 'ALERT') return true;
                  if (_selectedFilter == 'TRIPS' && t == 'TRIP') return true;
                  if (_selectedFilter == 'FINANCE' && t == 'FINANCE') return true;
                  if (_selectedFilter == 'SYSTEM' && t == 'SYSTEM') return true;
                  return false;
                }).toList();

          if (notifications.isEmpty) {
            return Center(
              child: Text(
                'No new notifications',
                style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
              ),
            );
          }
          return Column(
            children: [
              _buildFilterTabs(),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () async => ref.invalidate(notificationsProvider),
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: notifications.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final notif = notifications[index];
                      final isRead = notif['is_read'] == true;
                      final dateStr = notif['created_at'];
                      final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                      final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
                      final type = (notif['type'] ?? 'SYSTEM').toString().toUpperCase();
                      
                      IconData icon = Icons.notifications;
                      Color iconColor = AppColors.primary;
                      Color bgColor = AppColors.lightMint;
                      
                      if (type == 'ALERT') {
                        icon = Icons.warning_rounded;
                        iconColor = AppColors.error;
                        bgColor = AppColors.error.withValues(alpha: 0.1);
                      } else if (type == 'TRIP') {
                        icon = Icons.route;
                        iconColor = AppColors.info;
                        bgColor = AppColors.info.withValues(alpha: 0.1);
                      } else if (type == 'FINANCE') {
                        icon = Icons.account_balance_wallet;
                        iconColor = AppColors.warning;
                        bgColor = AppColors.warning.withValues(alpha: 0.1);
                      }
                      
                      if (isDark && !isRead) {
                        bgColor = bgColor.withValues(alpha: 0.2);
                      } else if (isRead) {
                        bgColor = isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground;
                        iconColor = isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant;
                      }

                      return InkWell(
                        onTap: () {
                          if (!isRead) {
                            _markAsRead(notif['id']);
                          }
                        },
                        borderRadius: BorderRadius.circular(16),
                        child: Card(
                          margin: EdgeInsets.zero,
                          color: isRead 
                              ? (isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground)
                              : (isDark ? AppColors.primary.withValues(alpha: 0.05) : AppColors.lightMint.withValues(alpha: 0.3)),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(color: bgColor, shape: BoxShape.circle),
                                  child: Icon(icon, color: iconColor, size: 20),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        notif['title'] ?? 'Notification',
                                        style: TextStyle(
                                          color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface,
                                          fontWeight: isRead ? FontWeight.w500 : FontWeight.bold,
                                          fontSize: 15,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        notif['message'] ?? '',
                                        style: TextStyle(
                                          color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
                                          fontSize: 13,
                                          height: 1.4,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        formattedDate,
                                        style: TextStyle(fontSize: 11, color: isDark ? AppColors.darkOnSurfaceVariant.withValues(alpha: 0.7) : AppColors.lightOnSurfaceVariant.withValues(alpha: 0.7)),
                                      ),
                                    ],
                                  ),
                                ),
                                if (!isRead)
                                  Container(
                                    margin: const EdgeInsets.only(top: 4),
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle),
                                  )
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) {
          String msg = 'Failed to load notifications';
          if (err is DioException) {
             msg = 'Failed to load notifications [${err.response?.statusCode}]: ${err.response?.data?['detail'] ?? err.message}';
          }
          return Center(child: Text(msg, style: const TextStyle(color: AppColors.statusRed)));
        }
      ),
    );
  }
}
