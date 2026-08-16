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
import '../../features/navigation/presentation/screens/scaffold_with_nav_bar.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/dashboard',
    routes: [
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
      ),
    ],
  );
});
