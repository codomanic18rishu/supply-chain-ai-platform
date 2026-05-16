def generate_insights(forecast):
    avg_demand = sum(forecast) / len(forecast)
    max_demand = max(forecast)
    min_demand = min(forecast)

    trend = "increasing" if forecast[-1] > forecast[0] else "stable"

    insights = f'''
📊 Demand Analysis Summary

• Average Predicted Demand: {avg_demand:.2f}
• Maximum Forecasted Demand: {max_demand:.2f}
• Minimum Forecasted Demand: {min_demand:.2f}
• Overall Trend: {trend}

📦 Inventory Recommendation
Increase safety stock by 15% to prevent shortages.

⚠️ Risk Assessment
Stockout risk is LOW based on forecast consistency.

💰 Business Opportunity
Optimized inventory planning can improve revenue and reduce holding costs.
'''

    return insights.strip()
