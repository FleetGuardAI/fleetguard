import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../storage/secure_storage.dart';
import '../../features/auth/presentation/screens/qr_scan_screen.dart';
import '../../features/auth/presentation/screens/phone_verification_screen.dart';
import '../../features/auth/presentation/screens/profile_creation_screen.dart';
import '../../features/auth/presentation/screens/document_upload_screen.dart';
import '../../features/auth/presentation/screens/selfie_verification_screen.dart';
import '../../features/auth/presentation/screens/pending_approval_screen.dart';
import '../../features/auth/presentation/screens/welcome_fleet_screen.dart';
import '../../features/permissions/presentation/screens/permission_screen.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/trip/presentation/screens/trip_list_screen.dart';
import '../../features/trip/presentation/screens/trip_detail_screen.dart';
import '../../features/trip/presentation/screens/active_trip_screen.dart';
import '../../features/expense/presentation/screens/expense_list_screen.dart';
import '../../features/expense/presentation/screens/create_expense_screen.dart';
import '../../features/inspection/presentation/screens/inspection_screen.dart';
import '../../features/pod/presentation/screens/pod_screen.dart';
import '../../features/wallet/presentation/screens/wallet_screen.dart';
import '../../features/emergency/presentation/screens/emergency_screen.dart';
import '../../features/documents/presentation/screens/documents_screen.dart';
import '../../features/notifications/presentation/screens/notification_screen.dart';
import '../../features/vehicle/presentation/screens/vehicle_detail_screen.dart';

/// GoRouter configuration with auth-aware routing
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    debugLogDiagnostics: true,
    redirect: (context, state) async {
      // Splash handles redirect logic
      if (state.matchedLocation == '/splash') return null;

      final isLoggedIn = await SecureStorage.isLoggedIn();
      final isAuthRoute = state.matchedLocation.startsWith('/auth');

      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/qr-scan';
      }

      if (isLoggedIn && isAuthRoute) {
        final status = await SecureStorage.getVerificationStatus();
        switch (status) {
          case 'PENDING_DOCUMENTS':
            // Allow navigation within the onboarding flow
            if (state.matchedLocation == '/auth/profile' ||
                state.matchedLocation == '/auth/documents' ||
                state.matchedLocation == '/auth/selfie-verify' ||
                state.matchedLocation == '/auth/welcome') {
              return null;
            }
            return '/auth/profile';
          case 'PENDING_APPROVAL':
            if (state.matchedLocation == '/auth/pending-approval' ||
                state.matchedLocation == '/auth/welcome') {
              return null;
            }
            return '/auth/pending-approval';
          case 'APPROVED':
            return '/dashboard';
          default:
            return '/dashboard';
        }
      }

      return null;
    },
    routes: [
      // --- Splash ---
      GoRoute(
        path: '/splash',
        builder: (context, state) => const _SplashScreen(),
      ),

      // --- Auth Flow ---
      GoRoute(
        path: '/auth/qr-scan',
        builder: (context, state) => const QrScanScreen(),
      ),
      GoRoute(
        path: '/auth/phone-verify',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>?;
          return PhoneVerificationScreen(
            companyName: extra?['company_name'] ?? '',
            inviteToken: extra?['invite_token'] ?? '',
          );
        },
      ),
      GoRoute(
        path: '/auth/profile',
        builder: (context, state) => const ProfileCreationScreen(),
      ),
      GoRoute(
        path: '/auth/documents',
        builder: (context, state) => const DocumentUploadScreen(),
      ),
      GoRoute(
        path: '/auth/selfie-verify',
        builder: (context, state) => const SelfieVerificationScreen(),
      ),
      GoRoute(
        path: '/auth/welcome',
        builder: (context, state) => const WelcomeFleetScreen(),
      ),
      GoRoute(
        path: '/auth/pending-approval',
        builder: (context, state) => const PendingApprovalScreen(),
      ),

      // --- Permissions ---
      GoRoute(
        path: '/permissions',
        builder: (context, state) => const PermissionScreen(),
      ),

      // --- Main App (with bottom nav shell) ---
      ShellRoute(
        builder: (context, state, child) => _MainShell(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/trips',
            builder: (context, state) => const TripListScreen(),
          ),
          GoRoute(
            path: '/expenses',
            builder: (context, state) => const ExpenseListScreen(),
          ),
          GoRoute(
            path: '/wallet',
            builder: (context, state) => const WalletScreen(),
          ),
        ],
      ),

      // --- Detail Screens (outside shell) ---
      GoRoute(
        path: '/trip/:id',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return TripDetailScreen(tripId: id);
        },
      ),
      GoRoute(
        path: '/trip/:id/active',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return ActiveTripScreen(tripId: id);
        },
      ),
      GoRoute(
        path: '/expense/create',
        builder: (context, state) => const CreateExpenseScreen(),
      ),
      GoRoute(
        path: '/inspection',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>?;
          return InspectionScreen(
            type: extra?['type'] ?? 'PRE_TRIP',
          );
        },
      ),
      GoRoute(
        path: '/pod/:tripId',
        builder: (context, state) {
          final tripId = int.parse(state.pathParameters['tripId']!);
          return PodScreen(tripId: tripId);
        },
      ),
      GoRoute(
        path: '/vehicle',
        builder: (context, state) => const VehicleDetailScreen(),
      ),
      GoRoute(
        path: '/emergency',
        builder: (context, state) => const EmergencyScreen(),
      ),
      GoRoute(
        path: '/documents',
        builder: (context, state) => const DocumentsScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationScreen(),
      ),
    ],
  );
});

/// Main shell with bottom navigation
class _MainShell extends StatelessWidget {
  final Widget child;

  const _MainShell({required this.child});

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/trips')) return 1;
    if (location.startsWith('/expenses')) return 2;
    if (location.startsWith('/wallet')) return 3;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/dashboard');
        break;
      case 1:
        context.go('/trips');
        break;
      case 2:
        context.go('/expenses');
        break;
      case 3:
        context.go('/wallet');
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _calculateSelectedIndex(context),
        onDestinationSelected: (index) => _onItemTapped(index, context),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.route_outlined),
            selectedIcon: Icon(Icons.route),
            label: 'Trips',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_outlined),
            selectedIcon: Icon(Icons.receipt),
            label: 'Expenses',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: 'Wallet',
          ),
        ],
      ),
    );
  }
}

/// Splash screen — determines initial route based on auth state
class _SplashScreen extends StatefulWidget {
  const _SplashScreen();

  @override
  State<_SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<_SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigate();
  }

  Future<void> _navigate() async {
    await Future.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;

    final isLoggedIn = await SecureStorage.isLoggedIn();
    if (!isLoggedIn) {
      context.go('/auth/qr-scan');
      return;
    }

    final status = await SecureStorage.getVerificationStatus();
    switch (status) {
      case 'PENDING_DOCUMENTS':
        context.go('/auth/profile');
        return;
      case 'PENDING_APPROVAL':
        context.go('/auth/pending-approval');
        return;
      default:
        context.go('/dashboard');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.local_shipping,
              size: 80,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'FleetGuard',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Driver',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
