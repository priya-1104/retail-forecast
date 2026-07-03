import os
import pandas as pd
from datetime import datetime
from app.database import db
from app.models.business import Product, Sale, Inventory
from app.services.auth_service import AuthService

class SalesService:
    @staticmethod
    def allowed_file(filename):
        """Returns True if the file extension is CSV or Excel."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

    @classmethod
    def import_sales_from_file(cls, file_path, user_id=None):
        """
        Parses CSV/Excel file and imports rows into the Sales table.
        Auto-creates products if the SKU is not found in the database.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            return False, f"Failed to read file format: {str(e)}"
            
        # Standardize column mappings (case-insensitive & stripping space)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Required columns check
        required_cols = {'date', 'product', 'quantity sold', 'price'}
        missing = required_cols - set(df.columns)
        if missing:
            return False, f"Missing required columns in header: {', '.join(missing)}"
            
        inserted_count = 0
        skipped_count = 0
        
        try:
            sales_objects = []
            
            for index, row in df.iterrows():
                # Parse date
                raw_date = row['date']
                try:
                    if isinstance(raw_date, datetime):
                        parsed_date = raw_date.date()
                    elif isinstance(raw_date, pd.Timestamp):
                        parsed_date = raw_date.to_pydatetime().date()
                    else:
                        # Try string parsing
                        parsed_date = pd.to_datetime(raw_date).date()
                except Exception:
                    skipped_count += 1
                    continue
                
                # Retrieve product SKU or Name
                prod_identifier = str(row['product']).strip()
                if not prod_identifier:
                    skipped_count += 1
                    continue
                    
                # Look up product by SKU or name
                product = Product.query.filter((Product.sku == prod_identifier) | (Product.name == prod_identifier)).first()
                
                if not product:
                    # Auto-create product with default values
                    sku_slug = f"SKU-{prod_identifier.replace(' ', '-').upper()[:10]}-{random_suffix()}"
                    product = Product(
                        name=prod_identifier,
                        sku=sku_slug,
                        category="Imported",
                        price=float(row['price']),
                        quantity=100  # default starting inventory
                    )
                    db.session.add(product)
                    db.session.commit()
                    
                    # Also seed default inventory metrics
                    inv = Inventory(
                        product_id=product.id,
                        safety_stock=10.0,
                        reorder_point=25.0,
                        eoq=50.0,
                        stock_status="In Stock"
                    )
                    db.session.add(inv)
                    db.session.commit()
                
                # Parse quantity and price
                try:
                    qty = int(row['quantity sold'])
                    price = float(row['price'])
                    # revenue can be provided or computed
                    revenue = float(row['revenue']) if 'revenue' in row and not pd.isna(row['revenue']) else qty * price
                except (ValueError, TypeError):
                    skipped_count += 1
                    continue
                    
                # Create sale object
                sale = Sale(
                    date=parsed_date,
                    product_id=product.id,
                    quantity_sold=qty,
                    price=price,
                    revenue=round(revenue, 2)
                )
                sales_objects.append(sale)
                inserted_count += 1
                
            if sales_objects:
                db.session.bulk_save_objects(sales_objects)
                db.session.commit()
                
                if user_id:
                    AuthService.log_action(user_id, 'Import Sales', f"Imported {inserted_count} sales records from uploaded file")
                    
            return True, f"Successfully imported {inserted_count} records. Skipped {skipped_count} invalid rows."
            
        except Exception as e:
            db.session.rollback()
            return False, f"Database transaction error during import: {str(e)}"

def random_suffix():
    import random
    return str(random.randint(1000, 9999))
