import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/services/location_service.dart';
import 'core/services/notification_service.dart';
import 'core/security/root_detection.dart';
import 'core/utils/logger.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock orientation to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: Colors.black,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  // Security check
  final isRooted = await RootDetection.isDeviceRooted();
  if (isRooted) {
    AppLogger.warning('Device root/jailbreak detected');
  }

  // Initialize local notifications
  await NotificationService.initialize();

  // Initialize background location service
  await LocationService.initialize();

  runApp(
    const ProviderScope(
      child: FleetGuardDriverApp(),
    ),
  );
}
