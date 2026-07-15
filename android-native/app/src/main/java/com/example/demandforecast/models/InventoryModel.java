package com.example.demandforecast.models;

import com.google.gson.annotations.SerializedName;

public class InventoryModel {
    private int id;
    
    @SerializedName("product_id")
    private int productId;
    
    @SerializedName("product_name")
    private String productName;
    
    private String sku;
    
    @SerializedName("current_stock")
    private int currentStock;
    
    @SerializedName("safety_stock")
    private double safetyStock;
    
    @SerializedName("reorder_point")
    private double reorderPoint;
    
    private double eoq;
    
    @SerializedName("stock_status")
    private String stockStatus;

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getProductId() { return productId; }
    public void setProductId(int productId) { this.productId = productId; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }

    public int getCurrentStock() { return currentStock; }
    public void setCurrentStock(int currentStock) { this.currentStock = currentStock; }

    public double getSafetyStock() { return safetyStock; }
    public void setSafetyStock(double safetyStock) { this.safetyStock = safetyStock; }

    public double getReorderPoint() { return reorderPoint; }
    public void setReorderPoint(double reorderPoint) { this.reorderPoint = reorderPoint; }

    public double getEoq() { return eoq; }
    public void setEoq(double eoq) { this.eoq = eoq; }

    public String getStockStatus() { return stockStatus; }
    public void setStockStatus(String stockStatus) { this.stockStatus = stockStatus; }
}
