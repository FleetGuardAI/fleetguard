import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/config/theme/app_theme.dart';
import 'core/routing/app_router.dart';

import 'features/auth/presentation/providers/auth_providers.dart';
import 'features/dashboard/presentation/providers/dashboard_providers.dart';
import 'features/trip/presentation/providers/trip_providers.dart';
import 'features/wallet/presentation/providers/wallet_provider.dart';
import 'features/expense/presentation/providers/expense_provider.dart';
import 'features/documents/presentation/providers/documents_provider.dart';
import 'features/notifications/data/notification_repository.dart';

class FleetGuardDriverApp extends ConsumerStatefulWidget {
  const FleetGuardDriverApp({super.key});

  @override
  ConsumerState<FleetGuardDriverApp> createState() => _FleetGuardDriverAppState();
}

class _FleetGuardDriverAppState extends ConsumerState<FleetGuardDriverApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // 1. Ensure Auth is still valid and synced
      ref.read(authServiceProvider).syncProfile();
      
      // 2. Invalidate data providers so they re-fetch
      ref.invalidate(driverProfileProvider);
      ref.invalidate(assignedVehicleProvider);
      ref.invalidate(todayTripsProvider);
      ref.invalidate(walletSummaryProvider);
      ref.invalidate(driverExpensesProvider);
      ref.invalidate(documentsProvider);
      ref.invalidate(notificationsProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'the vahan Driver',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      themeMode: ThemeMode.light,
      routerConfig: router,
    );
  }
}
