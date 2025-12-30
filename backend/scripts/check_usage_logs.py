"""Quick script to check usage logs"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db

result = db.service_client.table('ai_usage_logs').select('*', count='exact').execute()
total = result.count if hasattr(result, 'count') else len(result.data or [])
print(f'Total usage logs: {total}')

if result.data:
    sample = result.data[0]
    print(f'Sample: provider={sample.get("provider_name")}, feature={sample.get("feature_name")}, cost=${sample.get("estimated_cost_usd", 0)}')

