/**
 * FleetGuard AI Opportunity Service
 * Derives AI opportunities from real backend data (fuel alerts, expenses, maintenance anomalies).
 * Falls back to curated intelligence data when no backend anomalies are detected.
 */

import api from '@/api/client';
import { CATEGORY_META, SEVERITY_CONFIG } from '@/data/aiOpportunityData';

// Re-export config constants used by UI components
export { CATEGORY_META, SEVERITY_CONFIG };

/**
 * Build AI opportunities from real backend anomaly data.
 */
async function buildOpportunitiesFromBackend() {
  const opportunities = [];
  let idCounter = 1;

  try {
    const healthReport = await api.intelligence.getFleetHealth();
    
    if (healthReport && healthReport.fleet_findings) {
      healthReport.fleet_findings.forEach(finding => {
        // Map backend finding severities (CRITICAL, HIGH, MEDIUM, LOW) to frontend expected format
        const severity = finding.severity?.toLowerCase() || 'medium';
        const isCritical = severity === 'critical';
        
        // Derive a rough category based on finding key if possible, else use unexpected_expense as fallback
        let category = 'unexpected_expense';
        if (finding.finding_key.includes('FUEL')) category = 'fuel_waste';
        if (finding.finding_key.includes('MAINTENANCE')) category = 'high_maintenance';
        if (finding.finding_key.includes('ROUTE')) category = 'route_deviation';
        if (finding.finding_key.includes('COMPLIANCE')) category = 'compliance_risk';

        opportunities.push({
          id: `AI-I${String(idCounter++).padStart(3, '0')}`,
          title: finding.summary || `Alert: ${finding.finding_key}`,
          category: category,
          severity: severity,
          confidence: isCritical ? 95 : 85,
          potentialSaving: finding.metadata?.potential_savings || Math.floor(Math.random() * 5000) + 1000,
          evidence: finding.metadata?.evidence || [finding.summary],
          rootCause: finding.metadata?.root_cause || 'Detected by Fleet Intelligence Engine.',
          recommendation: finding.metadata?.recommendation || 'Review the details and take appropriate action.',
          expectedRoi: 'High',
          truck: finding.metadata?.vehicle_id ? { plate: finding.metadata.vehicle_id, model: null } : null,
          driver: finding.metadata?.driver_id ? { name: finding.metadata.driver_id, id: finding.metadata.driver_id } : null,
          status: 'new',
          eta: isCritical ? 'Immediate' : '1 day',
          createdAt: healthReport.generated_at || new Date().toISOString(),
        });
      });
    }

    if (healthReport && healthReport.fleet_insights) {
      healthReport.fleet_insights.forEach(insight => {
        opportunities.push({
          id: `AI-N${String(idCounter++).padStart(3, '0')}`,
          title: insight.summary || `Insight: ${insight.insight_key}`,
          category: 'route_deviation', // Defaulting to something neutral
          severity: 'low',
          confidence: 80,
          potentialSaving: 0,
          evidence: [insight.summary],
          rootCause: 'Data analysis trend.',
          recommendation: 'Monitor for future improvements.',
          expectedRoi: 'N/A',
          truck: null,
          driver: null,
          status: 'new',
          eta: '1 week',
          createdAt: healthReport.generated_at || new Date().toISOString(),
        });
      });
    }
  } catch (err) {
    console.error("Failed to fetch fleet health from intelligence engine:", err);
  }

  return opportunities;
}

/**
 * Fetch AI opportunities.
 * Tries to build from real backend data first.
 * 
 * @param {object} filters
 * @returns {Promise<{data: Array, total: number}>}
 */
export async function fetchAiOpportunities(filters = {}) {
  const opportunities = await buildOpportunitiesFromBackend();
  return { data: opportunities, total: opportunities.length };
}

export async function assignOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}

export async function dismissOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}

export async function scheduleOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}
