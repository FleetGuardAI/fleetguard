import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../../core/services/permission_service.dart';

class PermissionScreen extends StatefulWidget {
  const PermissionScreen({super.key});

  @override
  State<PermissionScreen> createState() => _PermissionScreenState();
}

class _PermissionScreenState extends State<PermissionScreen> {
  final Map<Permission, bool> _statuses = {
    Permission.camera: false,
    Permission.notification: false,
    Permission.location: false,
    Permission.locationAlways: false,
    Permission.activityRecognition: false,
  };

  void _requestAll() async {
    final results = await PermissionService.requestAllPermissions();
    setState(() {
      results.forEach((permission, status) {
        _statuses[permission] = status.isGranted;
      });
    });

    if (mounted) {
      context.go('/dashboard');
    }
  }

  Widget _buildPermissionTile(Permission permission) {
    final info = PermissionService.permissionInfo[permission];
    if (info == null) return const SizedBox.shrink();

    final isGranted = _statuses[permission] ?? false;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Icon(info.icon, size: 36, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(info.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 4),
                  Text(info.description, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
            ),
            Icon(
              isGranted ? Icons.check_circle : Icons.radio_button_unchecked,
              color: isGranted ? Colors.green : Colors.grey,
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Required Permissions')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'App Permissions',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('FleetGuard requires the following permissions to provide live tracking, emergency alerts, and receipt OCR.'),
            const SizedBox(height: 20),
            Expanded(
              child: ListView(
                children: [
                  _buildPermissionTile(Permission.camera),
                  _buildPermissionTile(Permission.notification),
                  _buildPermissionTile(Permission.location),
                  _buildPermissionTile(Permission.locationAlways),
                  _buildPermissionTile(Permission.activityRecognition),
                ],
              ),
            ),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _requestAll,
                child: const Text('Grant All & Continue'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
