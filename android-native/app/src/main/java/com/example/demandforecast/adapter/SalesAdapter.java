package com.example.demandforecast.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.demandforecast.R;
import com.example.demandforecast.models.SalesModel;

import java.util.List;

public class SalesAdapter extends RecyclerView.Adapter<SalesAdapter.SalesViewHolder> {

    private final List<SalesModel> salesList;

    public SalesAdapter(List<SalesModel> salesList) {
        this.salesList = salesList;
    }

    @NonNull
    @Override
    public SalesViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_sales, parent, false);
        return new SalesViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull SalesViewHolder holder, int position) {
        SalesModel model = salesList.get(position);
        holder.tvProductName.setText(model.getProductName() != null ? model.getProductName() : "Product #" + model.getProductId());
        
        String dateStr = model.getDate();
        if (dateStr != null && dateStr.length() > 10) {
            dateStr = dateStr.substring(0, 10);
        }
        holder.tvSalesDate.setText("Transaction Date: " + dateStr);
        holder.tvSalesQuantity.setText("Qty Sold: " + model.getQuantitySold() + " units");
        holder.tvSalesRevenue.setText(String.format("+$%.2f", model.getRevenue()));
    }

    @Override
    public int getItemCount() {
        return salesList.size();
    }

    static class SalesViewHolder extends RecyclerView.ViewHolder {
        TextView tvProductName, tvSalesDate, tvSalesQuantity, tvSalesRevenue;

        public SalesViewHolder(@NonNull View itemView) {
            super(itemView);
            tvProductName = itemView.findViewById(R.id.tv_sales_product_name);
            tvSalesDate = itemView.findViewById(R.id.tv_sales_date);
            tvSalesQuantity = itemView.findViewById(R.id.tv_sales_quantity);
            tvSalesRevenue = itemView.findViewById(R.id.tv_sales_revenue);
        }
    }
}
