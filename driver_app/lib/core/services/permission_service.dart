import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../utils/logger.dart';

/// Handles all permission requests with clear explanations
class PermissionService {
  /// Permission metadata with explanations
  static const Map<Permission, PermissionInfo> permissionInfo = {
    Permission.camera: PermissionInfo(
      title: 'Camera Access',
      description: 'Required to scan QR codes, capture receipts, take inspection photos, and verify your identity.',
      icon: Icons.camera_alt,
    ),
    Permission.notification: PermissionInfo(
      title: 'Notifications',
      description: 'Stay informed about trip assignments, expense approvals, emergency alerts, and messages from your dispatcher.',
      icon: Icons.notifications,
    ),
    Permission.location: PermissionInfo(
      title: 'Location (While Using)',
      description: 'Required to track your position during trips, calculate ETAs, and navigate to destinations.',
      icon: Icons.location_on,
    ),
    Permission.locationAlways: PermissionInfo(
      title: 'Location (Always)',
      description: 'Enables continuous tracking while on duty, even when the app is minimized. This ensures accurate trip records and fleet visibility.',
      icon: Icons.share_location,
    ),
    Permission.activityRecognition: PermissionInfo(
      title: 'Activity Recognition',
      description: 'Detects whether you are driving, walking, or stationary. Helps optimize GPS tracking and detect trip events automatically.',
      icon: Icons.directions_walk,
    ),
  };

  /// Request a single permission with explanation
  static Future<PermissionStatus> requestPermission(Permission permission) async {
    final status = await permission.status;

    if (status.isGranted) return status;

    if (status.isDenied) {
      final result = await permission.request();
      AppLogger.info('Permission ${permission.toString()}: ${result.name}');
      return result;
    }

    if (status.isPermanentlyDenied) {
      AppLogger.warning('Permission ${permission.toString()} permanently denied');
    }

    return status;
  }

  /// Request all required permissions in sequence
  static Future<Map<Permission, PermissionStatus>> requestAllPermissions() async {
    final results = <Permission, PermissionStatus>{};

    // Order matters — request in this sequence
    final permissions = [
      Permission.camera,
      Permission.notification,
      Permission.location,
      Permission.locationAlways,
      Permission.activityRecognition,
    ];

    for (final permission in permissions) {
      results[permission] = await requestPermission(permission);
    }

    return results;
  }

  /// Check if all critical permissions are granted
  static Future<bool> areAllCriticalPermissionsGranted() async {
    final camera = await Permission.camera.isGranted;
    final location = await Permission.location.isGranted;
    return camera && location;
  }

  /// Check if background location is granted
  static Future<bool> isBackgroundLocationGranted() async {
    return await Permission.locationAlways.isGranted;
  }

  /// Open app settings for permanently denied permissions
  static Future<bool> openSettings() async {
    return await openAppSettings();
  }
}

/// Metadata for permission explanation UI
class PermissionInfo {
  final String title;
  final String description;
  final IconData icon;

  const PermissionInfo({
    required this.title,
    required this.description,
    required this.icon,
  });
}
