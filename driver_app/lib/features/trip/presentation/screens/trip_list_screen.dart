import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class TripListScreen extends StatelessWidget {
  const TripListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final trips = [
      {
        'id': '8492',
        'trip_id': 'TRIP-8492',
        'status': 'IN_PROGRESS',
        'origin': 'JNPT Port, Navi Mumbai',
        'destination': 'Logistics Hub, Pune',
        'distance': '142.5 km',
        'eta': '45 mins',
      },
      {
        'id': '8491',
        'trip_id': 'TRIP-8491',
        'status': 'COMPLETED',
        'origin': 'Chakan Industrial Area, Pune',
        'destination': 'Bhiwandi Warehouse 4',
        'distance': '165.0 km',
        'eta': 'Completed',
      },
      {
        'id': '8490',
        'trip_id': 'TRIP-8490',
        'status': 'COMPLETED',
        'origin': 'Vashi APMC Market',
        'destination': 'Surat Textile Park',
        'distance': '280.0 km',
        'eta': 'Completed',
      },
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('My Trips')),
      body: ListView.builder(
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
                  Text(trip['trip_id']!, style: const TextStyle(fontWeight: FontWeight.bold)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: isInProgress ? Colors.blue.withOpacity(0.15) : Colors.green.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      trip['status']!,
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
                    Text('From: ${trip['origin']}'),
                    Text('To: ${trip['destination']}'),
                    const SizedBox(height: 4),
                    Text('Distance: ${trip['distance']} • ETA: ${trip['eta']}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  ],
                ),
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/trip/${trip['id']}'),
            ),
          );
        },
      ),
    );
  }
}
