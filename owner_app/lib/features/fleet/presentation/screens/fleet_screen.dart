import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import 'package:go_router/go_router.dart';

class FleetScreen extends StatefulWidget {
  const FleetScreen({super.key});

  @override
  State<FleetScreen> createState() => _FleetScreenState();
}

class _FleetScreenState extends State<FleetScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(
        title: const Text('Fleet'),
        actions: [
          TextButton.icon(
            onPressed: () {
              if (_tabController.index == 0) {
                context.push('/fleet/add-truck');
              } else {
                context.push('/fleet/invite-driver'); // Using the QR Invite flow
              }
            },
            icon: const Icon(Icons.add, color: AppTheme.primaryGreen),
            label: const Text('Add', style: TextStyle(color: AppTheme.primaryGreen)),
          ),
          const SizedBox(width: 8),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryGreen,
          unselectedLabelColor: AppTheme.textSecondary,
          indicatorColor: AppTheme.primaryGreen,
          tabs: const [
            Tab(text: 'TRUCKS'),
            Tab(text: 'DRIVERS'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTrucksList(),
          _buildDriversList(),
        ],
      ),
    );
  }

  Widget _buildTrucksList() {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        _buildSearchBar('Search truck...'),
        const SizedBox(height: 16),
        _buildTruckCard('UK07AB1234', 'Ravi Kumar', 'On Trip', 'Healthy', AppTheme.primaryGreen),
        const SizedBox(height: 12),
        _buildTruckCard('UK07CD5678', 'Amit Singh', 'Available', 'Attention', AppTheme.warningAmber),
        const SizedBox(height: 12),
        _buildTruckCard('UK07EF9012', 'Suresh', 'Maintenance', 'Attention', AppTheme.criticalRed),
      ],
    );
  }

  Widget _buildDriversList() {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        _buildSearchBar('Search driver...'),
        const SizedBox(height: 16),
        _buildDriverCard('Ravi Kumar', 'UK07AB1234', 'Active', 'Good', AppTheme.primaryGreen),
        const SizedBox(height: 12),
        _buildDriverCard('Amit Singh', 'UK07CD5678', 'Active', 'License expiring', AppTheme.warningAmber),
      ],
    );
  }

  Widget _buildSearchBar(String hint) {
    return TextField(
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: const Icon(Icons.search, color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.cardLight,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(vertical: 0),
      ),
    );
  }

  Widget _buildTruckCard(String plate, String driver, String status, String health, Color healthColor) {
    return InkWell(
      onTap: () {},
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const Text('🚛', style: TextStyle(fontSize: 32)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(plate, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(driver, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(status, style: const TextStyle(fontWeight: FontWeight.w500)),
                Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: healthColor),
                    const SizedBox(width: 4),
                    Text(health, style: TextStyle(color: healthColor, fontSize: 12)),
                  ],
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildDriverCard(String name, String plate, String status, String health, Color healthColor) {
    return InkWell(
      onTap: () {},
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.cardLight,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const CircleAvatar(
              backgroundColor: AppTheme.backgroundCream,
              child: Icon(Icons.person, color: AppTheme.textSecondary),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(plate, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(status, style: const TextStyle(fontWeight: FontWeight.w500)),
                Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: healthColor),
                    const SizedBox(width: 4),
                    Text(health, style: TextStyle(color: healthColor, fontSize: 12)),
                  ],
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}
