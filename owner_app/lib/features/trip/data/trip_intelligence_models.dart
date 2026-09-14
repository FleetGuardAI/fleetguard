// lib/features/trip/data/trip_intelligence_models.dart

class PreTripIntelligenceResponse {
  final String recommendation;
  final List<RecommendationReason> recommendationReasons;
  final double? expectedDistance;
  final double? expectedDurationHours;
  final double? expectedFuelLiters;
  final double? expectedFuelCost;
  final double? expectedTotalCost;
  final double? expectedRevenue;
  final double? expectedProfit;
  final double? expectedMarginPct;
  final double? minimumRecommendedFreight;
  final String riskLevel;
  final String confidenceLevel;
  final List<dynamic> assumptions;
  final String intelligenceVersion;

  PreTripIntelligenceResponse({
    required this.recommendation,
    required this.recommendationReasons,
    this.expectedDistance,
    this.expectedDurationHours,
    this.expectedFuelLiters,
    this.expectedFuelCost,
    this.expectedTotalCost,
    this.expectedRevenue,
    this.expectedProfit,
    this.expectedMarginPct,
    this.minimumRecommendedFreight,
    required this.riskLevel,
    required this.confidenceLevel,
    required this.assumptions,
    required this.intelligenceVersion,
  });

  factory PreTripIntelligenceResponse.fromJson(Map<String, dynamic> json) {
    return PreTripIntelligenceResponse(
      recommendation: json['recommendation'] ?? 'REVIEW',
      recommendationReasons: (json['recommendation_reasons'] as List?)
              ?.map((e) => RecommendationReason.fromJson(e))
              .toList() ?? [],
      expectedDistance: (json['expected_distance'] as num?)?.toDouble(),
      expectedDurationHours: (json['expected_duration_hours'] as num?)?.toDouble(),
      expectedFuelLiters: (json['expected_fuel_liters'] as num?)?.toDouble(),
      expectedFuelCost: (json['expected_fuel_cost'] as num?)?.toDouble(),
      expectedTotalCost: (json['expected_total_cost'] as num?)?.toDouble(),
      expectedRevenue: (json['expected_revenue'] as num?)?.toDouble(),
      expectedProfit: (json['expected_profit'] as num?)?.toDouble(),
      expectedMarginPct: (json['expected_margin_pct'] as num?)?.toDouble(),
      minimumRecommendedFreight: (json['minimum_recommended_freight'] as num?)?.toDouble(),
      riskLevel: json['risk_level'] ?? 'MEDIUM',
      confidenceLevel: json['confidence_level'] ?? 'INSUFFICIENT',
      assumptions: json['assumptions'] ?? [],
      intelligenceVersion: json['intelligence_version'] ?? '',
    );
  }
}

class RecommendationReason {
  final String factorType;
  final String description;

  RecommendationReason({required this.factorType, required this.description});

  factory RecommendationReason.fromJson(Map<String, dynamic> json) {
    return RecommendationReason(
      factorType: json['factor_type'] ?? '',
      description: json['description'] ?? '',
    );
  }
}

class LiveTripIntelligenceResponse {
  final String healthStatus;
  final double? expectedDurationHours;
  final double? elapsedHours;
  final double? estimatedRemainingHours;
  final double? actualCostSoFar;
  final double? projectedTotalCost;
  final double? expectedProfit;
  final double? projectedProfit;
  final double? profitErosion;
  final double? profitErosionPct;
  final List<Deviation> deviations;
  final bool snapshotAvailable;

  LiveTripIntelligenceResponse({
    required this.healthStatus,
    this.expectedDurationHours,
    this.elapsedHours,
    this.estimatedRemainingHours,
    this.actualCostSoFar,
    this.projectedTotalCost,
    this.expectedProfit,
    this.projectedProfit,
    this.profitErosion,
    this.profitErosionPct,
    required this.deviations,
    required this.snapshotAvailable,
  });

  factory LiveTripIntelligenceResponse.fromJson(Map<String, dynamic> json) {
    return LiveTripIntelligenceResponse(
      healthStatus: json['health_status'] ?? 'ON_TRACK',
      expectedDurationHours: (json['expected_duration_hours'] as num?)?.toDouble(),
      elapsedHours: (json['elapsed_hours'] as num?)?.toDouble(),
      estimatedRemainingHours: (json['estimated_remaining_hours'] as num?)?.toDouble(),
      actualCostSoFar: (json['actual_cost_so_far'] as num?)?.toDouble(),
      projectedTotalCost: (json['projected_total_cost'] as num?)?.toDouble(),
      expectedProfit: (json['expected_profit'] as num?)?.toDouble(),
      projectedProfit: (json['projected_profit'] as num?)?.toDouble(),
      profitErosion: (json['profit_erosion'] as num?)?.toDouble(),
      profitErosionPct: (json['profit_erosion_pct'] as num?)?.toDouble(),
      deviations: (json['deviations'] as List?)
              ?.map((e) => Deviation.fromJson(e))
              .toList() ?? [],
      snapshotAvailable: json['snapshot_available'] ?? false,
    );
  }
}

class Deviation {
  final String metric;
  final String severity;
  final double? variancePct;
  final String description;

  Deviation({
    required this.metric,
    required this.severity,
    this.variancePct,
    required this.description,
  });

  factory Deviation.fromJson(Map<String, dynamic> json) {
    return Deviation(
      metric: json['metric'] ?? '',
      severity: json['severity'] ?? 'INFO',
      variancePct: (json['variance_pct'] as num?)?.toDouble(),
      description: json['description'] ?? '',
    );
  }
}

class PostTripIntelligenceResponse {
  final OriginalExpectation? originalExpectation;
  final String? recommendationOutcome;
  final double? actualProfit; // Stored in financial_summary
  final double? actualMarginPct; // Stored in financial_summary

  PostTripIntelligenceResponse({
    this.originalExpectation,
    this.recommendationOutcome,
    this.actualProfit,
    this.actualMarginPct,
  });

  factory PostTripIntelligenceResponse.fromJson(Map<String, dynamic> json) {
    return PostTripIntelligenceResponse(
      originalExpectation: json['original_expectation'] != null
          ? OriginalExpectation.fromJson(json['original_expectation'])
          : null,
      recommendationOutcome: json['recommendation_outcome'],
      actualProfit: (json['financial_summary']?['net_profit'] as num?)?.toDouble(),
      actualMarginPct: (json['financial_summary']?['profit_margin_pct'] as num?)?.toDouble(),
    );
  }
}

class OriginalExpectation {
  final double? profit;
  final double? marginPct;
  final String? recommendation;
  final String? confidence;
  final bool hasData;

  OriginalExpectation({
    this.profit,
    this.marginPct,
    this.recommendation,
    this.confidence,
    required this.hasData,
  });

  factory OriginalExpectation.fromJson(Map<String, dynamic> json) {
    return OriginalExpectation(
      profit: (json['profit'] as num?)?.toDouble(),
      marginPct: (json['margin_pct'] as num?)?.toDouble(),
      recommendation: json['recommendation'],
      confidence: json['confidence'],
      hasData: json['has_data'] ?? false,
    );
  }
}
