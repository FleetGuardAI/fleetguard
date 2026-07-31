import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class ExpenseListScreen extends StatelessWidget {
  const ExpenseListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final expenses = [
      {'category': 'FUEL', 'amount': '₹4,500', 'date': 'Today, 02:30 PM', 'status': 'APPROVED', 'vendor': 'HPCL Pump Khopoli'},
      {'category': 'TOLL', 'amount': '₹320', 'date': 'Today, 11:15 AM', 'status': 'APPROVED', 'vendor': 'Mumbai-Pune Expressway'},
      {'category': 'PARKING', 'amount': '₹150', 'date': 'Yesterday', 'status': 'RECORDED', 'vendor': 'JNPT Parking Lot'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('My Expenses')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/expense/create'),
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Add Expense'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: expenses.length,
        itemBuilder: (context, index) {
          final exp = expenses[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: Icon(
                  exp['category'] == 'FUEL' ? Icons.local_gas_station : Icons.receipt,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              title: Text('${exp['category']} — ${exp['amount']}', style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('${exp['vendor']} • ${exp['date']}'),
              trailing: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: exp['status'] == 'APPROVED' ? Colors.green.withOpacity(0.15) : Colors.orange.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  exp['status']!,
                  style: TextStyle(
                    color: exp['status'] == 'APPROVED' ? Colors.green : Colors.orange,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
