"""
Recalculate AI Usage Costs
Backfills cost calculations for existing AI usage logs that don't have proper costs calculated
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.services.cost_calculator import CostCalculator
from decimal import Decimal
import structlog

logger = structlog.get_logger()


async def recalculate_all_costs():
    """
    Recalculate costs for all AI usage logs
    Updates logs that have:
    - estimated_cost_usd = 0 or NULL
    - OR need recalculation based on latest pricing
    """
    try:
        logger.info("Starting cost recalculation for all AI usage logs")
        
        # Fetch all logs - we'll recalculate all to ensure consistency
        # Process in batches to avoid memory issues
        batch_size = 1000
        offset = 0
        total_updated = 0
        total_cost = Decimal('0')
        
        while True:
            # Fetch batch of logs
            response = (
                db.service_client.table("ai_usage_logs")
                .select("*")
                .order("created_at", desc=False)
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            
            logs = response.data if response.data else []
            
            if not logs:
                break
            
            logger.info(f"Processing batch: {offset} to {offset + len(logs) - 1}")
            
            # Process each log
            updates = []
            for log in logs:
                try:
                    # Calculate cost using CostCalculator
                    provider_name = log.get("provider_name", "").lower()
                    model_name = log.get("model_name")
                    prompt_tokens = log.get("prompt_tokens")
                    completion_tokens = log.get("completion_tokens")
                    total_tokens = log.get("total_tokens")
                    characters_used = log.get("characters_used")
                    audio_duration_seconds = log.get("audio_duration_seconds")
                    
                    # Calculate cost based on provider
                    calculated_cost = CostCalculator.calculate_cost(
                        provider_name=provider_name,
                        model_name=model_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        characters=characters_used,
                        audio_duration_seconds=float(audio_duration_seconds) if audio_duration_seconds else None
                    )
                    
                    current_cost = Decimal(str(log.get("estimated_cost_usd", 0) or 0))
                    
                    # Only update if cost is different (or if it's 0/NULL)
                    if calculated_cost != current_cost or current_cost == 0:
                        updates.append({
                            "id": log["id"],
                            "estimated_cost_usd": float(calculated_cost),
                            "cost_model_version": "1.0"  # Mark as recalculated
                        })
                        total_cost += calculated_cost
                    
                except Exception as e:
                    logger.warning(
                        f"Error calculating cost for log {log.get('id')}",
                        error=str(e),
                        provider=log.get("provider_name"),
                        feature=log.get("feature_name")
                    )
                    continue
            
            # Bulk update this batch
            if updates:
                for update in updates:
                    try:
                        log_id = update.pop("id")
                        (
                            db.service_client.table("ai_usage_logs")
                            .update(update)
                            .eq("id", log_id)
                            .execute()
                        )
                        total_updated += 1
                    except Exception as e:
                        logger.warning(f"Error updating log {log_id}", error=str(e))
                        continue
            
            offset += batch_size
            
            # Log progress
            if len(logs) < batch_size:
                break
                
        logger.info(
            "Cost recalculation completed",
            total_logs_processed=offset,
            total_updated=total_updated,
            total_calculated_cost=float(total_cost)
        )
        
        return {
            "success": True,
            "total_processed": offset,
            "total_updated": total_updated,
            "total_cost_usd": float(total_cost)
        }
        
    except Exception as e:
        logger.error("Error during cost recalculation", error=str(e))
        raise


async def get_cost_summary():
    """Get summary of current cost state"""
    try:
        # Get total logs
        total_response = (
            db.service_client.table("ai_usage_logs")
            .select("id", count="exact")
            .execute()
        )
        total_logs = total_response.count if hasattr(total_response, 'count') else len(total_response.data) if total_response.data else 0
        
        # Get logs with zero or null cost
        zero_cost_response = (
            db.service_client.table("ai_usage_logs")
            .select("id", count="exact")
            .or_("estimated_cost_usd.is.null,estimated_cost_usd.eq.0")
            .execute()
        )
        zero_cost_count = zero_cost_response.count if hasattr(zero_cost_response, 'count') else len(zero_cost_response.data) if zero_cost_response.data else 0
        
        # Get total current cost
        cost_response = (
            db.service_client.table("ai_usage_logs")
            .select("estimated_cost_usd")
            .execute()
        )
        
        total_cost = Decimal('0')
        if cost_response.data:
            for log in cost_response.data:
                cost = log.get("estimated_cost_usd")
                if cost:
                    total_cost += Decimal(str(cost))
        
        logger.info(
            "Cost summary",
            total_logs=total_logs,
            logs_with_zero_cost=zero_cost_count,
            current_total_cost_usd=float(total_cost)
        )
        
        return {
            "total_logs": total_logs,
            "logs_with_zero_cost": zero_cost_count,
            "current_total_cost_usd": float(total_cost)
        }
        
    except Exception as e:
        logger.error("Error getting cost summary", error=str(e))
        raise


if __name__ == "__main__":
    async def main():
        try:
            # Get summary before
            logger.info("Getting cost summary before recalculation...")
            before_summary = await get_cost_summary()
            
            # Recalculate costs
            result = await recalculate_all_costs()
            
            # Get summary after
            logger.info("Getting cost summary after recalculation...")
            after_summary = await get_cost_summary()
            
            print("\n" + "="*60)
            print("COST RECALCULATION COMPLETE")
            print("="*60)
            print(f"Total logs processed: {result['total_processed']}")
            print(f"Total logs updated: {result['total_updated']}")
            print(f"\nBefore:")
            print(f"  Total logs: {before_summary['total_logs']}")
            print(f"  Logs with zero cost: {before_summary['logs_with_zero_cost']}")
            print(f"  Current total cost: ${before_summary['current_total_cost_usd']:.4f}")
            print(f"\nAfter:")
            print(f"  Total logs: {after_summary['total_logs']}")
            print(f"  Logs with zero cost: {after_summary['logs_with_zero_cost']}")
            print(f"  Current total cost: ${after_summary['current_total_cost_usd']:.4f}")
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error("Fatal error in main", error=str(e))
            print(f"\nERROR: {str(e)}")
            sys.exit(1)
    
    asyncio.run(main())

