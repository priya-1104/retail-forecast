package com.example.demandforecast.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class DashboardModel {
    @SerializedName("total_products")
    private int totalProducts;

    @SerializedName("total_revenue")
    private double totalRevenue;

    @SerializedName("low_stock_count")
    private int lowStockCount;

    @SerializedName("unread_alerts_count")
    private int unreadAlertsCount;

    @SerializedName("recent_sales_trend")
    private List<SalesTrendItem> recentSalesTrend;

    public int getTotalProducts() { return totalProducts; }
    public void setTotalProducts(int totalProducts) { this.totalProducts = totalProducts; }

    public double getTotalRevenue() { return totalRevenue; }
    public void setTotalRevenue(double totalRevenue) { this.totalRevenue = totalRevenue; }

    public int getLowStockCount() { return lowStockCount; }
    public void setLowStockCount(int lowStockCount) { this.lowStockCount = lowStockCount; }

    public int getUnreadAlertsCount() { return unreadAlertsCount; }
    public void setUnreadAlertsCount(int unreadAlertsCount) { this.unreadAlertsCount = unreadAlertsCount; }

    public List<SalesTrendItem> getRecentSalesTrend() { return recentSalesTrend; }
    public void setRecentSalesTrend(List<SalesTrendItem> recentSalesTrend) { this.recentSalesTrend = recentSalesTrend; }

    public static class SalesTrendItem {
        private String date;
        private double revenue;

        public String getDate() { return date; }
        public void setDate(String date) { this.date = date; }

        public double getRevenue() { return revenue; }
        public void setRevenue(double revenue) { this.revenue = revenue; }
    }
}
