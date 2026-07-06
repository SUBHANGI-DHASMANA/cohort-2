import sys
import json
import time

def print_agent_step(step_name, description):
    print(f"\n[\033[94mGemini Agent Agentic Workflow - {step_name}\033[0m]")
    time.sleep(0.5)
    print(description)

def query_agent(prompt):
    print(f"\n\033[92mUser Prompt:\033[0m \"{prompt}\"")
    
    prompt_lower = prompt.lower()
    
    # 1. Intent Classification
    print_agent_step("1. Intent Classification & Parsing", 
        "Gemini analyzed the prompt context.\n"
        " - Intent: Retrieve markdown recommendations for slow-moving, high-stock products.\n"
        " - Filters: Category = 'Apparel', Location = 'Northeast'")
    
    # 2. BigQuery SQL Generation
    sql_query = """
    SELECT 
        i.sku_id, 
        i.category, 
        i.current_stock, 
        i.price, 
        i.cost,
        SUM(t.quantity) as total_units_sold,
        s.region
    FROM `gcp-project.retail_dataset.inventory` i
    JOIN `gcp-project.retail_dataset.transactions` t ON i.sku_id = t.sku_id
    JOIN `gcp-project.retail_dataset.stores` s ON t.store_id = s.store_id
    WHERE i.category = 'Apparel' AND s.region = 'Northeast'
    GROUP BY i.sku_id, i.category, i.current_stock, i.price, i.cost, s.region
    HAVING total_units_sold < 100 AND i.current_stock > 500
    """
    
    print_agent_step("2. BigQuery SQL Generation",
        f"Gemini auto-generated the optimized SQL query for BigQuery:\n\033[90m{sql_query}\033[0m")
    
    # 3. NVIDIA Acceleration Trigger
    print_agent_step("3. RAPIDS GPU Analytics Pipeline Triggered",
        "Data volumes exceed standard memory capacity. Gemini calls the cuDF and cuML analytics microservice on Google Kubernetes Engine (GKE) with L4 GPUs.\n"
        " -> Running cuDF.pandas geospatial-joining on 1,000,000+ transaction rows...\n"
        " -> Running cuML K-Means clustering to predict inventory risk...\n"
        " -> Compute Complete (Time-to-Insight: \033[93m0.86 seconds\033[0m vs \033[91m12.4 seconds on CPU\033[0m)")
    
    # 4. Result Aggregation and Optimization Logic
    # Let's mock the recommendations returned by the GPU pipeline
    recommendations = [
        {"sku_id": 1042, "category": "Apparel", "stock": 1250, "price": 89.99, "cost": 42.50, "velocity": "Very Low", "recommended_markdown": "25%", "estimated_lift": "+140%", "margin_recovered": "$11,250"},
        {"sku_id": 1109, "category": "Apparel", "stock": 840, "price": 45.00, "cost": 18.00, "velocity": "Low", "recommended_markdown": "15%", "estimated_lift": "+85%", "margin_recovered": "$5,670"},
        {"sku_id": 1281, "category": "Apparel", "stock": 620, "price": 120.00, "cost": 65.00, "velocity": "Very Low", "recommended_markdown": "30%", "estimated_lift": "+210%", "margin_recovered": "$14,880"},
    ]
    
    print_agent_step("4. Actionable Markdown Generation",
        "Gemini applied Price Elasticity curves generated via cuML Ridge Regression to compute optimal discounts:")
    
    print("\n" + "="*95)
    print(f"{'SKU ID':<10} | {'Category':<10} | {'Current Stock':<13} | {'Reg Price':<10} | {'Risk Tier':<10} | {'Markdown':<10} | {'Est. Sales Lift':<15} | {'Margin Recovered'}")
    print("-"*95)
    for r in recommendations:
        print(f"{r['sku_id']:<10} | {r['category']:<10} | {r['stock']:<13} | ${r['price']:<9} | {r['velocity']:<10} | {r['recommended_markdown']:<10} | {r['estimated_lift']:<15} | {r['margin_recovered']}")
    print("="*95)
    
    # 5. Natural Language Response & Proactive Action
    print_agent_step("5. Gemini Agent Response Summary",
        "\033[1mAgent Response:\033[0m\n"
        "\"I found 3 major Apparel items in the Northeast region that are overstocked with low velocity. "
        "By applying custom markdowns (ranging from 15% to 30%), we can clear this excess stock "
        "before season-end and recover an estimated \033[92m$31,800\033[0m in margin.\n\n"
        "Would you like me to draft the markdown upload file for BigQuery and email the regional store managers?\"")

if __name__ == "__main__":
    print("\033[95m========================================================\033[0m")
    print("\033[95m       FinPulse - Gemini Enterprise Agent Simulation      \033[0m")
    print("\033[95m========================================================\033[0m")
    
    default_prompt = "Which apparel products have high stock but low sales in the Northeast, and what markdown should I apply?"
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = default_prompt
        
    query_agent(prompt)
