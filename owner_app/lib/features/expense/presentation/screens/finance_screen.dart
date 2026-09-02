import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/expense_provider.dart';
import 'expense_detail_screen.dart';
import 'add_expense_screen.dart';
import 'package:fleetguard_owner/l10n/app_localizations.dart';
import '../../../../core/widgets/empty_state_widget.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/glass_card.dart';

class FinanceScreen extends ConsumerWidget {
  const FinanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final loc = AppLocalizations.of(context)!;
    final expensesAsync = ref.watch(fleetExpensesProvider);
    final analyticsAsync = ref.watch(fleetExpenseAnalyticsProvider);
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
    
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text(loc.finance, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      ),
      body: expensesAsync.when(
        data: (expenses) {
          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              analyticsAsync.when(
                data: (analytics) {
                  final totalAmount = analytics['total']?.toDouble() ?? 0.0;
                  final fuelAmount = analytics['fuel']?.toDouble() ?? 0.0;
                  final maintenanceAmount = analytics['maintenance']?.toDouble() ?? 0.0;
                  final otherAmount = analytics['other']?.toDouble() ?? 0.0;
                  
                  return _buildTotalExpenseCard(
                    context,
                    currencyFormatter.format(totalAmount),
                    currencyFormatter.format(fuelAmount),
                    currencyFormatter.format(maintenanceAmount),
                    currencyFormatter.format(otherAmount),
                    totalAmount, fuelAmount, maintenanceAmount, otherAmount,
                  );
                },
                loading: () => const SkeletonLoader(height: 250, borderRadius: 24),
                error: (err, stack) => ErrorStateWidget(
                  message: 'Failed to load analytics.',
                  onRetry: () => ref.refresh(fleetExpenseAnalyticsProvider),
                ),
              ),
              const SizedBox(height: 24),
              Text('Recent Expenses', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 16),
              if (expenses.isEmpty)
                const EmptyStateWidget(
                  icon: Icons.receipt_long,
                  title: 'No Expenses Found',
                  message: 'Your fleet has no recorded expenses yet.',
                ),
              ...expenses.map((exp) {
                final dateStr = exp['expense_date'];
                final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12.0),
                  child: InkWell(
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => ExpenseDetailScreen(expense: exp)));
                    },
                    child: _buildExpenseItem(
                      context,
                      '${exp['category']} — ${exp['description'] ?? 'Unknown'}',
                      currencyFormatter.format(exp['amount'] ?? 0),
                      exp['category'] == 'FUEL' ? Icons.local_gas_station : 
                      exp['category'] == 'REPAIR' ? Icons.build : Icons.receipt_long,
                      formattedDate,
                    ),
                  ),
                );
              }),
              const SizedBox(height: 32),
              Text('Driver Payments & Advances', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
              const SizedBox(height: 16),
              Consumer(
                builder: (context, ref, child) {
                  final walletAsync = ref.watch(fleetWalletTransactionsProvider);
                  return walletAsync.when(
                    data: (transactions) {
                      if (transactions.isEmpty) {
                        return const EmptyStateWidget(
                          icon: Icons.account_balance_wallet,
                          title: 'No Payments Recorded',
                          message: 'No driver payments or advances found.',
                        );
                      }
                      return Column(
                        children: transactions.map((tx) {
                          final dateStr = tx['created_at'];
                          final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
                          final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
                          
                          IconData icon = Icons.payment;
                          if (tx['transaction_type'] == 'SALARY') icon = Icons.account_balance_wallet;
                          if (tx['transaction_type'] == 'ADVANCE') icon = Icons.request_quote;
                          
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: _buildExpenseItem(
                              context,
                              '${tx['driver_name'] ?? 'Unknown Driver'} — ${tx['transaction_type']}',
                              currencyFormatter.format(tx['amount'] ?? 0),
                              icon,
                              '$formattedDate • ${tx['status']}',
                            ),
                          );
                        }).toList(),
                      );
                    },
                    loading: () => ListView.separated(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: 3,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (_, __) => const SkeletonLoader(height: 80, borderRadius: 16),
                    ),
                    error: (err, stack) => ErrorStateWidget(
                      message: 'Failed to load payments.',
                      onRetry: () => ref.refresh(fleetWalletTransactionsProvider),
                    ),
                  );
                },
              ),
            ],
          );
        },
        loading: () => ListView.separated(
          padding: const EdgeInsets.all(16.0),
          itemCount: 4,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (_, __) => const SkeletonLoader(height: 80, borderRadius: 16),
        ),
        error: (err, stack) => ErrorStateWidget(
          message: 'Failed to load expenses.',
          onRetry: () => ref.refresh(fleetExpensesProvider),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const AddExpenseScreen()));
        },
        icon: const Icon(Icons.add_a_photo, color: Colors.white),
        label: const Text('Add Expense', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: AppColors.primary,
      ),
    );
  }

  Widget _buildTotalExpenseCard(BuildContext context, String total, String fuel, String maintenance, String other, double totalAmt, double fuelAmt, double maintAmt, double otherAmt) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Total Fleet Expenses', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 16)),
          const SizedBox(height: 8),
          Text(total, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 36, fontWeight: FontWeight.bold)),
          const SizedBox(height: 24),
          if (totalAmt > 0) SizedBox(
            height: 120,
            child: Row(
              children: [
                Expanded(
                  child: PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: 20,
                      sections: [
                        if (fuelAmt > 0) PieChartSectionData(value: fuelAmt, color: AppColors.statusAmber, radius: 25, showTitle: false),
                        if (maintAmt > 0) PieChartSectionData(value: maintAmt, color: AppColors.primary, radius: 25, showTitle: false),
                        if (otherAmt > 0) PieChartSectionData(value: otherAmt, color: AppColors.statusGreen, radius: 25, showTitle: false),
                      ],
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _BreakdownItem(label: 'Fuel', amount: fuel, color: AppColors.statusAmber),
                      const SizedBox(height: 8),
                      _BreakdownItem(label: 'Maintenance', amount: maintenance, color: AppColors.primary),
                      const SizedBox(height: 8),
                      _BreakdownItem(label: 'Other', amount: other, color: AppColors.statusGreen),
                    ],
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildExpenseItem(BuildContext context, String title, String amount, IconData icon, String date) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.primary.withValues(alpha: 0.1),
            child: Icon(icon, color: AppColors.primary),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontWeight: FontWeight.w600, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                Text(date, style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
              ],
            ),
          ),
          Text(amount, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        ],
      ),
    );
  }
}

class _BreakdownItem extends StatelessWidget {
  final String label;
  final String amount;
  final Color color;

  const _BreakdownItem({required this.label, required this.amount, required this.color});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Row(
      children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 8),
        Expanded(child: Text(label, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12))),
        Text(amount, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold, fontSize: 14)),
      ],
    );
  }
}
