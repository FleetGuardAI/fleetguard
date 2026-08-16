import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class ScaffoldWithNavBar extends StatelessWidget {
  const ScaffoldWithNavBar({
    required this.child,
    super.key,
  });

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.local_shipping),
            label: 'Fleet',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.smart_toy),
            label: 'Copilot',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.receipt),
            label: 'Expense',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.route),
            label: 'Trips',
          ),
        ],
        currentIndex: _calculateSelectedIndex(context),
        onTap: (int idx) => _onItemTapped(idx, context),
      ),
    );
  }

  static int _calculateSelectedIndex(BuildContext context) {
    final String location = GoRouterState.of(context).uri.toString();
    if (location.startsWith('/dashboard')) {
      return 0;
    }
    if (location.startsWith('/fleet')) {
      return 1;
    }
    if (location.startsWith('/copilot')) {
      return 2;
    }
    if (location.startsWith('/expense')) {
      return 3;
    }
    if (location.startsWith('/trips')) {
      return 4;
    }
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        GoRouter.of(context).go('/dashboard');
        break;
      case 1:
        GoRouter.of(context).go('/fleet');
        break;
      case 2:
        GoRouter.of(context).go('/copilot');
        break;
      case 3:
        GoRouter.of(context).go('/expense');
        break;
      case 4:
        GoRouter.of(context).go('/trips');
        break;
    }
  }
}
