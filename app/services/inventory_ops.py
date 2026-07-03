import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.database import db
from app.models.business import Product, Sale, Inventory
from app.models.system import Alert

class InventoryOps:
    @staticmethod
    def calculate_optimization_metrics(product_id, lead_time_days=5, max_lead_time_days=10, ordering_cost=15.0, holding_rate=0.18):
        """
        Retrieves sales history, calculates average & max daily sales,
        and computes Safety Stock, Reorder Point, and EOQ.
        Updates the Inventory record and triggers alerts if necessary.
        """
        product = Product.query.get(product_id)
        if not product or product.price <= 0:
            return None
            
        sales = Sale.query.filter_by(product_id=product_id).all()
        
        # If no sales history, set sensible default values based on quantity
        if not sales or len(sales) < 5:
            inv = Inventory.query.filter_by(product_id=product_id).first()
            if not inv:
                inv = Inventory(product_id=product_id)
                db.session.add(inv)
            
            # Simple heuristic defaults
            inv.safety_stock = 10.0
            inv.reorder_point = 25.0
            inv.eoq = 50.0
            inv.stock_status = "In Stock" if product.quantity > 10 else ("Low Stock" if product.quantity > 0 else "Out of Stock")
            db.session.commit()
            return inv
            
        # Calculate daily quantities sold
        df_sales = pd.DataFrame([{'date': s.date, 'qty': s.quantity_sold} for s in sales])
        df_daily = df_sales.groupby('date').sum()
        
        # Ingest daily rates
        avg_daily_sales = df_daily['qty'].mean()
        max_daily_sales = df_daily['qty'].max()
        
        # 1. Safety Stock = (Max Daily Sales * Max Lead Time) - (Avg Daily Sales * Avg Lead Time)
        safety_stock = (max_daily_sales * max_lead_time_days) - (avg_daily_sales * lead_time_days)
        safety_stock = max(1.0, float(safety_stock))
        
        # 2. Reorder Point = (Avg Daily Sales * Avg Lead Time) + Safety Stock
        reorder_point = (avg_daily_sales * lead_time_days) + safety_stock
        reorder_point = float(reorder_point)
        
        # 3. Annual Demand (D) = Avg Daily Sales * 365
        annual_demand = avg_daily_sales * 365.0
        
        # 4. Holding Cost per unit per year (H) = holding_rate * unit_price
        holding_cost = holding_rate * product.price
        
        # 5. EOQ = sqrt((2 * D * S) / H)
        eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        eoq = max(5.0, float(eoq))
        
        # Determine Stock Status
        current_stock = product.quantity
        status = "In Stock"
        
        if current_stock <= 0:
            status = "Out of Stock"
        elif current_stock <= safety_stock:
            status = "Critical Low"
        elif current_stock <= reorder_point:
            status = "Low Stock"
        elif current_stock >= reorder_point * 3.5:
            status = "Overstock"
            
        # Save or update Inventory optimization stats
        inv = Inventory.query.filter_by(product_id=product_id).first()
        if not inv:
            inv = Inventory(product_id=product_id)
            db.session.add(inv)
            
        inv.safety_stock = round(safety_stock, 1)
        inv.reorder_point = round(reorder_point, 1)
        inv.eoq = round(eoq, 1)
        inv.stock_status = status
        db.session.commit()
        
        # Check and trigger low stock alerts
        InventoryOps.trigger_stock_status_alerts(product, inv)
        
        return inv

    @classmethod
    def trigger_stock_status_alerts(cls, product, inv):
        """Creates notifications in the Alert table based on safety stock and reorder point checks."""
        today_date = datetime.utcnow().date()
        today_start = datetime(today_date.year, today_date.month, today_date.day)
        
        if inv.stock_status in ["Critical Low", "Low Stock", "Out of Stock"]:
            # Check if alert already exists for today
            existing = Alert.query.filter(
                Alert.product_id == product.id,
                Alert.type == "Low Stock",
                Alert.created_at >= today_start
            ).first()
            
            if not existing:
                msg = f"Alert: Product '{product.name}' (SKU: {product.sku}) status is '{inv.stock_status}'. Current Qty: {product.quantity}. Reorder Point: {inv.reorder_point}. Safety Stock: {inv.safety_stock}. Suggested order size (EOQ): {inv.eoq}."
                alert = Alert(
                    product_id=product.id,
                    type="Low Stock",
                    message=msg
                )
                db.session.add(alert)
                db.session.commit()
                
        elif inv.stock_status == "Overstock":
            existing = Alert.query.filter(
                Alert.product_id == product.id,
                Alert.type == "Overstock",
                Alert.created_at >= today_start
            ).first()
            
            if not existing:
                msg = f"Warning: Overstock detected for '{product.name}' (SKU: {product.sku}). Current Qty: {product.quantity}. Reorder Point: {inv.reorder_point}. Holding capital may be constrained."
                alert = Alert(
                    product_id=product.id,
                    type="Overstock",
                    message=msg
                )
                db.session.add(alert)
                db.session.commit()
