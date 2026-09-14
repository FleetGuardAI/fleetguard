import 'package:flutter/material.dart';
import '../../data/trip_intelligence_models.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/glass_card.dart';

class PostTripPerformanceCard extends StatelessWidget {
  final PostTripIntelligenceResponse data;
  final bool isLoading;

  const PostTripPerformanceCard({super.key, required this.data, this.isLoading = false});

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

    if (data.originalExpectation == null || !data.originalExpectation!.hasData) {
      return const SizedBox.shrink();
    }

    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    Color outcomeColor;
    switch (data.recommendationOutcome) {
      case 'OUTPERFORMED':
        outcomeColor = AppColors.statusGreen;
        break;
      case 'LOSS':
        outcomeColor = AppColors.statusRed;
        break;
      case 'UNDERPERFORMED':
        outcomeColor = AppColors.statusAmber;
        break;
      default:
        outcomeColor = AppColors.coolGray;
        break;
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF1A1A3A) : const Color(0xFFF0F0FA), // Subtle indigo tint
          border: Border.all(color: const Color(0xFF6366F1).withValues(alpha: 0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: const BoxDecoration(
                border: Border(bottom: BorderSide(color: Color(0xFF6366F1), width: 0.5)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.psychology, color: Color(0xFF6366F1), size: 20),
                      SizedBox(width: 8),
                      Text('Original Dispatch Intelligence', style: TextStyle(color: Color(0xFF6366F1), fontWeight: FontWeight.bold)),
                    ],
                  ),
                  if (data.recommendationOutcome != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: outcomeColor.withValues(alpha: 0.1),
                        border: Border.all(color: outcomeColor.withValues(alpha: 0.3)),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        'Outcome: ${data.recommendationOutcome!.replaceAll('_', ' ')}',
                        style: TextStyle(color: outcomeColor, fontWeight: FontWeight.bold, fontSize: 10),
                      ),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildMetric('Expected Profit', data.originalExpectation?.profit != null ? '₹${data.originalExpectation!.profit}' : '---', isDark),
                  _buildMetric('Expected Margin', data.originalExpectation?.marginPct != null ? '${data.originalExpectation!.marginPct!.toStringAsFixed(1)}%' : '---', isDark),
                  _buildMetric(
                    'Dispatch Rec.', 
                    data.originalExpectation?.recommendation ?? '---', 
                    isDark, 
                    valueColor: _getRecColor(data.originalExpectation?.recommendation)
                  ),
                  _buildMetric('Confidence', data.originalExpectation?.confidence ?? '---', isDark),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetric(String label, String value, bool isDark, {Color? valueColor}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 10, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: valueColor ?? (isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface))),
      ],
    );
  }

  Color _getRecColor(String? rec) {
    switch (rec) {
      case 'TAKE': return AppColors.statusGreen;
      case 'REVIEW': return AppColors.statusAmber;
      case 'AVOID': return AppColors.statusRed;
      default: return AppColors.coolGray;
    }
  }
}
