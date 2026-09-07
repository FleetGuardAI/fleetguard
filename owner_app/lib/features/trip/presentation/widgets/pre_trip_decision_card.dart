import 'package:flutter/material.dart';
import '../../data/trip_intelligence_models.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/glass_card.dart';

class PreTripDecisionCard extends StatelessWidget {
  final PreTripIntelligenceResponse data;
  final bool isLoading;

  const PreTripDecisionCard({super.key, required this.data, this.isLoading = false});

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
    
    Color recColor;
    IconData recIcon;
    switch (data.recommendation) {
      case 'TAKE':
        recColor = AppColors.statusGreen;
        recIcon = Icons.check_circle;
        break;
      case 'REVIEW':
        recColor = AppColors.statusAmber;
        recIcon = Icons.warning;
        break;
      case 'AVOID':
        recColor = AppColors.statusRed;
        recIcon = Icons.cancel;
        break;
      default:
        recColor = AppColors.coolGray;
        recIcon = Icons.info;
        break;
    }

    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(recIcon, color: recColor, size: 28),
              const SizedBox(width: 8),
              Text(
                data.recommendation,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: recColor,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getRiskColor(data.riskLevel).withValues(alpha: 0.1),
                  border: Border.all(color: _getRiskColor(data.riskLevel).withValues(alpha: 0.3)),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  'RISK: ${data.riskLevel}',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getRiskColor(data.riskLevel),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildEconomicsGrid(isDark),
          const SizedBox(height: 16),
          const Text('Why?', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...data.recommendationReasons.map((r) => _buildReasonRow(r)),
          if (data.minimumRecommendedFreight != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  const Icon(Icons.currency_rupee, size: 16, color: AppColors.primary),
                  const SizedBox(width: 4),
                  const Text('Min Freight:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  const SizedBox(width: 4),
                  Text('₹${data.minimumRecommendedFreight!.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                ],
              ),
            ),
          ],
          const SizedBox(height: 12),
          Text(
            'Confidence: ${data.confidenceLevel}',
            style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
          ),
        ],
      ),
    );
  }

  Widget _buildEconomicsGrid(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkBackground : AppColors.lightBackground,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildMetric('Revenue', data.expectedRevenue != null ? '₹${data.expectedRevenue}' : '---', isDark),
              _buildMetric('Exp. Cost', data.expectedTotalCost != null ? '₹${data.expectedTotalCost}' : '---', isDark),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildMetric(
                'Exp. Profit',
                data.expectedProfit != null ? '₹${data.expectedProfit}' : '---',
                isDark,
                valueColor: (data.expectedProfit ?? 0) >= 0 ? AppColors.statusGreen : AppColors.statusRed,
              ),
              _buildMetric('Margin', data.expectedMarginPct != null ? '${data.expectedMarginPct!.toStringAsFixed(1)}%' : '---', isDark),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String label, String value, bool isDark, {Color? valueColor}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: valueColor ?? (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface))),
      ],
    );
  }

  Widget _buildReasonRow(RecommendationReason reason) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            reason.factorType == 'positive' ? Icons.check : (reason.factorType == 'negative' ? Icons.remove : Icons.circle),
            size: 16,
            color: reason.factorType == 'positive' ? AppColors.statusGreen : (reason.factorType == 'negative' ? AppColors.statusRed : AppColors.coolGray),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              reason.description,
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Color _getRiskColor(String risk) {
    switch (risk) {
      case 'HIGH': return AppColors.statusRed;
      case 'MEDIUM': return AppColors.statusAmber;
      case 'LOW': return AppColors.statusGreen;
      default: return AppColors.coolGray;
    }
  }
}
