import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/fleet/presentation/screens/fleet_screen.dart';
import '../../features/copilot/presentation/screens/copilot_screen.dart';
import '../../features/expense/presentation/screens/expense_screen.dart';
import '../../features/trip/presentation/screens/trips_screen.dart';
import '../../features/fleet/presentation/screens/add_driver_screen.dart';
import '../../features/fleet/presentation/screens/add_truck_screen.dart';
import '../../features/fleet/presentation/screens/invite_driver_screen.dart';
import '../../features/fleet/presentation/screens/add_hardware_asset_screen.dart';
import '../../features/navigation/presentation/screens/scaffold_with_nav_bar.dart';
import '../../features/auth/presentation/screens/qr_scan_screen.dart';
import '../../features/operations/presentation/screens/operations_screen.dart';
import '../../features/more/presentation/screens/more_screen.dart';
import '../storage/secure_storage.dart';

final authStateProvider = StateProvider<bool>((ref) => false);

final appRouterProvider = Provider<GoRouter>((ref) {
  // Setup simple async initialization for auth state
  Future.microtask(() async {
    final loggedIn = await SecureStorage.isLoggedIn();
    ref.read(authStateProvider.notifier).state = loggedIn;
  });

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final isLoggedIn = ref.read(authStateProvider);
      final isAuthRoute = state.matchedLocation == '/auth/qr-scan';

      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/qr-scan';
      }
      if (isLoggedIn && isAuthRoute) {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/auth/qr-scan',
        builder: (context, state) => const QRScanScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) {
          return ScaffoldWithNavBar(child: child);
        },
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/fleet',
            builder: (context, state) => const FleetScreen(),
          ),
          GoRoute(
            path: '/fleet/add-driver',
            builder: (context, state) => const AddDriverScreen(),
          ),
          GoRoute(
            path: '/fleet/invite-driver',
            builder: (context, state) => const InviteDriverScreen(),
          ),
          GoRoute(
            path: '/fleet/add-truck',
            builder: (context, state) => const AddTruckScreen(),
          ),
          GoRoute(
            path: '/fleet/add-device',
            builder: (context, state) => const AddHardwareAssetScreen(),
          ),
          GoRoute(
            path: '/operations',
            builder: (context, state) => const OperationsScreen(),
          ),
          GoRoute(
            path: '/more',
            builder: (context, state) => const MoreScreen(),
          ),
        ],
      ),
      GoRoute(
        path: '/copilot',
        builder: (context, state) => const CopilotScreen(),
      ),
      GoRoute(
        path: '/expense',
        builder: (context, state) => const ExpenseScreen(),
      ),
      GoRoute(
        path: '/trips',
        builder: (context, state) => const TripsScreen(),
      ),
    ],
  );
});
