import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/wallet_provider.dart';
import '../../data/wallet_repository.dart';

class WalletScreen extends ConsumerWidget {
  const WalletScreen({super.key});

  void _showAdvanceDialog(BuildContext context, WidgetRef ref) {
    final amountController = TextEditingController();
    final reasonController = TextEditingController();
    bool isSubmitting = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: const Text('Request Salary Advance'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Enter advance amount requested for approval from fleet manager:'),
                const SizedBox(height: 12),
                TextField(
                  controller: amountController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Amount (₹)', prefixIcon: Icon(Icons.currency_rupee)),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: reasonController,
                  decoration: const InputDecoration(labelText: 'Reason (Optional)'),
                ),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                onPressed: isSubmitting
                    ? null
                    : () async {
                        final amountText = amountController.text;
                        final amount = double.tryParse(amountText);
                        if (amount == null || amount <= 0) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Please enter a valid amount')),
                          );
                          return;
                        }

                        setState(() {
                          isSubmitting = true;
                        });

                        try {
                          await ref.read(walletRepositoryProvider).requestAdvance(
                            amount: amount,
                            reason: reasonController.text.isNotEmpty ? reasonController.text : null,
                          );
                          if (context.mounted) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Salary advance request submitted for fleet manager approval!')),
                            );
                            ref.invalidate(walletSummaryProvider);
                          }
                        } catch (e) {
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Failed to request advance: $e')),
                            );
                          }
                        } finally {
                          if (context.mounted) {
                            setState(() {
                              isSubmitting = false;
                            });
                          }
                        }
                      },
                child: isSubmitting ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Submit Request'),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final walletAsync = ref.watch(walletSummaryProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Driver Wallet')),
      body: walletAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error loading wallet: $err', textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.invalidate(walletSummaryProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (walletData) {
          final double balance = (walletData['balance'] ?? 0).toDouble();
          final double totalSalary = (walletData['total_salary'] ?? 0).toDouble();
          final double totalAdvances = (walletData['total_advances'] ?? 0).toDouble();
          final double totalIncentives = (walletData['total_incentives'] ?? 0).toDouble();
          final List transactions = walletData['recent_transactions'] ?? [];

          final currencyFormat = NumberFormat.currency(locale: 'en_IN', symbol: '₹');

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(walletSummaryProvider);
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Balance Card
                  Card(
                    color: Theme.of(context).colorScheme.primary,
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Available Wallet Balance', style: TextStyle(color: Colors.white70, fontSize: 14)),
                          const SizedBox(height: 8),
                          Text(currencyFormat.format(balance), style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 20),
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton.icon(
                                  style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.black),
                                  onPressed: () => _showAdvanceDialog(context, ref),
                                  icon: const Icon(Icons.request_quote),
                                  label: const Text('Request Advance'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildSummaryTile(context, 'Total Salary', currencyFormat.format(totalSalary), Colors.blue),
                      _buildSummaryTile(context, 'Total Advances', currencyFormat.format(totalAdvances), Colors.orange),
                      _buildSummaryTile(context, 'Incentives', currencyFormat.format(totalIncentives), Colors.green),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text('Recent Transactions', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  if (transactions.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(32.0),
                      child: Center(child: Text('No transactions found')),
                    )
                  else
                    ...transactions.map((tx) {
                      final double amount = (tx['amount'] ?? 0).toDouble();
                      final String type = tx['transaction_type'] ?? 'UNKNOWN';
                      final String status = tx['status'] ?? 'UNKNOWN';
                      final String dateStr = tx['created_at'];
                      final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                      final formattedDate = DateFormat('dd MMM yyyy, hh:mm a').format(date);
                      
                      IconData icon;
                      Color color;
                      String prefix = '';
                      
                      if (type == 'ADVANCE') {
                        icon = Icons.arrow_upward;
                        color = Colors.orange;
                        prefix = '-';
                      } else if (type == 'INCENTIVE') {
                        icon = Icons.star;
                        color = Colors.blue;
                        prefix = '+';
                      } else {
                        icon = Icons.arrow_downward;
                        color = Colors.green;
                        prefix = '+';
                      }

                      return Card(
                        child: ListTile(
                          leading: CircleAvatar(backgroundColor: color, child: Icon(icon, color: Colors.white)),
                          title: Text(tx['description'] ?? type, style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text('$status • $formattedDate'),
                          trailing: Text('$prefix${currencyFormat.format(amount)}', style: TextStyle(color: color, fontWeight: FontWeight.bold)),
                        ),
                      );
                    }),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummaryTile(BuildContext context, String title, String amount, Color color) {
    return Column(
      children: [
        Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 4),
        Text(amount, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color)),
      ],
    );
  }
}
