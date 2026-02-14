"""
Reputation Calculation Service
Calculates agent reputation scores from actual transaction data
Phase 1.4: Real Reputation System
"""

from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from typing import Dict, Optional


class ReputationCalculator:
    """
    Calculates agent reputation based on real performance data
    
    Reputation Score Formula:
        0.40 * success_rate +
        0.20 * response_time_score +
        0.15 * cost_accuracy_score +
        0.15 * repeat_customer_rate +
        0.10 * peer_rating
    """
    
    def __init__(self, db_connection_string: str):
        self.db_url = db_connection_string
        
    def calculate_for_agent(self, agent_id: str) -> Dict:
        """
        Calculate complete reputation metrics for one agent
        Returns dict with all metrics + final reputation score
        """
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        try:
            # Get all executions for this agent
            cur.execute("""
                SELECT 
                    status,
                    success,
                    execution_time_ms,
                    quoted_cost_usd,
                    actual_cost_usd,
                    quality_rating,
                    requesting_agent_id,
                    completed_at
                FROM agent_executions
                WHERE executing_agent_id = %s
                AND status IN ('completed', 'failed', 'timeout')
            """, (agent_id,))
            
            executions = cur.fetchall()
            
            if not executions or len(executions) < 10:
                # Not enough data for reliable reputation
                return {
                    "agent_id": agent_id,
                    "reputation_score": 0.5,
                    "reputation_tier": "unverified",
                    "total_executions": len(executions),
                    "message": "Not enough executions for reliable reputation (minimum 10)"
                }
            
            # Calculate metrics
            metrics = self._calculate_metrics(executions)
            
            # Calculate final reputation score
            reputation_score = self._calculate_reputation_score(metrics)
            reputation_tier = self._get_reputation_tier(reputation_score, len(executions))
            
            # Update database
            self._update_performance_metrics(
                cur, conn, agent_id, metrics, reputation_score, reputation_tier
            )
            
            # Record in history
            self._record_reputation_history(
                cur, conn, agent_id, reputation_score, len(executions),
                metrics['success_rate_overall']
            )
            
            return {
                "agent_id": agent_id,
                "reputation_score": float(reputation_score),
                "reputation_tier": reputation_tier,
                **metrics
            }
            
        finally:
            cur.close()
            conn.close()
    
    def _calculate_metrics(self, executions: list) -> Dict:
        """Calculate all metrics from execution data"""
        total = len(executions)
        successful = sum(1 for e in executions if e[1] == True)  # success column
        failed = sum(1 for e in executions if e[1] == False)
        timeout = sum(1 for e in executions if e[0] == 'timeout')
        
        # Success rates
        success_rate_overall = successful / total if total > 0 else 0
        
        # Last 30 days
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        recent_30d = [e for e in executions if e[7] and e[7] >= thirty_days_ago]
        success_rate_30d = (
            sum(1 for e in recent_30d if e[1] == True) / len(recent_30d)
            if recent_30d else success_rate_overall
        )
        
        # Last 7 days
        seven_days_ago = now - timedelta(days=7)
        recent_7d = [e for e in executions if e[7] and e[7] >= seven_days_ago]
        success_rate_7d = (
            sum(1 for e in recent_7d if e[1] == True) / len(recent_7d)
            if recent_7d else success_rate_overall
        )
        
        # Execution times
        exec_times = [e[2] for e in executions if e[2] is not None]
        avg_execution_time_ms = int(sum(exec_times) / len(exec_times)) if exec_times else 0
        exec_times_sorted = sorted(exec_times) if exec_times else [0]
        median_execution_time_ms = exec_times_sorted[len(exec_times_sorted) // 2]
        p95_index = int(len(exec_times_sorted) * 0.95)
        p95_execution_time_ms = exec_times_sorted[p95_index] if exec_times_sorted else 0
        
        # Cost accuracy
        cost_data = [
            (e[3], e[4]) for e in executions 
            if e[3] is not None and e[4] is not None and e[3] > 0
        ]
        if cost_data:
            accuracies = [
                1 - abs(actual - quoted) / quoted
                for quoted, actual in cost_data
            ]
            avg_cost_accuracy = sum(accuracies) / len(accuracies)
            avg_cost_accuracy = max(0, min(1, avg_cost_accuracy))  # Clamp to [0,1]
        else:
            avg_cost_accuracy = 1.0
        
        # Quality ratings
        ratings = [e[5] for e in executions if e[5] is not None]
        avg_quality_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Network effects
        unique_requesters = len(set(e[6] for e in executions))
        requester_counts = {}
        for e in executions:
            requester = e[6]
            requester_counts[requester] = requester_counts.get(requester, 0) + 1
        repeat_customers = sum(1 for count in requester_counts.values() if count >= 2)
        repeat_customer_rate = repeat_customers / unique_requesters if unique_requesters > 0 else 0
        
        # Total revenue
        revenues = [e[4] for e in executions if e[4] is not None and e[1] == True]
        total_revenue_usd = sum(revenues) if revenues else 0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "timeout_executions": timeout,
            "success_rate_overall": round(success_rate_overall, 4),
            "success_rate_30d": round(success_rate_30d, 4),
            "success_rate_7d": round(success_rate_7d, 4),
            "avg_execution_time_ms": avg_execution_time_ms,
            "median_execution_time_ms": median_execution_time_ms,
            "p95_execution_time_ms": p95_execution_time_ms,
            "avg_cost_accuracy": round(avg_cost_accuracy, 4),
            "avg_quality_rating": round(avg_quality_rating, 2),
            "total_quality_ratings": len(ratings),
            "unique_requesters": unique_requesters,
            "repeat_customer_count": repeat_customers,
            "repeat_customer_rate": round(repeat_customer_rate, 4),
            "total_revenue_usd": float(total_revenue_usd)
        }
    
    def _calculate_reputation_score(self, metrics: Dict) -> Decimal:
        """
        Calculate final reputation score using weighted formula
        
        Formula:
            0.40 * success_rate +
            0.20 * response_time_score +
            0.15 * cost_accuracy_score +
            0.15 * repeat_customer_rate +
            0.10 * peer_rating
        """
        # Success rate (40% weight) - use 30-day for recency
        success_component = 0.40 * metrics['success_rate_30d']
        
        # Response time score (20% weight)
        # Assume 5000ms is "acceptable" - faster is better
        target_time_ms = 5000
        actual_time_ms = metrics['avg_execution_time_ms']
        if actual_time_ms <= 0:
            response_time_score = 1.0
        else:
            response_time_score = min(1.0, target_time_ms / actual_time_ms)
        response_component = 0.20 * response_time_score
        
        # Cost accuracy (15% weight)
        cost_component = 0.15 * metrics['avg_cost_accuracy']
        
        # Repeat customer rate (15% weight)
        repeat_component = 0.15 * metrics['repeat_customer_rate']
        
        # Peer rating (10% weight) - from quality ratings (1-5 scale, normalize to 0-1)
        if metrics['avg_quality_rating'] > 0:
            peer_rating = metrics['avg_quality_rating'] / 5.0
        else:
            peer_rating = 0.5  # Neutral if no ratings
        peer_component = 0.10 * peer_rating
        
        # Final score
        reputation_score = (
            success_component +
            response_component +
            cost_component +
            repeat_component +
            peer_component
        )
        
        return round(Decimal(str(reputation_score)), 4)
    
    def _get_reputation_tier(self, score: Decimal, total_executions: int) -> str:
        """
        Determine reputation tier based on score and volume
        
        Tiers:
        - Unverified: < 10 executions
        - Bronze: 0.50-0.69 (10+ executions)
        - Silver: 0.70-0.84 (25+ executions)
        - Gold: 0.85-0.94 (50+ executions)
        - Platinum: 0.95+ (100+ executions)
        """
        score_float = float(score)
        
        if total_executions < 10:
            return "unverified"
        elif score_float >= 0.95 and total_executions >= 100:
            return "platinum"
        elif score_float >= 0.85 and total_executions >= 50:
            return "gold"
        elif score_float >= 0.70 and total_executions >= 25:
            return "silver"
        else:
            return "bronze"
    
    def _update_performance_metrics(
        self, cur, conn, agent_id: str, metrics: Dict,
        reputation_score: Decimal, reputation_tier: str
    ):
        """Update agent_performance_metrics table"""
        now = datetime.now()
        
        # Get first and last execution times
        cur.execute("""
            SELECT MIN(started_at), MAX(started_at)
            FROM agent_executions
            WHERE executing_agent_id = %s
        """, (agent_id,))
        first_exec, last_exec = cur.fetchone()
        
        cur.execute("""
            INSERT INTO agent_performance_metrics (
                agent_id, total_executions, successful_executions,
                failed_executions, timeout_executions,
                success_rate_overall, success_rate_30d, success_rate_7d,
                avg_execution_time_ms, median_execution_time_ms, p95_execution_time_ms,
                avg_cost_accuracy, total_revenue_usd,
                avg_quality_rating, total_quality_ratings,
                unique_requesters, repeat_customer_count, repeat_customer_rate,
                reputation_score, reputation_tier,
                first_execution_at, last_execution_at, last_updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (agent_id) DO UPDATE SET
                total_executions = EXCLUDED.total_executions,
                successful_executions = EXCLUDED.successful_executions,
                failed_executions = EXCLUDED.failed_executions,
                timeout_executions = EXCLUDED.timeout_executions,
                success_rate_overall = EXCLUDED.success_rate_overall,
                success_rate_30d = EXCLUDED.success_rate_30d,
                success_rate_7d = EXCLUDED.success_rate_7d,
                avg_execution_time_ms = EXCLUDED.avg_execution_time_ms,
                median_execution_time_ms = EXCLUDED.median_execution_time_ms,
                p95_execution_time_ms = EXCLUDED.p95_execution_time_ms,
                avg_cost_accuracy = EXCLUDED.avg_cost_accuracy,
                total_revenue_usd = EXCLUDED.total_revenue_usd,
                avg_quality_rating = EXCLUDED.avg_quality_rating,
                total_quality_ratings = EXCLUDED.total_quality_ratings,
                unique_requesters = EXCLUDED.unique_requesters,
                repeat_customer_count = EXCLUDED.repeat_customer_count,
                repeat_customer_rate = EXCLUDED.repeat_customer_rate,
                reputation_score = EXCLUDED.reputation_score,
                reputation_tier = EXCLUDED.reputation_tier,
                last_execution_at = EXCLUDED.last_execution_at,
                last_updated_at = EXCLUDED.last_updated_at
        """, (
            agent_id,
            metrics['total_executions'], metrics['successful_executions'],
            metrics['failed_executions'], metrics['timeout_executions'],
            metrics['success_rate_overall'], metrics['success_rate_30d'], metrics['success_rate_7d'],
            metrics['avg_execution_time_ms'], metrics['median_execution_time_ms'], metrics['p95_execution_time_ms'],
            metrics['avg_cost_accuracy'], metrics['total_revenue_usd'],
            metrics['avg_quality_rating'], metrics['total_quality_ratings'],
            metrics['unique_requesters'], metrics['repeat_customer_count'], metrics['repeat_customer_rate'],
            reputation_score, reputation_tier,
            first_exec, last_exec, now
        ))
        
        conn.commit()
    
    def _record_reputation_history(
        self, cur, conn, agent_id: str,
        reputation_score: Decimal, total_executions: int, success_rate: float
    ):
        """Record reputation change in history table"""
        cur.execute("""
            INSERT INTO agent_reputation_history (
                agent_id, reputation_score, total_executions, success_rate,
                change_reason, recorded_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            agent_id, reputation_score, total_executions, success_rate,
            'periodic_recalculation', datetime.now()
        ))
        conn.commit()
    
    def calculate_all_agents(self, min_executions: int = 10) -> Dict:
        """
        Calculate reputation for all agents with sufficient execution history
        Returns summary of updates
        """
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        try:
            # Get agents with enough executions
            cur.execute("""
                SELECT executing_agent_id, COUNT(*)
                FROM agent_executions
                WHERE status IN ('completed', 'failed', 'timeout')
                GROUP BY executing_agent_id
                HAVING COUNT(*) >= %s
            """, (min_executions,))
            
            agents = cur.fetchall()
            
            results = {
                "total_agents": len(agents),
                "updated": 0,
                "failed": 0,
                "details": []
            }
            
            for agent_id, exec_count in agents:
                try:
                    result = self.calculate_for_agent(str(agent_id))
                    results["updated"] += 1
                    results["details"].append({
                        "agent_id": str(agent_id),
                        "reputation_score": result.get("reputation_score"),
                        "reputation_tier": result.get("reputation_tier")
                    })
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "agent_id": str(agent_id),
                        "error": str(e)
                    })
            
            return results
            
        finally:
            cur.close()
            conn.close()


# CLI interface for manual recalculation
if __name__ == "__main__":
    import sys
    import json
    
    DATABASE_URL = "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway"
    
    calculator = ReputationCalculator(DATABASE_URL)
    
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        # Recalculate all agents
        print("Recalculating reputation for all agents...")
        results = calculator.calculate_all_agents()
        print(json.dumps(results, indent=2))
    elif len(sys.argv) > 1:
        # Recalculate specific agent
        agent_id = sys.argv[1]
        print(f"Calculating reputation for agent {agent_id}...")
        result = calculator.calculate_for_agent(agent_id)
        print(json.dumps(result, indent=2))
    else:
        print("Usage:")
        print("  python reputation_calculator.py <agent_id>  # Calculate for one agent")
        print("  python reputation_calculator.py all         # Calculate for all agents")
