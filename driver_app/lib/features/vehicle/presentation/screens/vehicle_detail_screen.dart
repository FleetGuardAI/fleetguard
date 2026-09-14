import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../dashboard/presentation/providers/dashboard_providers.dart';

class VehicleDetailScreen extends ConsumerWidget {
  const VehicleDetailScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final vehicleAsync = ref.watch(assignedVehicleProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Assigned Vehicle Details')),
      body: vehicleAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error loading vehicle: $err')),
        data: (vehicleData) {
          final registration = vehicleData['registration_number'] ?? 'Unknown Registration';
          final brand = vehicleData['brand'] ?? 'Unknown Brand';
          final model = vehicleData['model'] ?? 'Unknown Model';
          final vin = vehicleData['vin'] ?? 'Unknown VIN';
          final year = vehicleData['year'] ?? 'Unknown Year';

          return SingleChildScrollView(
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
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.local_shipping, size: 70, color: Colors.white),
                        const SizedBox(height: 8),
                        Text(registration, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 22)),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('$brand $model', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(height: 4),
                        Text('VIN: $vin • Year: $year'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Text('Compliance & Documents', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _buildComplianceRow('Insurance Policy', 'VALID', Colors.green),
            _buildComplianceRow('Fitness Certificate', 'VALID', Colors.green),
            _buildComplianceRow('PUC Certificate', 'VALID', Colors.green),
            _buildComplianceRow('National Permit', 'PERMIT ACTIVE', Colors.green),
            const SizedBox(height: 20),
            const Card(
              child: ListTile(
                leading: CircleAvatar(child: Icon(Icons.person)),
                title: Text('Assigned Dispatcher', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Fleet Manager\nContact via Support'),
              ),
            ),
          ],
        ),
      );
    }),
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
