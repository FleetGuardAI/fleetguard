import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/fleet/presentation/screens/fleet_screen.dart';
import '../../features/copilot/presentation/screens/copilot_screen.dart';
import '../../features/expense/presentation/screens/finance_screen.dart';
import '../../features/trip/presentation/screens/trips_screen.dart';
import '../../features/fleet/presentation/screens/add_driver_screen.dart';
import '../../features/fleet/presentation/screens/add_truck_screen.dart';
import '../../features/fleet/presentation/screens/invite_driver_screen.dart';
import '../../features/fleet/presentation/screens/add_hardware_asset_screen.dart';
import '../../features/tracking/presentation/screens/live_tracking_screen.dart';
import '../../features/navigation/presentation/screens/scaffold_with_nav_bar.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/splash_screen.dart';
import '../../features/more/presentation/screens/profile_screen.dart';
import '../../features/more/presentation/screens/settings_screen.dart';
import '../../features/notifications/presentation/screens/notifications_screen.dart';
import '../storage/secure_storage.dart';

final authStateProvider = StateProvider<bool>((ref) => false);

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;
  bool _initialized = false;
  bool _hasError = false;
  
  bool get initialized => _initialized;
  bool get hasError => _hasError;

  RouterNotifier(this._ref) {
    _ref.listen<bool>(authStateProvider, (_, __) {
      notifyListeners();
    });
    _init();
  }

  Future<void> retryInit() async {
    _hasError = false;
    notifyListeners();
    await _init();
  }

  Future<void> forceLogin() async {
    await SecureStorage.clearAuth();
    _ref.read(authStateProvider.notifier).state = false;
    _hasError = false;
    _initialized = true;
    notifyListeners();
  }

  Future<void> _init() async {
    debugPrint('[STARTUP] App initialization started');
    try {
      debugPrint('[STARTUP] Checking stored authentication');
      final token = await SecureStorage.getAccessToken();
      
      if (token == null || token.isEmpty) {
        debugPrint('[STARTUP] Token found: false');
        _ref.read(authStateProvider.notifier).state = false;
      } else {
        debugPrint('[STARTUP] Token found: true');
        debugPrint('[STARTUP] Validating session');
        
        try {
          // Read dio, but don't depend on interceptors since we inject token manually for this specific check
          final dio = _ref.read(apiClientProvider).dio;
          final response = await dio.get(
            '/api/v1/auth/me',
            options: Options(
              headers: {'Authorization': 'Bearer $token'},
            ),
          ).timeout(const Duration(seconds: 10));
          
          if (response.statusCode == 200) {
            debugPrint('[STARTUP] Session valid');
            _ref.read(authStateProvider.notifier).state = true;
          } else {
            debugPrint('[STARTUP] Session invalid (status: ${response.statusCode})');
            await SecureStorage.clearAuth();
            _ref.read(authStateProvider.notifier).state = false;
          }
        } on DioException catch (e) {
          if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
            debugPrint('[STARTUP] Session invalid (401/403)');
            await SecureStorage.clearAuth();
            _ref.read(authStateProvider.notifier).state = false;
          } else {
            debugPrint('[STARTUP] Backend unavailable: $e');
            _hasError = true;
            notifyListeners();
            return; // Stop initialization, wait for retry
          }
        } catch (e) {
          debugPrint('[STARTUP] Validation error: $e');
          _hasError = true;
          notifyListeners();
          return; // Stop initialization, wait for retry
        }
      }
      
      debugPrint('[STARTUP] Initialization completed');
      _hasError = false;
      _initialized = true;
    } catch (e) {
      debugPrint('[STARTUP] Fatal initialization error: $e');
      _hasError = true;
    } finally {
      if (!_hasError) {
        debugPrint('[STARTUP] Navigating to login/dashboard');
      }
      notifyListeners();
    }
  }
}

final routerNotifierProvider = Provider<RouterNotifier>((ref) {
  return RouterNotifier(ref);
});

final appRouterProvider = Provider<GoRouter>((ref) {
  final notifier = ref.watch(routerNotifierProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    refreshListenable: notifier,
    redirect: (context, state) {
      if (!notifier.initialized) {
        return '/splash';
      }

      final isLoggedIn = ref.read(authStateProvider);
      final isAuthRoute = state.matchedLocation == '/auth/qr-scan';
      final isSplashRoute = state.matchedLocation == '/splash';

      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/qr-scan';
      }
      if (isLoggedIn && (isAuthRoute || isSplashRoute)) {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/auth/qr-scan',
        builder: (context, state) => const LoginScreen(),
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
            path: '/trips',
            builder: (context, state) => const TripsScreen(),
          ),
          GoRoute(
            path: '/finance',
            builder: (context, state) => const FinanceScreen(),
          ),
          GoRoute(
            path: '/copilot',
            builder: (context, state) {
              final contextType = state.uri.queryParameters['contextType'];
              final contextId = state.uri.queryParameters['contextId'];
              final contextLabel = state.uri.queryParameters['contextLabel'];
              return CopilotScreen(
                contextType: contextType, 
                contextId: contextId,
                contextLabel: contextLabel,
              );
            },
          ),
        ],
      ),
      GoRoute(
        path: '/tracking',
        builder: (context, state) => const LiveTrackingScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),
    ],
  );
});
