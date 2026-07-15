package com.example.demandforecast.models;

import com.google.gson.annotations.SerializedName;

public class SalesModel {
    private int id;
    private String date;
    
    @SerializedName("product_id")
    private int productId;
    
    @SerializedName("product_name")
    private String productName;
    
    @SerializedName("quantity_sold")
    private int quantitySold;
    
    private double price;
    private double revenue;

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }

    public int getProductId() { return productId; }
    public void setProductId(int productId) { this.productId = productId; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public int getQuantitySold() { return quantitySold; }
    public void setQuantitySold(int quantitySold) { this.quantitySold = quantitySold; }

    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }

    public double getRevenue() { return revenue; }
    public void setRevenue(double revenue) { this.revenue = revenue; }
}
