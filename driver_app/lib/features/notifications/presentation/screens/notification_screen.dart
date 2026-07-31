import 'package:flutter/material.dart';

class NotificationScreen extends StatelessWidget {
  const NotificationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final notifications = [
      {'title': 'New Trip Assigned', 'body': 'Trip #TRIP-8492 assigned: JNPT to Pune Hub', 'time': '10 mins ago', 'type': 'trip'},
      {'title': 'Expense Approved', 'body': 'Fuel expense of ₹4,500 approved by dispatcher', 'time': '1 hour ago', 'type': 'expense'},
      {'title': 'Vehicle Assigned', 'body': 'Vehicle MH-12-FG-2026 assigned for your shift', 'time': '2 hours ago', 'type': 'vehicle'},
      {'title': 'Advance Approved', 'body': 'Salary advance of ₹5,000 approved and processed', 'time': 'Yesterday', 'type': 'wallet'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: notifications.length,
        itemBuilder: (context, index) {
          final notif = notifications[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: const Icon(Icons.notifications_active, color: Colors.blue),
              ),
              title: Text(notif['title']!, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text(notif['body']!),
                  const SizedBox(height: 4),
                  Text(notif['time']!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
