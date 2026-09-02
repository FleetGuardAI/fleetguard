import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../dashboard/presentation/providers/dashboard_providers.dart';

class TripListScreen extends ConsumerWidget {
  const TripListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripsAsync = ref.watch(todayTripsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Trips')),
      body: tripsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
        data: (trips) {
          if (trips.isEmpty) {
            return const Center(child: Text('No trips found.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16.0),
            itemCount: trips.length,
            itemBuilder: (context, index) {
              final trip = trips[index];
              final isInProgress = trip['status'] == 'IN_PROGRESS';

              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(trip['trip_id'] ?? 'Unknown', style: const TextStyle(fontWeight: FontWeight.bold)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: isInProgress ? Colors.blue.withOpacity(0.15) : Colors.green.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          trip['status'] ?? 'UNKNOWN',
                          style: TextStyle(
                            color: isInProgress ? Colors.blue : Colors.green,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 8.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('From: ${trip['origin_location']}'),
                        Text('To: ${trip['destination_location']}'),
                        const SizedBox(height: 4),
                        Text('Distance: ${trip['planned_distance'] ?? 0} km', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      ],
                    ),
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/trip/${trip['id']}'),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
