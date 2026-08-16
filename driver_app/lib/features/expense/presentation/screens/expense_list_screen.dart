import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/expense_provider.dart';

class ExpenseListScreen extends ConsumerWidget {
  const ExpenseListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expensesAsync = ref.watch(driverExpensesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Expenses')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/expense/create'),
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Add Expense'),
      ),
      body: expensesAsync.when(
        data: (expenses) {
          if (expenses.isEmpty) {
            return const Center(child: Text('No expenses recorded yet.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16.0),
            itemCount: expenses.length,
            itemBuilder: (context, index) {
              final exp = expenses[index];
              final dateStr = exp['expense_date'];
              final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
              final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
              
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
                  title: Text('${exp['category']} — ₹${exp['amount']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${exp['description']} • $formattedDate'),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: exp['status'] == 'APPROVED' ? Colors.green.withOpacity(0.15) : Colors.orange.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      exp['status'] ?? 'UNKNOWN',
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
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }
}
