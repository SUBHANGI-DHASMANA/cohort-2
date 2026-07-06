import csv
import random
from datetime import datetime, timedelta
import math
import os

def generate_data(target_dir=".", num_transactions=1000000, num_skus=5000, num_stores=50):
    print(f"Starting synthetic retail data generation in: {os.path.abspath(target_dir)}")
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. Generate Stores
    stores_path = os.path.join(target_dir, "stores.csv")
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    cities = {
        "Northeast": ["New York", "Boston", "Philadelphia", "Pittsburgh", "Buffalo"],
        "Southeast": ["Atlanta", "Miami", "Charlotte", "Nashville", "Orlando"],
        "Midwest": ["Chicago", "Detroit", "Minneapolis", "St. Louis", "Cleveland"],
        "Southwest": ["Houston", "Dallas", "Phoenix", "Austin", "El Paso"],
        "West": ["Los Angeles", "San Francisco", "Seattle", "Denver", "Portland"]
    }
    
    stores = []
    with open(stores_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["store_id", "city", "region"])
        for store_id in range(1, num_stores + 1):
            region = random.choice(regions)
            city = random.choice(cities[region])
            writer.writerow([store_id, city, region])
            stores.append({"store_id": store_id, "region": region})
    print(f"Generated {num_stores} stores at: {stores_path}")

    # 2. Generate Inventory / Product Catalog
    inventory_path = os.path.join(target_dir, "inventory.csv")
    categories = ["Apparel", "Electronics", "Home & Kitchen", "Beauty", "Sports"]
    cat_price_ranges = {
        "Apparel": (15, 120),
        "Electronics": (50, 800),
        "Home & Kitchen": (10, 250),
        "Beauty": (5, 90),
        "Sports": (20, 400)
    }
    
    skus = []
    with open(inventory_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sku_id", "category", "cost", "price", "current_stock", "reorder_point", "first_stock_date"])
        
        start_date = datetime(2025, 12, 1) # Start stocking from late 2025
        for sku_id in range(1001, 1001 + num_skus):
            category = random.choice(categories)
            min_p, max_p = cat_price_ranges[category]
            price = round(random.uniform(min_p, max_p), 2)
            # Cost is typically 40% to 70% of price
            cost = round(price * random.uniform(0.4, 0.7), 2)
            
            # Create some overstocked/slow items deliberately for the clustering exercise
            # 15% of items are high-stock, low-velocity "at-risk" items
            is_overstocked = random.random() < 0.15
            if is_overstocked:
                current_stock = random.randint(500, 2000)
                reorder_point = random.randint(50, 150)
            else:
                current_stock = random.randint(10, 400)
                reorder_point = random.randint(20, 100)
                
            first_stock_days = random.randint(0, 150)
            first_stock_date = (start_date + timedelta(days=first_stock_days)).strftime("%Y-%m-%d")
            
            writer.writerow([sku_id, category, cost, price, current_stock, reorder_point, first_stock_date])
            
            # Base velocity: units sold per day when active. Overstocked items have lower velocity
            base_velocity = random.uniform(0.01, 0.1) if is_overstocked else random.uniform(0.1, 3.0)
            skus.append({
                "sku_id": sku_id,
                "category": category,
                "price": price,
                "cost": cost,
                "base_velocity": base_velocity,
                "is_overstocked": is_overstocked
            })
    print(f"Generated {num_skus} SKUs at: {inventory_path}")

    # 3. Generate Transactions
    transactions_path = os.path.join(target_dir, "transactions.csv")
    
    # Simulation config
    end_sim_date = datetime(2026, 6, 20)
    sim_days = 180
    start_sim_date = end_sim_date - timedelta(days=sim_days)
    
    # Store sales weight (some stores are busy, some are slow)
    store_weights = [random.uniform(0.5, 2.0) for _ in range(num_stores)]
    
    # We will write in chunks to be memory efficient and extremely fast
    print(f"Generating {num_transactions} transactions... (this might take a few seconds)")
    
    with open(transactions_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "date", "sku_id", "store_id", "quantity", "price", "discount"])
        
        tx_id = 1
        chunk_size = 50000
        rows = []
        
        while tx_id <= num_transactions:
            # Random date within the 180 days
            days_offset = random.randint(0, sim_days)
            tx_date = start_sim_date + timedelta(days=days_offset)
            date_str = tx_date.strftime("%Y-%m-%d")
            
            # Pick store and SKU based on weight
            store_idx = random.randint(0, num_stores - 1)
            store_id = store_idx + 1
            store_w = store_weights[store_idx]
            
            sku = random.choice(skus)
            # Probability of selling this item on this day
            # Weekends have higher sales
            day_multiplier = 1.4 if tx_date.weekday() >= 5 else 0.8
            prob = sku["base_velocity"] * store_w * day_multiplier
            
            # Determine if a transaction occurs
            if random.random() < min(prob, 0.95):
                quantity = random.randint(1, 3)
                if sku["is_overstocked"] and random.random() < 0.2:
                    # Give a random promotion discount for overstocked items
                    discount = round(random.choice([0.10, 0.15, 0.20, 0.25]), 2)
                else:
                    discount = 0.0
                
                price_sold = round(sku["price"] * (1 - discount), 2)
                
                rows.append([tx_id, date_str, sku["sku_id"], store_id, quantity, price_sold, discount])
                tx_id += 1
                
                if len(rows) >= chunk_size:
                    writer.writerows(rows)
                    rows = []
                    # Progress indicator
                    pct = round((tx_id / num_transactions) * 100)
                    print(f"Progress: {pct}% ({tx_id} transactions written)")
                    
        if rows:
            writer.writerows(rows)
            
    print(f"Generated {tx_id - 1} transactions at: {transactions_path}")
    print("Data generation complete!")

if __name__ == "__main__":
    # Generate data in current directory
    generate_data(".", num_transactions=1000000, num_skus=5000, num_stores=50)
