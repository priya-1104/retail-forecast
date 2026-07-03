import os
import sys
import random
from datetime import datetime, timedelta
import math

# Add root folder to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models.auth import User
from app.models.business import Product, Sale, Inventory
from app.models.system import Alert

def seed_database():
    app = create_app()
    with app.app_context():
        print("Initializing database seeding...")
        
        # 1. Clear database (optional, but good for resetting in dev)
        db.drop_all()
        db.create_all()
        
        # 2. Seed Users
        print("Seeding Users...")
        users_to_seed = [
            {"username": "admin", "email": "admin@demandforecast.com", "password": "AdminPass123!", "role": "Admin"},
            {"username": "manager", "email": "manager@demandforecast.com", "password": "ManagerPass123!", "role": "Manager"},
            {"username": "staff", "email": "staff@demandforecast.com", "password": "StaffPass123!", "role": "Staff"}
        ]
        
        for u_data in users_to_seed:
            user = User(username=u_data["username"], email=u_data["email"], role=u_data["role"])
            user.set_password(u_data["password"])
            db.session.add(user)
            
        db.session.commit()
        print(f"Users seeded successfully: {[u['username'] for u in users_to_seed]}")

        # 3. Seed Products
        print("Seeding Products...")
        products_data = [
            {"name": "Wireless Headset HD", "sku": "SKU-HEADSET-101", "category": "Electronics", "price": 89.99, "quantity": 150, "description": "High-fidelity wireless Bluetooth headphones with active noise cancellation."},
            {"name": "Titanium Smartwatch Pro", "sku": "SKU-WATCH-202", "category": "Electronics", "price": 249.99, "quantity": 85, "description": "Premium smartwatch with fitness tracker, heart rate monitor, and built-in GPS."},
            {"name": "Ultralight Running Shoes", "sku": "SKU-SHOES-303", "category": "Footwear", "price": 120.00, "quantity": 220, "description": "Comfortable, responsive, and breathable athletic running shoes for all terrains."},
            {"name": "Classic Leather Jacket", "sku": "SKU-JACKET-404", "category": "Apparel", "price": 199.99, "quantity": 40, "description": "Genuine vintage-style cowhide leather jacket with zip closure and satin lining."},
            {"name": "Automatic Espresso Maker", "sku": "SKU-COFFEE-505", "category": "Appliances", "price": 349.99, "quantity": 110, "description": "15-bar pump espresso machine with milk frother and programmable brewing profiles."}
        ]
        
        products = []
        for p_data in products_data:
            prod = Product(
                name=p_data["name"],
                sku=p_data["sku"],
                category=p_data["category"],
                price=p_data["price"],
                quantity=p_data["quantity"],
                description=p_data["description"]
            )
            db.session.add(prod)
            products.append(prod)
            
        db.session.commit()
        print(f"Products seeded successfully: {[p.name for p in products]}")

        # 4. Seed Inventory optimization records (initial calculations set to 0, will be updated by services)
        print("Seeding initial Inventory metrics...")
        for prod in products:
            inv = Inventory(
                product_id=prod.id,
                safety_stock=10.0,
                reorder_point=25.0,
                eoq=50.0,
                stock_status="In Stock"
            )
            db.session.add(inv)
        db.session.commit()

        # 5. Seed Historical Sales
        # We will generate daily sales records for the past 730 days (2 years)
        print("Seeding 730 days of historical sales records (with trend & seasonality)...")
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=730)
        
        # Product demand profiles to simulate realistic sales curves
        profiles = {
            "SKU-HEADSET-101": {"base": 12, "weekly_season": 5, "trend_slope": 0.015, "annual_period": 365},
            "SKU-WATCH-202": {"base": 8, "weekly_season": 3, "trend_slope": 0.008, "annual_period": 365},
            "SKU-SHOES-303": {"base": 18, "weekly_season": 7, "trend_slope": -0.01, "annual_period": 365}, # slight decline
            "SKU-JACKET-404": {"base": 5, "weekly_season": 1.5, "trend_slope": 0.005, "annual_period": 365, "seasonal_amp": 4}, # highly seasonal (winter peak)
            "SKU-COFFEE-505": {"base": 10, "weekly_season": 4, "trend_slope": 0.02, "annual_period": 365} # rising trend
        }
        
        sales_records = []
        current_day = start_date
        
        while current_day < end_date:
            day_of_week = current_day.weekday()  # 0 (Monday) to 6 (Sunday)
            day_index = (current_day - start_date).days
            
            for prod in products:
                prof = profiles[prod.sku]
                
                # Base demand
                demand = prof["base"]
                
                # Add weekly seasonality (more sales on Friday=4, Saturday=5, Sunday=6)
                if day_of_week in [4, 5, 6]:
                    demand += prof["weekly_season"] * (1.2 if day_of_week == 5 else 0.8)
                else:
                    demand -= (prof["weekly_season"] / 2)
                
                # Add long term linear trend
                demand += prof["trend_slope"] * day_index
                
                # Add annual/seasonal sine wave (winter apparel peak for jacket, general electronics peak)
                if prod.sku == "SKU-JACKET-404":
                    # Peak in winter (day_index close to day 180 or day 360 depending on start)
                    # Let's align with winter months (Dec/Jan/Feb)
                    month = current_day.month
                    if month in [11, 12, 1]:
                        demand += prof.get("seasonal_amp", 4)
                    elif month in [5, 6, 7]:
                        demand -= prof.get("seasonal_amp", 4)
                else:
                    # Generic annual seasonality
                    demand += 3 * math.sin(2 * math.pi * day_index / prof["annual_period"])
                
                # Add random noise
                demand += random.normalvariate(0, 2)
                
                # Floor value at 0
                quantity_sold = max(0, int(round(demand)))
                
                # Write sales record
                if quantity_sold > 0:
                    revenue = quantity_sold * prod.price
                    sale = Sale(
                        date=current_day,
                        product_id=prod.id,
                        quantity_sold=quantity_sold,
                        price=prod.price,
                        revenue=round(revenue, 2)
                    )
                    sales_records.append(sale)
            
            current_day += timedelta(days=1)
            
        print(f"Adding {len(sales_records)} sales records to session...")
        
        # Batch insert for speed
        db.session.bulk_save_objects(sales_records)
        db.session.commit()
        print("Historical sales records seeded successfully.")
        
        # 6. Seed one initial Low Stock alert as check
        print("Seeding initial warning alert...")
        alert = Alert(
            product_id=products[3].id, # Leather jacket
            type="Low Stock",
            message=f"Product '{products[3].name}' is below safety stock level. Current quantity: {products[3].quantity}. Safety Stock: 15.0."
        )
        db.session.add(alert)
        db.session.commit()
        print("Alerts seeded successfully.")
        print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
