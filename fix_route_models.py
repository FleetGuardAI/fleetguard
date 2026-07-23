import os
import re

# Fix assessment
file = "c:/Fleetguard/backend/infrastructure/intelligence/route_domain/assessments/trip_compliance.py"
with open(file, 'r') as f:
    content = f.read()

content = content.replace(
    "            assessment_key=self.key(),\n            assessment_name=self.name(),\n            status=AssessmentStatus.INCONCLUSIVE,\n            findings=[],\n            contributing_checks=checks\n        )",
    "            assessment_key=self.key(),\n            assessment_name=self.name(),\n            assessment_version=self.version(),\n            status=AssessmentStatus.INCONCLUSIVE,\n            summary=\"Missing required checks.\",\n            findings=[],\n            contributing_checks=checks\n        )"
)
content = content.replace(
    "            assessment_key=self.key(),\n            assessment_name=self.name(),\n            status=AssessmentStatus.COMPLETE,\n            findings=findings,\n            contributing_checks=checks\n        )",
    "            assessment_key=self.key(),\n            assessment_name=self.name(),\n            assessment_version=self.version(),\n            status=AssessmentStatus.COMPLETE,\n            summary=f\"Computed {len(findings)} compliance finding(s).\",\n            findings=findings,\n            contributing_checks=checks\n        )"
)
with open(file, 'w') as f:
    f.write(content)

# Fix risk
file = "c:/Fleetguard/backend/infrastructure/intelligence/route_domain/risk/compliance_risk.py"
with open(file, 'r') as f:
    content = f.read()

content = content.replace("domain_key=self.key()", "risk_engine_key=self.key(), risk_engine_name=self.name(), risk_engine_version=self.version()")
content = content.replace("contributing_assessments=", "supporting_assessments=")
content = content.replace("explanation=", "summary=")

with open(file, 'w') as f:
    f.write(content)
    
# Fix decision
file = "c:/Fleetguard/backend/infrastructure/intelligence/route_domain/decision/compliance_decision.py"
with open(file, 'r') as f:
    content = f.read()

content = content.replace("p.domain_key", "p.risk_engine_key")
with open(file, 'w') as f:
    f.write(content)

# Fix test_route_assessment
file = "c:/Fleetguard/backend/tests/intelligence/route_domain/test_route_assessment.py"
with open(file, 'r') as f:
    content = f.read()

with open(file, 'w') as f:
    f.write(content)

# Fix test_route_risk
file = "c:/Fleetguard/backend/tests/intelligence/route_domain/test_route_risk.py"
with open(file, 'r') as f:
    content = f.read()

content = content.replace(
    "            assessment_key=\"route.trip_compliance_assessment\",\n            assessment_name=\"Trip Compliance Assessment\",\n            status=status,\n            findings=findings,\n            contributing_checks=[]",
    "            assessment_key=\"route.trip_compliance_assessment\",\n            assessment_name=\"Trip Compliance Assessment\",\n            assessment_version=\"1.0.0\",\n            status=status,\n            summary=\"test\",\n            findings=findings,\n            contributing_checks=[]"
)
with open(file, 'w') as f:
    f.write(content)

print("done")
