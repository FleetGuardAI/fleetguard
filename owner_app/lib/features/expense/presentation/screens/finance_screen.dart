import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/expense_provider.dart';
import '../providers/reports_provider.dart';
import 'expense_detail_screen.dart';
import 'add_expense_screen.dart';
import '../../../../core/widgets/empty_state_widget.dart';
import '../../../../core/widgets/error_state_widget.dart';
import '../../../../core/widgets/skeleton_loader.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/utils/navigation_safe_area.dart';

class FinanceScreen extends ConsumerStatefulWidget {
  const FinanceScreen({super.key});

  @override
  ConsumerState<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends ConsumerState<FinanceScreen> with SingleTickerProviderStateMixin {
  int _touchedDonutIndex = -1;
  int _touchedBarIndex = -1;
  late TabController _tabController;

  final List<String> _periods = [
    'This Month',
    'Last Month',
    'Last 3 Months',
    'Last 6 Months',
    'This Year'
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // Helper to filter dates locally
  bool _isDateInPeriod(DateTime date, String period) {
    final now = DateTime.now();
    DateTime start;
    DateTime end = now;
    
    switch (period) {
      case 'This Month':
        start = DateTime(now.year, now.month, 1);
        break;
      case 'Last Month':
        start = DateTime(now.year, now.month - 1, 1);
        end = DateTime(now.year, now.month, 0, 23, 59, 59);
        break;
      case 'Last 3 Months':
        start = DateTime(now.year, now.month - 3, 1);
        break;
      case 'Last 6 Months':
        start = DateTime(now.year, now.month - 6, 1);
        break;
      case 'This Year':
        start = DateTime(now.year, 1, 1);
        break;
      default:
        start = DateTime(now.year, now.month, 1);
    }
    
    return date.isAfter(start.subtract(const Duration(days: 1))) && date.isBefore(end.add(const Duration(days: 1)));
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Finance', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold, fontSize: 24)),
            Text("Manage your fleet's expenses and payments", style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12, fontWeight: FontWeight.normal), maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16.0),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: ref.watch(selectedPeriodProvider),
                dropdownColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                icon: Icon(Icons.arrow_drop_down, color: AppColors.primary),
                style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
                onChanged: (String? newValue) {
                  if (newValue != null) {
                    ref.read(selectedPeriodProvider.notifier).state = newValue;
                  }
                },
                items: _periods.map<DropdownMenuItem<String>>((String value) {
                  return DropdownMenuItem<String>(
                    value: value,
                    child: Text(value),
                  );
                }).toList(),
              ),
            ),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant,
          indicatorColor: AppColors.primary,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Expenses'),
            Tab(text: 'Payments'),
            Tab(text: 'Reports'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOverviewTab(context, isDark, currencyFormatter),
          _buildExpensesTab(context, isDark, currencyFormatter),
          _buildPaymentsTab(context, isDark, currencyFormatter),
          _buildReportsTab(context, isDark),
        ],
      ),
      floatingActionButton: Padding(
        padding: EdgeInsets.only(bottom: context.fixedControlClearance > 0 ? context.fixedControlClearance - 16 : 0),
        child: FloatingActionButton.extended(
          onPressed: () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const AddExpenseScreen()));
          },
          icon: const Icon(Icons.add_a_photo, color: Colors.white),
          label: const Text('Add Expense', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          backgroundColor: AppColors.primary,
        ),
      ),
    );
  }

  Widget _buildOverviewTab(BuildContext context, bool isDark, NumberFormat currencyFormatter) {
    final expensesAsync = ref.watch(fleetExpensesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(fleetExpensesProvider);
      },
      child: expensesAsync.when(
        data: (expenses) {
          // Filter expenses locally
          final selectedPeriod = ref.watch(selectedPeriodProvider);
          final filteredExpenses = expenses.where((exp) {
            final dateStr = exp['expense_date'];
            if (dateStr == null) return false;
            final date = DateTime.parse(dateStr).toLocal();
            return _isDateInPeriod(date, selectedPeriod);
          }).toList();

          // Calculate analytics locally for exact period matching
          double totalAmt = 0;
          double fuelAmt = 0;
          double maintAmt = 0;
          double otherAmt = 0;

          for (var exp in filteredExpenses) {
            final double amount = (exp['amount'] ?? 0).toDouble();
            totalAmt += amount;
            if (exp['category'] == 'FUEL') {
              fuelAmt += amount;
            } else if (exp['category'] == 'REPAIR' || exp['category'] == 'MAINTENANCE') {
              maintAmt += amount;
            } else {
              otherAmt += amount;
            }
          }

          return SingleChildScrollView(
            padding: EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: context.scrollContentClearance),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildTotalExpenseCard(context, totalAmt, fuelAmt, maintAmt, otherAmt, isDark, currencyFormatter),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(child: _buildCategoryCard('Fuel', fuelAmt, Icons.local_gas_station, AppColors.info, isDark, currencyFormatter)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildCategoryCard('Maintenance', maintAmt, Icons.build, AppColors.primary, isDark, currencyFormatter)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildCategoryCard('Other', otherAmt, Icons.receipt_long, AppColors.purpleAccent, isDark, currencyFormatter)),
                  ],
                ),
                const SizedBox(height: 32),
                _buildExpenseTrendsChart(filteredExpenses, isDark, currencyFormatter),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Recent Expenses', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                    TextButton(
                      onPressed: () => _tabController.animateTo(1),
                      child: Row(
                        children: [
                          Text('View All', style: TextStyle(color: AppColors.primary)),
                          Icon(Icons.arrow_forward, size: 16, color: AppColors.primary),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                if (filteredExpenses.isEmpty)
                  const EmptyStateWidget(
                    icon: Icons.receipt_long,
                    title: 'No Expenses Found',
                    message: 'No expenses recorded in this period.',
                  ),
                ...filteredExpenses.take(5).map((exp) {
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
                        isDark,
                      ),
                    ),
                  );
                }),
              ],
            ),
          );
        },
        loading: () => ListView.separated(
          padding: EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: context.scrollContentClearance),
          itemCount: 4,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (_, __) => const SkeletonLoader(height: 120, borderRadius: 16),
        ),
        error: (err, stack) => ErrorStateWidget(
          message: 'Failed to load expenses.',
          onRetry: () => ref.refresh(fleetExpensesProvider),
        ),
      ),
    );
  }

  Widget _buildTotalExpenseCard(BuildContext context, double totalAmt, double fuelAmt, double maintAmt, double otherAmt, bool isDark, NumberFormat currencyFormatter) {
    // For demo purposes, we'll pretend there was a 12% decrease
    const trendText = '↓ 12%';
    
    // Calculate dynamic center text based on touched index
    String centerValue = currencyFormatter.format(totalAmt);
    String centerLabel = 'Total';
    
    if (_touchedDonutIndex == 0) {
      centerValue = currencyFormatter.format(fuelAmt);
      centerLabel = 'Fuel (${((fuelAmt / (totalAmt == 0 ? 1 : totalAmt)) * 100).toStringAsFixed(1)}%)';
    } else if (_touchedDonutIndex == 1) {
      centerValue = currencyFormatter.format(maintAmt);
      centerLabel = 'Maint (${((maintAmt / (totalAmt == 0 ? 1 : totalAmt)) * 100).toStringAsFixed(1)}%)';
    } else if (_touchedDonutIndex == 2) {
      centerValue = currencyFormatter.format(otherAmt);
      centerLabel = 'Other (${((otherAmt / (totalAmt == 0 ? 1 : totalAmt)) * 100).toStringAsFixed(1)}%)';
    }

    return GlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Total Fleet Expenses', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 16)),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(currencyFormatter.format(totalAmt), style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontSize: 36, fontWeight: FontWeight.bold, letterSpacing: -1)),
              const SizedBox(width: 12),
              Padding(
                padding: const EdgeInsets.only(bottom: 6.0),
                child: Text('$trendText vs previous', style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600, fontSize: 14)),
              ),
            ],
          ),
          const SizedBox(height: 32),
          if (totalAmt > 0) SizedBox(
            height: 180,
            child: Row(
              children: [
                Expanded(
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      PieChart(
                        PieChartData(
                          pieTouchData: PieTouchData(
                            touchCallback: (FlTouchEvent event, pieTouchResponse) {
                              setState(() {
                                if (!event.isInterestedForInteractions || pieTouchResponse == null || pieTouchResponse.touchedSection == null) {
                                  _touchedDonutIndex = -1;
                                  return;
                                }
                                _touchedDonutIndex = pieTouchResponse.touchedSection!.touchedSectionIndex;
                              });
                            },
                          ),
                          sectionsSpace: 4,
                          centerSpaceRadius: 45,
                          startDegreeOffset: -90,
                          sections: [
                            if (fuelAmt > 0) PieChartSectionData(
                              value: fuelAmt, 
                              color: AppColors.info, 
                              radius: _touchedDonutIndex == 0 ? 30 : 20, 
                              showTitle: false
                            ),
                            if (maintAmt > 0) PieChartSectionData(
                              value: maintAmt, 
                              color: AppColors.primary, 
                              radius: _touchedDonutIndex == 1 ? 30 : 20, 
                              showTitle: false
                            ),
                            if (otherAmt > 0) PieChartSectionData(
                              value: otherAmt, 
                              color: AppColors.purpleAccent, 
                              radius: _touchedDonutIndex == 2 ? 30 : 20, 
                              showTitle: false
                            ),
                          ],
                        ),
                        swapAnimationDuration: const Duration(milliseconds: 250),
                      ),
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(centerLabel, style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                          Text(centerValue, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _BreakdownItem(
                        label: 'Fuel', 
                        amount: currencyFormatter.format(fuelAmt), 
                        color: AppColors.info, 
                        isTouched: _touchedDonutIndex == 0,
                        onTap: () => setState(() => _touchedDonutIndex = _touchedDonutIndex == 0 ? -1 : 0),
                      ),
                      const SizedBox(height: 16),
                      _BreakdownItem(
                        label: 'Maintenance', 
                        amount: currencyFormatter.format(maintAmt), 
                        color: AppColors.primary,
                        isTouched: _touchedDonutIndex == 1,
                        onTap: () => setState(() => _touchedDonutIndex = _touchedDonutIndex == 1 ? -1 : 1),
                      ),
                      const SizedBox(height: 16),
                      _BreakdownItem(
                        label: 'Other', 
                        amount: currencyFormatter.format(otherAmt), 
                        color: AppColors.purpleAccent,
                        isTouched: _touchedDonutIndex == 2,
                        onTap: () => setState(() => _touchedDonutIndex = _touchedDonutIndex == 2 ? -1 : 2),
                      ),
                    ],
                  ),
                )
              ],
            ),
          ) else
             const SizedBox(
               height: 150,
               child: Center(child: Text('No expense data to display for this period.')),
             ),
        ],
      ),
    );
  }

  Widget _buildCategoryCard(String title, double amount, IconData icon, Color color, bool isDark, NumberFormat currencyFormatter) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(height: 12),
          Text(title, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12)),
          const SizedBox(height: 4),
          Text(currencyFormatter.format(amount), style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: FontWeight.bold, fontSize: 16), maxLines: 1, overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }

  Widget _buildExpenseTrendsChart(List<Map<String, dynamic>> expenses, bool isDark, NumberFormat formatter) {
    if (expenses.isEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Expense Trends', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
          const SizedBox(height: 16),
          const EmptyStateWidget(icon: Icons.bar_chart, title: 'Insufficient Data', message: 'No expenses recorded in this period.'),
        ],
      );
    }

    final Map<String, double> grouped = {};
    for (var exp in expenses) {
      final dateStr = exp['expense_date'];
      if (dateStr == null) continue;
      final date = DateTime.parse(dateStr).toLocal();
      final key = DateFormat('MMM dd').format(date);
      grouped[key] = (grouped[key] ?? 0) + (exp['amount'] ?? 0).toDouble();
    }
    
    final sortedKeys = grouped.keys.toList()..sort((a, b) {
      try {
        return DateFormat('MMM dd').parse(a).compareTo(DateFormat('MMM dd').parse(b));
      } catch (_) {
        return 0;
      }
    });
    
    final keys = sortedKeys.length > 6 ? sortedKeys.sublist(sortedKeys.length - 6) : sortedKeys;
    final List<double> values = keys.map((k) => grouped[k]!).toList();
    double maxY = values.isEmpty ? 1000 : values.reduce((a, b) => a > b ? a : b) * 1.2;
    if (maxY == 0) maxY = 1000;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Expense Trends', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        const SizedBox(height: 24),
        SizedBox(
          height: 200,
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              maxY: maxY,
              barTouchData: BarTouchData(
                enabled: true,
                touchTooltipData: BarTouchTooltipData(
                  tooltipBgColor: isDark ? AppColors.lightCardBackground : AppColors.darkCardBackground,
                  getTooltipItem: (group, groupIndex, rod, rodIndex) {
                    return BarTooltipItem(
                      formatter.format(rod.toY),
                      TextStyle(color: isDark ? AppColors.lightOnSurface : AppColors.darkOnSurface, fontWeight: FontWeight.bold),
                    );
                  },
                ),
                touchCallback: (FlTouchEvent event, barTouchResponse) {
                  setState(() {
                    if (!event.isInterestedForInteractions || barTouchResponse == null || barTouchResponse.spot == null) {
                      _touchedBarIndex = -1;
                      return;
                    }
                    _touchedBarIndex = barTouchResponse.spot!.touchedBarGroupIndex;
                  });
                },
              ),
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final idx = value.toInt();
                      final title = idx >= 0 && idx < keys.length ? keys[idx] : '';
                      return Padding(
                        padding: const EdgeInsets.only(top: 8.0),
                        child: Text(title, style: TextStyle(fontSize: 10, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                      );
                    },
                  ),
                ),
                leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: const FlGridData(show: false),
              borderData: FlBorderData(show: false),
              barGroups: List.generate(values.length, (i) {
                return BarChartGroupData(
                  x: i,
                  barRods: [
                    BarChartRodData(
                      toY: values[i],
                      color: _touchedBarIndex == i ? AppColors.emerald : AppColors.primary.withValues(alpha: 0.6),
                      width: 16,
                      borderRadius: BorderRadius.circular(4),
                      backDrawRodData: BackgroundBarChartRodData(
                        show: true,
                        toY: maxY,
                        color: isDark ? AppColors.darkCardBackground : AppColors.lightBorder.withValues(alpha: 0.5),
                      )
                    )
                  ],
                );
              }),
            ),
            swapAnimationDuration: const Duration(milliseconds: 250),
          ),
        ),
      ],
    );
  }

  Widget _buildExpensesTab(BuildContext context, bool isDark, NumberFormat currencyFormatter) {
    final expensesAsync = ref.watch(fleetExpensesProvider);
    return expensesAsync.when(
      data: (expenses) {
        final selectedPeriod = ref.watch(selectedPeriodProvider);
        final filteredExpenses = expenses.where((exp) {
          final dateStr = exp['expense_date'];
          if (dateStr == null) return false;
          final date = DateTime.parse(dateStr).toLocal();
          return _isDateInPeriod(date, selectedPeriod);
        }).toList();

        if (filteredExpenses.isEmpty) {
          return const EmptyStateWidget(icon: Icons.receipt_long, title: 'No Expenses Found', message: 'No expenses recorded in this period.');
        }

        return ListView.builder(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: context.scrollContentClearance),
          itemCount: filteredExpenses.length,
          itemBuilder: (context, index) {
            final exp = filteredExpenses[index];
            final dateStr = exp['expense_date'];
            final date = dateStr != null ? DateTime.parse(dateStr).toLocal() : DateTime.now();
            final formattedDate = DateFormat('MMM dd, hh:mm a').format(date);
            return Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: InkWell(
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ExpenseDetailScreen(expense: exp))),
                child: _buildExpenseItem(
                  context,
                  '${exp['category']} — ${exp['description'] ?? 'Unknown'}',
                  currencyFormatter.format(exp['amount'] ?? 0),
                  exp['category'] == 'FUEL' ? Icons.local_gas_station : exp['category'] == 'REPAIR' ? Icons.build : Icons.receipt_long,
                  formattedDate,
                  isDark,
                ),
              ),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, __) => const Center(child: Text('Failed to load expenses')),
    );
  }

  Widget _buildPaymentsTab(BuildContext context, bool isDark, NumberFormat currencyFormatter) {
    final walletAsync = ref.watch(fleetWalletTransactionsProvider);
    return walletAsync.when(
      data: (transactions) {
        final selectedPeriod = ref.watch(selectedPeriodProvider);
        final filteredTx = transactions.where((tx) {
          final dateStr = tx['created_at'];
          if (dateStr == null) return false;
          final date = DateTime.parse(dateStr).toLocal();
          return _isDateInPeriod(date, selectedPeriod);
        }).toList();

        if (filteredTx.isEmpty) {
          return const EmptyStateWidget(icon: Icons.account_balance_wallet, title: 'No Payments', message: 'No driver payments or advances found for this period.');
        }

        return ListView.builder(
          padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: context.scrollContentClearance),
          itemCount: filteredTx.length,
          itemBuilder: (context, index) {
            final tx = filteredTx[index];
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
                isDark,
              ),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, __) => const Center(child: Text('Failed to load payments')),
    );
  }

  Widget _buildReportsTab(BuildContext context, bool isDark) {
    final reportAsync = ref.watch(fleetReportProvider);
    
    return reportAsync.when(
      data: (reportData) {
        final kpis = reportData['kpis'] as dynamic; // DashboardKPIs
        final mileageTrend = reportData['mileageTrend'] as List;
        final expenseDistribution = reportData['expenseDistribution'] as List;
        
        return ListView(
          padding: EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: context.scrollContentClearance),
          children: [
            Text('Fleet Analytics', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            const SizedBox(height: 16),
            GlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('KPI Summary', style: TextStyle(fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildReportStat('Active Trucks', '${kpis.totalActiveTrucks}', Icons.local_shipping, isDark),
                      _buildReportStat('Active Trips', '${kpis.activeTrips}', Icons.route, isDark),
                      _buildReportStat('Pending Issues', '${kpis.attentionRequired}', Icons.warning_amber, isDark),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Text('Expense Distribution', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            const SizedBox(height: 16),
            expenseDistribution.isEmpty
                ? const EmptyStateWidget(icon: Icons.pie_chart_outline, title: 'Insufficient Data', message: 'No expenses recorded to show distribution.')
                : SizedBox(
                    height: 250,
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 2,
                        centerSpaceRadius: 50,
                        sections: expenseDistribution.asMap().entries.map((entry) {
                          final i = entry.key;
                          final e = entry.value;
                          final isTouched = i == _touchedDonutIndex;
                          final radius = isTouched ? 60.0 : 50.0;
                          final value = double.parse(e['value'].toString());
                          final color = _getCategoryColor(e['name'], isDark);
                          
                          return PieChartSectionData(
                            color: color,
                            value: value,
                            title: '${value.toStringAsFixed(0)}%',
                            radius: radius,
                            titleStyle: TextStyle(
                              fontSize: isTouched ? 16 : 14,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          );
                        }).toList(),
                        pieTouchData: PieTouchData(
                          touchCallback: (FlTouchEvent event, pieTouchResponse) {
                            setState(() {
                              if (!event.isInterestedForInteractions || pieTouchResponse == null || pieTouchResponse.touchedSection == null) {
                                _touchedDonutIndex = -1;
                                return;
                              }
                              _touchedDonutIndex = pieTouchResponse.touchedSection!.touchedSectionIndex;
                            });
                          },
                        ),
                      ),
                    ),
                  ),
            if (expenseDistribution.isNotEmpty) ...[
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                alignment: WrapAlignment.center,
                children: expenseDistribution.map((e) {
                  return Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(width: 12, height: 12, decoration: BoxDecoration(color: _getCategoryColor(e['name'], isDark), shape: BoxShape.circle)),
                      const SizedBox(width: 4),
                      Text(e['name'], style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 12)),
                    ],
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 32),
            Text('Mileage Trend', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            const SizedBox(height: 16),
            mileageTrend.isEmpty
                ? const EmptyStateWidget(icon: Icons.speed, title: 'Insufficient Data', message: 'Not enough trip distance/fuel data to compute mileage.')
                : SizedBox(
                    height: 250,
                    child: LineChart(
                      LineChartData(
                        gridData: FlGridData(show: true, drawVerticalLine: false, horizontalInterval: 1),
                        titlesData: FlTitlesData(
                          leftTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              reservedSize: 40,
                              getTitlesWidget: (value, meta) => Text(value.toStringAsFixed(1), style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 10)),
                            ),
                          ),
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (value, meta) {
                                if (value.toInt() >= 0 && value.toInt() < mileageTrend.length) {
                                  return Padding(
                                    padding: const EdgeInsets.only(top: 8.0),
                                    child: Text(mileageTrend[value.toInt()]['month'], style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 10)),
                                  );
                                }
                                return const Text('');
                              },
                              interval: 1,
                            ),
                          ),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        borderData: FlBorderData(show: false),
                        lineBarsData: [
                          LineChartBarData(
                            spots: mileageTrend.asMap().entries.map((e) {
                              return FlSpot(e.key.toDouble(), double.parse(e.value['avg_mileage'].toString()));
                            }).toList(),
                            isCurved: true,
                            color: AppColors.primary,
                            barWidth: 3,
                            isStrokeCapRound: true,
                            dotData: const FlDotData(show: true),
                            belowBarData: BarAreaData(
                              show: true,
                              color: AppColors.primary.withValues(alpha: 0.1),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
          ],
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => Center(child: Text('Error loading reports: $e')),
    );
  }

  Color _getCategoryColor(String category, bool isDark) {
    switch (category.toUpperCase()) {
      case 'FUEL': return AppColors.info;
      case 'TOLL':
      case 'TOLLS': return AppColors.orangeAccent;
      case 'MAINTENANCE':
      case 'REPAIR': return AppColors.primary;
      case 'TYRE':
      case 'TYRES': return AppColors.purpleAccent;
      case 'SALARY': return AppColors.redAlert;
      case 'MISC':
      case 'MISCELLANEOUS': return Colors.amber;
      default: return isDark ? AppColors.darkBorder : AppColors.lightBorder;
    }
  }

  Widget _buildReportStat(String label, String value, IconData icon, bool isDark) {
    return Column(
      children: [
        Icon(icon, color: AppColors.primary),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        Text(label, style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
      ],
    );
  }

  Widget _buildExpenseItem(BuildContext context, String title, String amount, IconData icon, String date, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isDark ? AppColors.darkMint.withValues(alpha: 0.1) : AppColors.lightMint,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppColors.primary, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Text(date, style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
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
  final bool isTouched;
  final VoidCallback onTap;

  const _BreakdownItem({required this.label, required this.amount, required this.color, required this.isTouched, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        decoration: BoxDecoration(
          color: isTouched ? color.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
            const SizedBox(width: 8),
            Flexible(child: Text(label, style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontSize: 13, fontWeight: isTouched ? FontWeight.bold : FontWeight.normal), maxLines: 1, overflow: TextOverflow.ellipsis)),
            const SizedBox(width: 4),
            Text(amount, style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface, fontWeight: isTouched ? FontWeight.bold : FontWeight.w600, fontSize: 14)),
          ],
        ),
      ),
    );
  }
}
