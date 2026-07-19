import os
import glob
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove check_version
    content = re.sub(r'\s*check_version=self\.version\(\),', '', content)
    content = re.sub(r'\s*check_version="1\.0",', '', content)
    
    # Change summary to message
    content = re.sub(r'summary=', 'message=', content)
    
    # Remove details
    content = re.sub(r'\s*details=.*?,', '', content)
    content = re.sub(r'\s*details=.*?(\s*\))', r'\1', content)
    
    # Change supporting_evidence to evidence_used
    content = re.sub(r'supporting_evidence=\[latest\]', 'evidence_used=[str(latest.evidence_id)]', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed {filepath}")

for f in glob.glob("c:/Fleetguard/backend/infrastructure/intelligence/tyre_domain/checks/*.py"):
    fix_file(f)

fix_file("c:/Fleetguard/backend/tests/intelligence/tyre_domain/test_tyre_assessment.py")
