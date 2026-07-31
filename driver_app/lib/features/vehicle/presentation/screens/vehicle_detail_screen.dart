import 'package:flutter/material.dart';

class VehicleDetailScreen extends StatelessWidget {
  const VehicleDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Assigned Vehicle Details')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Column(
                children: [
                  Container(
                    height: 160,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                    ),
                    child: const Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.local_shipping, size: 70, color: Colors.white),
                        SizedBox(height: 8),
                        Text('MH-12-FG-2026', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 22)),
                      ],
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Tata Prima 3530.K Heavy Commercial Truck', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        SizedBox(height: 4),
                        Text('VIN: MAT1234567890FG01 • Year: 2024'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Text('Compliance & Documents', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _buildComplianceRow('Insurance Policy', 'VALID until Oct 2026', Colors.green),
            _buildComplianceRow('Fitness Certificate', 'VALID until Dec 2026', Colors.green),
            _buildComplianceRow('PUC Certificate', 'VALID until Sep 2026', Colors.green),
            _buildComplianceRow('National Permit', 'PERMIT ACTIVE', Colors.green),
            _buildComplianceRow('Fuel Capacity', '400.0 Liters (Diesel)', Colors.blue),
            const SizedBox(height: 20),
            Card(
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.person)),
                title: const Text('Assigned Dispatcher', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: const Text('Rajesh Sharma • Fleet Ops HQ\nPhone: +91 98111 22233'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildComplianceRow(String label, String status, Color color) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(status),
        trailing: Icon(Icons.verified, color: color),
      ),
    );
  }
}
