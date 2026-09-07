import 'package:flutter/material.dart';
import '../../data/trip_intelligence_models.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/glass_card.dart';

class LiveTripHealthCard extends StatelessWidget {
  final LiveTripIntelligenceResponse data;
  final bool isLoading;

  const LiveTripHealthCard({super.key, required this.data, this.isLoading = false});

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const GlassCard(
        padding: EdgeInsets.all(16),
        child: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isCritical = data.healthStatus == 'CRITICAL';
    final isAtRisk = data.healthStatus == 'AT_RISK';
    
    final headerBg = isCritical ? AppColors.statusRed : isAtRisk ? AppColors.statusAmber : AppColors.statusGreen;
    
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
          border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: headerBg,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.monitor_heart, color: Colors.white, size: 20),
                      SizedBox(width: 8),
                      Text('Live Trip Health', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      data.healthStatus.replaceAll('_', ' '),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!data.snapshotAvailable)
                    Container(
                      margin: const EdgeInsets.bottom(16),
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.statusAmber.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'Pre-trip snapshot unavailable. Live health calculations are limited.',
                        style: TextStyle(color: AppColors.statusAmber, fontSize: 12),
                      ),
                    ),
                  
                  if (data.expectedProfit != null) ...[
                    const Text('Projected Economics', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildMetric('Expected Profit', '₹${data.expectedProfit}', isDark),
                        _buildMetric(
                          'Current Projection',
                          '₹${data.projectedProfit}',
                          isDark,
                          valueColor: (data.profitErosion ?? 0) > 0 ? AppColors.statusRed : AppColors.statusGreen,
                        ),
                      ],
                    ),
                    if ((data.profitErosion ?? 0) > 0) ...[
                      const SizedBox(height: 8),
                      const Divider(),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.trending_down, size: 16, color: AppColors.statusRed),
                              SizedBox(width: 4),
                              Text('Profit Erosion', style: TextStyle(color: AppColors.statusRed, fontSize: 12)),
                            ],
                          ),
                          Text(
                            '-₹${data.profitErosion} (${data.profitErosionPct?.toStringAsFixed(1)}%)',
                            style: const TextStyle(color: AppColors.statusRed, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 16),
                  ],

                  if (data.deviations.isNotEmpty) ...[
                    const Text('Active Deviations', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    const SizedBox(height: 8),
                    ...data.deviations.map((d) => _buildDeviationRow(d, isDark)),
                    const SizedBox(height: 16),
                  ],

                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildMetric(
                        'Elapsed Time',
                        '${data.elapsedHours?.toStringAsFixed(1)} hrs',
                        isDark,
                        subtext: data.estimatedRemainingHours != null ? '${data.estimatedRemainingHours?.toStringAsFixed(1)} hrs left est.' : null,
                      ),
                      _buildMetric(
                        'Cost So Far',
                        '₹${data.actualCostSoFar}',
                        isDark,
                        subtext: data.projectedTotalCost != null ? '₹${data.projectedTotalCost} total est.' : null,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetric(String label, String value, bool isDark, {Color? valueColor, String? subtext}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: valueColor ?? (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface))),
        if (subtext != null)
          Text(subtext, style: TextStyle(fontSize: 10, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
      ],
    );
  }

  Widget _buildDeviationRow(Deviation dev, bool isDark) {
    final isCrit = dev.severity == 'CRITICAL';
    final color = isCrit ? AppColors.statusRed : AppColors.statusAmber;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        border: Border.all(color: color.withValues(alpha: 0.2)),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: RichText(
              text: TextSpan(
                style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                children: [
                  TextSpan(text: '${dev.metric}: ', style: const TextStyle(fontWeight: FontWeight.bold)),
                  TextSpan(text: dev.description),
                ],
              ),
            ),
          ),
          if (dev.variancePct != null)
            Text(
              '${dev.variancePct! > 0 ? '+' : ''}${dev.variancePct!.toStringAsFixed(1)}%',
              style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 12),
            ),
        ],
      ),
    );
  }
}
