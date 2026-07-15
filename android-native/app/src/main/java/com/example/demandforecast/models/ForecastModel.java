package com.example.demandforecast.models;

import com.google.gson.annotations.SerializedName;

public class ForecastModel {
    private int id;
    
    @SerializedName("product_id")
    private int productId;
    
    @SerializedName("product_name")
    private String productName;
    
    @SerializedName("forecast_date")
    private String forecastDate;
    
    @SerializedName("predicted_quantity")
    private double predictedQuantity;
    
    @SerializedName("model_used")
    private String modelUsed;
    
    @SerializedName("horizon_days")
    private int horizonDays;

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getProductId() { return productId; }
    public void setProductId(int productId) { this.productId = productId; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public String getForecastDate() { return forecastDate; }
    public void setForecastDate(String forecastDate) { this.forecastDate = forecastDate; }

    public double getPredictedQuantity() { return predictedQuantity; }
    public void setPredictedQuantity(double predictedQuantity) { this.predictedQuantity = predictedQuantity; }

    public String getModelUsed() { return modelUsed; }
    public void setModelUsed(String modelUsed) { this.modelUsed = modelUsed; }

    public int getHorizonDays() { return horizonDays; }
    public void setHorizonDays(int horizonDays) { this.horizonDays = horizonDays; }
}
