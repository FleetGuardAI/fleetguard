import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/expense_provider.dart';
import '../../data/expense_repository.dart';

class ExpenseDetailScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic> expense;

  const ExpenseDetailScreen({super.key, required this.expense});

  @override
  ConsumerState<ExpenseDetailScreen> createState() => _ExpenseDetailScreenState();
}

class _ExpenseDetailScreenState extends ConsumerState<ExpenseDetailScreen> {
  bool _isLoading = false;

  void _handleAction(String action) async {
    setState(() => _isLoading = true);
    try {
      final repo = ref.read(fleetExpenseRepositoryProvider);
      if (action == 'approve') {
        await repo.approveExpense(widget.expense['id']);
      } else {
        await repo.rejectExpense(widget.expense['id']);
      }
      ref.invalidate(fleetExpensesProvider);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Expense ${action}d successfully')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
    final amount = currencyFormatter.format(widget.expense['amount'] ?? 0);
    final status = widget.expense['status'] ?? 'PENDING';
    final isPending = status == 'PENDING';

    return Scaffold(
      backgroundColor: AppColors.darkBackground,
      appBar: AppBar(
        title: const Text('Expense Details', style: TextStyle(color: Colors.white)),
        backgroundColor: AppColors.darkBackground,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildInfoCard('Details', [
            _buildRow('Amount', amount),
            _buildRow('Category', widget.expense['category'] ?? 'N/A'),
            _buildRow('Description', widget.expense['description'] ?? 'N/A'),
            _buildRow('Status', status),
          ]),
          const SizedBox(height: 16),
          _buildInfoCard('Context', [
            _buildRow('Trip ID', widget.expense['trip_id']?.toString() ?? 'N/A'),
            _buildRow('Date', widget.expense['expense_date'] != null 
              ? DateFormat('MMM dd, yyyy').format(DateTime.parse(widget.expense['expense_date'])) 
              : 'N/A'),
          ]),
          const SizedBox(height: 32),
          if (isPending) ...[
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.statusRed,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () => _handleAction('reject'),
                      child: const Text('Reject', style: TextStyle(fontSize: 16, color: Colors.white)),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () => _handleAction('approve'),
                      child: const Text('Approve', style: TextStyle(fontSize: 16, color: Colors.white)),
                    ),
                  ),
                ],
              ),
          ]
        ],
      ),
    );
  }

  Widget _buildInfoCard(String title, List<Widget> children) {
    return Card(
      color: AppColors.darkSurface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.bold, fontSize: 14)),
            const Divider(color: Colors.white10, height: 24),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70)),
          Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
