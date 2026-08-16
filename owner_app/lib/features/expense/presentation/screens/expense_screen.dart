import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../providers/expense_provider.dart';

class ExpenseScreen extends ConsumerWidget {
  const ExpenseScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expensesAsync = ref.watch(fleetExpensesProvider);
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(title: const Text('Fleet Expenses')),
      body: expensesAsync.when(
        data: (expenses) {
          double totalAmount = 0.0;
          double fuelAmount = 0.0;
          double maintenanceAmount = 0.0;
          double otherAmount = 0.0;

          for (var exp in expenses) {
            double amt = exp['amount']?.toDouble() ?? 0.0;
            totalAmount += amt;
            if (exp['category'] == 'FUEL') fuelAmount += amt;
            else if (exp['category'] == 'REPAIR' || exp['category'] == 'MAINTENANCE') maintenanceAmount += amt;
            else otherAmount += amt;
          }

          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              _buildTotalExpenseCard(
                currencyFormatter.format(totalAmount),
                currencyFormatter.format(fuelAmount),
                currencyFormatter.format(maintenanceAmount),
                currencyFormatter.format(otherAmount),
              ),
              const SizedBox(height: 24),
              const Text('Recent Expenses', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              if (expenses.isEmpty)
                const Center(child: Padding(padding: EdgeInsets.all(16), child: Text('No expenses recorded.'))),
              ...expenses.map((exp) {
                final dateStr = exp['expense_date'];
                final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12.0),
                  child: _buildExpenseItem(
                    '${exp['category']} — ${exp['description'] ?? 'Unknown'}',
                    currencyFormatter.format(exp['amount'] ?? 0),
                    exp['category'] == 'FUEL' ? Icons.local_gas_station : 
                    exp['category'] == 'REPAIR' ? Icons.build : Icons.receipt_long,
                    formattedDate,
                  ),
                );
              }),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error loading expenses: $err', style: const TextStyle(color: Colors.red))),
      ),
    );
  }

  Widget _buildTotalExpenseCard(String total, String fuel, String maintenance, String other) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.primaryGreen,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryGreen.withValues(alpha: 0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Total Fleet Expenses', style: TextStyle(color: Colors.white70, fontSize: 16)),
          const SizedBox(height: 8),
          Text(total, style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.bold)),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _BreakdownItem(label: 'Fuel', amount: fuel),
              _BreakdownItem(label: 'Maintenance', amount: maintenance),
              _BreakdownItem(label: 'Other', amount: other),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildExpenseItem(String title, String amount, IconData icon, String date) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardLight,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 5, offset: const Offset(0, 2)),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppTheme.backgroundCream,
            child: Icon(icon, color: AppTheme.primaryGreen),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(date, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ],
            ),
          ),
          Text(amount, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ],
      ),
    );
  }
}

class _BreakdownItem extends StatelessWidget {
  final String label;
  final String amount;

  const _BreakdownItem({required this.label, required this.amount});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
        const SizedBox(height: 4),
        Text(amount, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
      ],
    );
  }
}
