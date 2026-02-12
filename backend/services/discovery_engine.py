"""
Discovery Engine - Analyzes transaction patterns to suggest collaborations

This is the core intelligence that makes agents WANT to use the platform
"""
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

from models.agent import Agent
from models.transaction import Transaction, TransactionStatus
from models.instrument import Instrument
from models.collaboration import AgentSuggestion


class DiscoveryEngine:
    """
    Analyzes agent performance and transaction patterns to discover:
    1. Which agents are frequently bought together (co-purchase analysis)
    2. Which combinations perform better than solo (value multipliers)
    3. Tag-based groupings (e.g., all SIBYSI agents)
    4. Performance correlation (agents whose customers overlap)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_co_purchases(self, agent_id: str, lookback_days: int = 90):
        """
        Find agents frequently purchased by the same buyers as this agent
        
        Returns: List of (agent_id, co_purchase_rate, synergy_score)
        """
        # Get all buyers who purchased from this agent
        agent_buyers = self.db.query(Transaction.buyer_agent_id).filter(
            and_(
                Transaction.seller_agent_id == agent_id,
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.created_at >= datetime.utcnow() - timedelta(days=lookback_days)
            )
        ).distinct().all()
        
        buyer_ids = [b[0] for b in agent_buyers]
        
        if not buyer_ids:
            return []
        
        # Find what else these buyers purchased
        other_purchases = self.db.query(
            Transaction.seller_agent_id,
            func.count(Transaction.buyer_agent_id).label('overlap_count')
        ).filter(
            and_(
                Transaction.buyer_agent_id.in_(buyer_ids),
                Transaction.seller_agent_id != agent_id,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).group_by(Transaction.seller_agent_id).all()
        
        total_buyers = len(buyer_ids)
        
        # Calculate co-purchase rates and synergy scores
        co_purchases = []
        for seller_id, overlap_count in other_purchases:
            co_purchase_rate = overlap_count / total_buyers
            
            # Only consider significant overlap (>10%)
            if co_purchase_rate < 0.1:
                continue
            
            # Calculate synergy score (0-100)
            synergy_score = min(100, co_purchase_rate * 100 * 1.5)
            
            co_purchases.append({
                'agent_id': str(seller_id),
                'co_purchase_rate': co_purchase_rate,
                'synergy_score': synergy_score,
                'shared_buyers': overlap_count,
                'total_buyers': total_buyers
            })
        
        # Sort by synergy score descending
        co_purchases.sort(key=lambda x: x['synergy_score'], reverse=True)
        
        return co_purchases[:10]  # Top 10
    
    def calculate_value_multiplier(self, agent_ids: list):
        """
        Compare earnings as instrument vs solo
        
        Returns: {
            'solo_total': sum of individual earnings,
            'instrument_projected': projected combined earnings,
            'multiplier': instrument / solo ratio
        }
        """
        # Get solo earnings for each agent (last 90 days)
        solo_earnings = {}
        for agent_id in agent_ids:
            earnings = self.db.query(func.sum(Transaction.seller_payout_usd)).filter(
                and_(
                    Transaction.seller_agent_id == agent_id,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.created_at >= datetime.utcnow() - timedelta(days=90)
                )
            ).scalar() or 0
            
            solo_earnings[agent_id] = earnings
        
        solo_total = sum(solo_earnings.values())
        
        # Look for existing similar instruments to project
        similar_instruments = self.db.query(Instrument).filter(
            Instrument.member_count == len(agent_ids),
            Instrument.status == 'active'
        ).all()
        
        if similar_instruments:
            avg_instrument_revenue = statistics.mean([i.total_revenue_usd for i in similar_instruments])
            multiplier = avg_instrument_revenue / (solo_total / len(agent_ids)) if solo_total > 0 else 2.5
        else:
            # Default multiplier based on instrument size
            multiplier = 1.5 + (len(agent_ids) * 0.5)  # 2× for 2 agents, 2.5× for 3, etc.
        
        instrument_projected = solo_total * multiplier
        
        return {
            'solo_total': solo_total,
            'solo_monthly': solo_total / 3,  # 90 days / 3 = monthly
            'instrument_projected_monthly': instrument_projected / 3,
            'multiplier': multiplier,
            'per_agent_solo': {aid: earnings for aid, earnings in solo_earnings.items()}
        }
    
    def find_tag_based_opportunities(self, agent_id: str):
        """
        Find other agents with shared tags that could form instruments
        """
        # Get agent's tags
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent or not agent.capabilities:
            return []
        
        # Assuming capabilities contains tags
        agent_tags = agent.capabilities if isinstance(agent.capabilities, list) else []
        
        if not agent_tags:
            return []
        
        # Find agents with overlapping tags
        potential_partners = self.db.query(Agent).filter(
            and_(
                Agent.id != agent_id,
                Agent.is_active == True
            )
        ).all()
        
        tag_matches = []
        for partner in potential_partners:
            partner_tags = partner.capabilities if isinstance(partner.capabilities, list) else []
            overlap = set(agent_tags) & set(partner_tags)
            
            if overlap:
                tag_matches.append({
                    'agent_id': str(partner.id),
                    'agent_name': partner.name,
                    'shared_tags': list(overlap),
                    'tag_overlap_rate': len(overlap) / len(agent_tags),
                    'synergy_potential': len(overlap) * 20  # Simple scoring
                })
        
        tag_matches.sort(key=lambda x: x['synergy_potential'], reverse=True)
        
        return tag_matches[:5]
    
    def generate_suggestions_for_agent(self, agent_id: str):
        """
        Generate all types of suggestions for an agent
        
        This is what powers the discovery dashboard
        """
        suggestions = []
        
        # 1. Co-purchase analysis
        co_purchases = self.analyze_co_purchases(agent_id)
        for cp in co_purchases[:3]:  # Top 3
            # Calculate projected earnings
            value_data = self.calculate_value_multiplier([agent_id, cp['agent_id']])
            
            suggestion = AgentSuggestion(
                agent_id=agent_id,
                suggestion_type="collaboration",
                suggested_agent_ids=[cp['agent_id']],
                synergy_score=cp['synergy_score'],
                co_purchase_percentage=cp['co_purchase_rate'] * 100,
                earnings_multiplier_projected=value_data['multiplier'],
                evidence_data={
                    'co_purchase_data': cp,
                    'value_projection': value_data,
                    'message': f"{int(cp['co_purchase_rate']*100)}% of your buyers also purchase this agent. Projected {value_data['multiplier']:.1f}× earnings as instrument."
                }
            )
            
            self.db.add(suggestion)
            suggestions.append(suggestion)
        
        # 2. Tag-based opportunities
        tag_matches = self.find_tag_based_opportunities(agent_id)
        if tag_matches:
            best_match = tag_matches[0]
            
            value_data = self.calculate_value_multiplier([agent_id, best_match['agent_id']])
            
            suggestion = AgentSuggestion(
                agent_id=agent_id,
                suggestion_type="tag_group",
                suggested_agent_ids=[best_match['agent_id']],
                synergy_score=best_match['synergy_potential'],
                earnings_multiplier_projected=value_data['multiplier'],
                evidence_data={
                    'tag_data': best_match,
                    'value_projection': value_data,
                    'message': f"Shared tags: {', '.join(best_match['shared_tags'])}. Form tagged instrument group."
                }
            )
            
            self.db.add(suggestion)
            suggestions.append(suggestion)
        
        # 3. Look for open instruments agent could join
        # Get agent's performance tier
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        
        open_instruments = self.db.query(Instrument).filter(
            and_(
                Instrument.is_accepting_members == True,
                Instrument.status == 'active'
            )
        ).all()
        
        for instrument in open_instruments[:2]:  # Top 2
            # Calculate value of joining
            current_members = len(instrument.member_agent_ids)
            projected_multiplier = instrument.value_multiplier or 2.0
            
            suggestion = AgentSuggestion(
                agent_id=agent_id,
                suggestion_type="instrument_join",
                suggested_instrument_id=instrument.id,
                synergy_score=projected_multiplier * 20,
                earnings_multiplier_projected=projected_multiplier,
                similar_success_count=instrument.transaction_count,
                evidence_data={
                    'instrument_data': {
                        'name': instrument.name,
                        'members': current_members,
                        'revenue': instrument.total_revenue_usd,
                        'transactions': instrument.transaction_count,
                        'rating': instrument.rating_avg
                    },
                    'message': f"Join existing {current_members}-agent instrument. Current members earning {projected_multiplier:.1f}× solo average."
                }
            )
            
            self.db.add(suggestion)
            suggestions.append(suggestion)
        
        self.db.commit()
        
        return suggestions
    
    def get_dashboard_data_for_agent(self, agent_id: str):
        """
        Generate complete discovery dashboard data for an agent
        
        This is the UI that makes agents WANT to collaborate
        """
        # 1. Agent's current performance
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        
        agent_stats = {
            'solo_earnings_90d': self.db.query(func.sum(Transaction.seller_payout_usd)).filter(
                and_(
                    Transaction.seller_agent_id == agent_id,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.created_at >= datetime.utcnow() - timedelta(days=90)
                )
            ).scalar() or 0,
            'transaction_count': agent.transaction_count,
            'rating': agent.rating_avg,
            'success_rate': agent.success_rate
        }
        
        agent_stats['monthly_earnings'] = agent_stats['solo_earnings_90d'] / 3
        
        # 2. Market benchmarks
        all_agent_earnings = self.db.query(
            Transaction.seller_agent_id,
            func.sum(Transaction.seller_payout_usd).label('total')
        ).filter(
            and_(
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.created_at >= datetime.utcnow() - timedelta(days=90)
            )
        ).group_by(Transaction.seller_agent_id).all()
        
        if all_agent_earnings:
            earnings_list = [e[1] for e in all_agent_earnings]
            market_stats = {
                'median_solo_90d': statistics.median(earnings_list),
                'median_solo_monthly': statistics.median(earnings_list) / 3,
                'top_10_percent': statistics.quantiles(earnings_list, n=10)[-1] if len(earnings_list) >= 10 else max(earnings_list)
            }
        else:
            market_stats = {'median_solo_90d': 0, 'median_solo_monthly': 0, 'top_10_percent': 0}
        
        # 3. Instrument performance benchmarks
        instrument_earnings = self.db.query(
            func.avg(Instrument.total_revenue_usd),
            func.avg(Instrument.value_multiplier)
        ).filter(
            Instrument.status == 'active'
        ).first()
        
        instrument_stats = {
            'avg_instrument_revenue': instrument_earnings[0] or 0,
            'avg_value_multiplier': instrument_earnings[1] or 2.5
        }
        
        # 4. Active suggestions
        suggestions = self.db.query(AgentSuggestion).filter(
            and_(
                AgentSuggestion.agent_id == agent_id,
                AgentSuggestion.is_acted_on == False,
                or_(
                    AgentSuggestion.expires_at == None,
                    AgentSuggestion.expires_at > datetime.utcnow()
                )
            )
        ).order_by(AgentSuggestion.synergy_score.desc()).all()
        
        return {
            'your_performance': agent_stats,
            'market_benchmarks': market_stats,
            'instrument_benchmarks': instrument_stats,
            'opportunities': [s.to_dict() for s in suggestions],
            'potential_impact': {
                'current_monthly': agent_stats['monthly_earnings'],
                'instrument_projected_monthly': agent_stats['monthly_earnings'] * instrument_stats['avg_value_multiplier'],
                'potential_increase_pct': (instrument_stats['avg_value_multiplier'] - 1) * 100
            }
        }
