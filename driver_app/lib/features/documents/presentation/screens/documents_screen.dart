import 'package:flutter/material.dart';

class DocumentsScreen extends StatelessWidget {
  const DocumentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final docs = [
      {'title': 'Driving License', 'status': 'Verified', 'validity': 'Valid till 15 Aug 2028', 'icon': Icons.badge},
      {'title': 'Aadhaar Card', 'status': 'Verified', 'validity': 'Identity Verified', 'icon': Icons.fingerprint},
      {'title': 'Vehicle Registration (RC)', 'status': 'Valid', 'validity': 'MH-12-FG-2026', 'icon': Icons.directions_car},
      {'title': 'Insurance Policy', 'status': 'Valid', 'validity': 'Expires 24 Oct 2026', 'icon': Icons.security},
      {'title': 'PUC Certificate', 'status': 'Valid', 'validity': 'Expires 10 Sep 2026', 'icon': Icons.verified},
      {'title': 'National Permit', 'status': 'Valid', 'validity': 'All-India Transport Permit', 'icon': Icons.map},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('My Documents (Offline Ready)')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: docs.length,
        itemBuilder: (context, index) {
          final doc = docs[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: Icon(doc['icon'] as IconData, size: 36, color: Theme.of(context).colorScheme.primary),
              title: Text(doc['title'] as String, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(doc['validity'] as String),
              trailing: const Icon(Icons.offline_pin, color: Colors.green),
            ),
          );
        },
      ),
    );
  }
}
