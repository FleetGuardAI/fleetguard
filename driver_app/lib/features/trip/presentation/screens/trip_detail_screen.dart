import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class TripDetailScreen extends StatelessWidget {
  final int tripId;

  const TripDetailScreen({super.key, required this.tripId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Trip #TRIP-$tripId')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Customer Information', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Icon(Icons.business, color: Colors.blue),
                      ],
                    ),
                    const Divider(height: 20),
                    const Text('Company: Acme Logistics Ltd', style: TextStyle(fontWeight: FontWeight.w600)),
                    const Text('Contact Person: Suresh Patel (+91 98765 43210)'),
                    const SizedBox(height: 8),
                    const Text('Instructions: Handle fragile electronics cargo with care. Call 15 mins prior to arrival.', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Route & Multi-Stops', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 12),
                    const ListTile(
                      leading: Icon(Icons.my_location, color: Colors.green),
                      title: Text('Pickup: JNPT Terminal 3'),
                      subtitle: Text('Scheduled: Today 08:00 AM'),
                    ),
                    const ListTile(
                      leading: Icon(Icons.local_gas_station, color: Colors.amber),
                      title: Text('Stop 1: Khopoli Fuel Plaza'),
                      subtitle: Text('Scheduled Fuel Fill Stop'),
                    ),
                    const ListTile(
                      leading: Icon(Icons.location_on, color: Colors.red),
                      title: Text('Delivery: Chakan Warehouse B'),
                      subtitle: Text('Scheduled: Today 04:30 PM'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => context.push('/trip/$tripId/active'),
                    icon: const Icon(Icons.navigation),
                    label: const Text('Start Navigation'),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: () => context.push('/pod/$tripId'),
                  icon: const Icon(Icons.assignment_turned_in),
                  label: const Text('Submit POD'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
