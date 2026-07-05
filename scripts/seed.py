import os
import sys
import random
from datetime import datetime, timedelta, time
import math

# Add root folder to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models.auth import User
from app.models.business import (
    Product, Sale, Inventory, Brand, Supplier, Warehouse, Customer,
    SalesItem, PurchaseOrder, PurchaseItem, ProductReturn, Discount, Coupon, Payment, Invoice
)
from app.models.system import Alert, SystemLog
from app.models.forecast import ModelVersion, TrainingHistory
from app.models.hr import Employee, Attendance

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

        # 3. Seed Enterprise Metadata (Brands, Suppliers, Warehouses)
        print("Seeding Brands...")
        brands = [
            Brand(name="AudioTech", manufacturer="AudioTech Corp", description="High-end consumer audio devices"),
            Brand(name="ApexWear", manufacturer="Apex Wearables Ltd", description="Fitness and wearable electronics"),
            Brand(name="EcoStride", manufacturer="EcoStride Footwear LLC", description="Sustainable performance shoes"),
            Brand(name="Heritage Leather", manufacturer="Heritage Garments", description="Premium leather apparel"),
            Brand(name="Caffeinate", manufacturer="Caffeinate Appliances", description="Kitchen and coffee machinery")
        ]
        for b in brands:
            db.session.add(b)
            
        print("Seeding Suppliers...")
        suppliers = [
            Supplier(name="Global Electronics Distributors", email="orders@globaldist.com", phone="1-800-555-0199", address="456 Silicon Alley, CA", rating=4.8),
            Supplier(name="Apparel Source Inc", email="sales@apparelsource.com", phone="1-800-555-0144", address="789 Fashion Ave, NY", rating=4.5),
            Supplier(name="EcoShoes Manufacturing", email="support@ecoshoes.com", phone="1-800-555-0133", address="12 Industrial Pkwy, OR", rating=4.7)
        ]
        for s in suppliers:
            db.session.add(s)
            
        print("Seeding Warehouses...")
        warehouses = [
            Warehouse(name="Central Distribution Hub", location="100 Logistics Blvd, OH", capacity_sqft=50000),
            Warehouse(name="West Coast Depot", location="200 Pacific Way, CA", capacity_sqft=25000),
            Warehouse(name="East Coast Fulfillment", location="300 Atlantic Dr, NJ", capacity_sqft=30000)
        ]
        for w in warehouses:
            db.session.add(w)
            
        db.session.commit()

        # 4. Seed Products
        print("Seeding Products...")
        products_data = [
            {"name": "Wireless Headset HD", "sku": "SKU-HEADSET-101", "category": "Electronics", "price": 89.99, "quantity": 150, "description": "High-fidelity wireless Bluetooth headphones with active noise cancellation.", "brand_id": 1, "supplier_id": 1, "warehouse_id": 1},
            {"name": "Titanium Smartwatch Pro", "sku": "SKU-WATCH-202", "category": "Electronics", "price": 249.99, "quantity": 85, "description": "Premium smartwatch with fitness tracker, heart rate monitor, and built-in GPS.", "brand_id": 2, "supplier_id": 1, "warehouse_id": 1},
            {"name": "Ultralight Running Shoes", "sku": "SKU-SHOES-303", "category": "Footwear", "price": 120.00, "quantity": 220, "description": "Comfortable, responsive, and breathable athletic running shoes for all terrains.", "brand_id": 3, "supplier_id": 3, "warehouse_id": 2},
            {"name": "Classic Leather Jacket", "sku": "SKU-JACKET-404", "category": "Apparel", "price": 199.99, "quantity": 40, "description": "Genuine vintage-style cowhide leather jacket with zip closure and satin lining.", "brand_id": 4, "supplier_id": 2, "warehouse_id": 3},
            {"name": "Automatic Espresso Maker", "sku": "SKU-COFFEE-505", "category": "Appliances", "price": 349.99, "quantity": 110, "description": "15-bar pump espresso machine with milk frother and programmable brewing profiles.", "brand_id": 5, "supplier_id": 1, "warehouse_id": 1}
        ]
        
        products = []
        for p_data in products_data:
            prod = Product(
                name=p_data["name"],
                sku=p_data["sku"],
                category=p_data["category"],
                price=p_data["price"],
                quantity=p_data["quantity"],
                description=p_data["description"],
                brand_id=p_data["brand_id"],
                supplier_id=p_data["supplier_id"],
                warehouse_id=p_data["warehouse_id"],
                barcode=f"BARCODE-{p_data['sku']}",
                unit="pcs"
            )
            db.session.add(prod)
            products.append(prod)
            
        db.session.commit()
        print(f"Products seeded successfully: {[p.name for p in products]}")

        # 5. Seed initial Inventory optimization records
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

        # 6. Seed Customers
        print("Seeding Customers...")
        customers = [
            Customer(name="John Doe", email="john.doe@gmail.com", phone="555-0101", address="123 Maple St, OH", membership_tier="Gold", loyalty_points=1200),
            Customer(name="Jane Smith", email="jane.smith@yahoo.com", phone="555-0102", address="456 Oak Ave, CA", membership_tier="Silver", loyalty_points=650),
            Customer(name="Robert Johnson", email="robert.j@outlook.com", phone="555-0103", address="789 Pine Rd, NY", membership_tier="Regular", loyalty_points=100)
        ]
        for c in customers:
            db.session.add(c)
        db.session.commit()

        # 7. Seed HR Employees & Attendance
        print("Seeding HR Employees...")
        employees = [
            Employee(
                employee_id="EMP001",
                name="Alice Miller",
                department="Management",
                designation="Inventory Manager",
                salary=45000.0,
                joining_date=datetime.utcnow().date() - timedelta(days=365),
                status="Active"
            ),
            Employee(
                employee_id="EMP002",
                name="Bob Davis",
                department="Logistics",
                designation="Warehouse Staff",
                salary=32000.0,
                joining_date=datetime.utcnow().date() - timedelta(days=200),
                status="Active"
            )
        ]
        for emp in employees:
            db.session.add(emp)
        db.session.commit()

        print("Seeding Attendance records...")
        for emp in employees:
            # Seed 10 days of attendance
            for i in range(10):
                day = datetime.utcnow().date() - timedelta(days=i)
                att = Attendance(
                    employee_id=emp.id,
                    date=day,
                    check_in=datetime.combine(day, time(9, 0)),
                    check_out=datetime.combine(day, time(17, 0)),
                    working_hours=8.0
                )
                db.session.add(att)
        db.session.commit()

        # 8. Seed Discounts & Coupons
        print("Seeding Discounts & Coupons...")
        discounts = [
            Discount(name="Summer Clearance", discount_percent=15.0, active=True),
            Discount(name="Black Friday Preview", discount_percent=25.0, active=True)
        ]
        for d in discounts:
            db.session.add(d)

        coupons = [
            Coupon(code="WELCOME10", discount_amount=10.0, expiry_date=datetime.utcnow().date() + timedelta(days=90)),
            Coupon(code="SAVE20", discount_amount=20.0, expiry_date=datetime.utcnow().date() + timedelta(days=30))
        ]
        for cp in coupons:
            db.session.add(cp)
        db.session.commit()

        # 9. Seed Historical Sales, SalesItems, Payments, Invoices
        print("Seeding historical sales records (with trends & Phase 2 entities)...")
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        profiles = {
            "SKU-HEADSET-101": {"base": 12, "weekly_season": 5, "trend_slope": 0.015, "annual_period": 365},
            "SKU-WATCH-202": {"base": 8, "weekly_season": 3, "trend_slope": 0.008, "annual_period": 365},
            "SKU-SHOES-303": {"base": 18, "weekly_season": 7, "trend_slope": -0.01, "annual_period": 365},
            "SKU-JACKET-404": {"base": 5, "weekly_season": 1.5, "trend_slope": 0.005, "annual_period": 365},
            "SKU-COFFEE-505": {"base": 10, "weekly_season": 4, "trend_slope": 0.02, "annual_period": 365}
        }
        
        current_day = start_date
        while current_day < end_date:
            day_of_week = current_day.weekday()
            day_index = (current_day - start_date).days
            
            for prod in products:
                prof = profiles[prod.sku]
                demand = prof["base"]
                
                if day_of_week in [4, 5, 6]:
                    demand += prof["weekly_season"] * (1.2 if day_of_week == 5 else 0.8)
                else:
                    demand -= (prof["weekly_season"] / 2)
                    
                demand += prof["trend_slope"] * day_index
                demand += random.normalvariate(0, 1.5)
                quantity_sold = max(0, int(round(demand)))
                
                if quantity_sold > 0:
                    revenue = quantity_sold * prod.price
                    sale = Sale(
                        date=current_day,
                        product_id=prod.id,
                        quantity_sold=quantity_sold,
                        price=prod.price,
                        revenue=round(revenue, 2),
                        customer_id=random.choice([None, 1, 2, 3])
                    )
                    db.session.add(sale)
                    db.session.flush() # Flush to get sale.id

                    # Seed SalesItem
                    s_item = SalesItem(
                        sale_id=sale.id,
                        product_id=prod.id,
                        quantity=quantity_sold,
                        price=prod.price
                    )
                    db.session.add(s_item)

                    # Seed Payment
                    payment = Payment(
                        sale_id=sale.id,
                        payment_method=random.choice(['Cash', 'Card', 'UPI']),
                        amount=round(revenue, 2)
                    )
                    db.session.add(payment)

                    # Seed Invoice
                    invoice = Invoice(
                        sale_id=sale.id,
                        invoice_number=f"INV-{sale.id:06d}",
                        issue_date=current_day,
                        total_amount=round(revenue, 2)
                    )
                    db.session.add(invoice)

                    # Seed dynamic returns (3% chance)
                    if random.random() < 0.03:
                        ret = ProductReturn(
                            sale_id=sale.id,
                            product_id=prod.id,
                            quantity=1,
                            reason="Wrong size/color",
                            return_date=current_day + timedelta(days=2)
                        )
                        db.session.add(ret)
            
            current_day += timedelta(days=1)
        db.session.commit()

        # 10. Seed Purchase Orders & Purchase Items
        print("Seeding Purchase Orders...")
        for prod in products:
            po = PurchaseOrder(
                product_id=prod.id,
                supplier_id=prod.supplier_id,
                warehouse_id=prod.warehouse_id,
                quantity=100,
                order_date=datetime.utcnow().date() - timedelta(days=15),
                delivery_date=datetime.utcnow().date() - timedelta(days=12),
                status="Delivered",
                total_amount=round(100 * prod.price * 0.6, 2), # Wholesaler price is 60% of retail
                payment_status="Paid"
            )
            db.session.add(po)
            db.session.flush()

            po_item = PurchaseItem(
                purchase_order_id=po.id,
                product_id=prod.id,
                quantity=100,
                price=round(prod.price * 0.6, 2)
            )
            db.session.add(po_item)
        db.session.commit()

        # 11. Seed Alerts, System Logs & AI Model Tracking logs
        print("Seeding System logs & AI models history...")
        sys_log1 = SystemLog(type="Database", message="Database migrations applied successfully for Phase 2 schema updates.")
        sys_log2 = SystemLog(type="Security", message="Admin login session initialized from local IP: 127.0.0.1.")
        db.session.add(sys_log1)
        db.session.add(sys_log2)

        for prod in products:
            mv = ModelVersion(
                product_id=prod.id,
                model_type="LSTM",
                version_tag="v1.0",
                file_path=f"models/{prod.sku}_lstm_v1.h5"
            )
            th = TrainingHistory(
                product_id=prod.id,
                model_type="LSTM",
                accuracy_score=round(random.uniform(0.85, 0.94), 3),
                hyperparameters='{"epochs": 50, "batch_size": 16, "learning_rate": 0.001}'
            )
            db.session.add(mv)
            db.session.add(th)
            
        alert = Alert(
            product_id=products[3].id,
            type="Low Stock",
            message=f"Product '{products[3].name}' is below safety stock level. Current quantity: {products[3].quantity}."
        )
        db.session.add(alert)
        db.session.commit()

        print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
