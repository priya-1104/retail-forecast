package com.example.demandforecast.adapter;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.demandforecast.R;
import com.example.demandforecast.models.InventoryModel;

import java.util.ArrayList;
import java.util.List;

public class InventoryAdapter extends RecyclerView.Adapter<InventoryAdapter.InventoryViewHolder> {

    private final List<InventoryModel> inventoryList;
    private final List<InventoryModel> filteredList;

    public InventoryAdapter(List<InventoryModel> inventoryList) {
        this.inventoryList = inventoryList;
        this.filteredList = new ArrayList<>(inventoryList);
    }

    public void filter(String query) {
        filteredList.clear();
        if (query.isEmpty()) {
            filteredList.addAll(inventoryList);
        } else {
            String lowercase = query.toLowerCase().trim();
            for (InventoryModel item : inventoryList) {
                if ((item.getProductName() != null && item.getProductName().toLowerCase().contains(lowercase)) ||
                    (item.getSku() != null && item.getSku().toLowerCase().contains(lowercase))) {
                    filteredList.add(item);
                }
            }
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public InventoryViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_inventory, parent, false);
        return new InventoryViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull InventoryViewHolder holder, int position) {
        InventoryModel model = filteredList.get(position);
        holder.tvProductName.setText(model.getProductName() != null ? model.getProductName() : "Product #" + model.getProductId());
        holder.tvSku.setText("SKU: " + (model.getSku() != null ? model.getSku() : "N/A"));
        holder.tvReorder.setText("Reorder Point: " + String.format("%.0f", model.getReorderPoint()) + " | Safety Stock: " + String.format("%.0f", model.getSafetyStock()));
        holder.tvQuantity.setText(model.getCurrentStock() + " units");
        
        holder.tvStatus.setText(model.getStockStatus());
        String status = model.getStockStatus();
        if (status.equalsIgnoreCase("Low Stock") || status.equalsIgnoreCase("Critical Low")) {
            holder.tvStatus.setTextColor(Color.parseColor("#FFC107"));
            holder.tvStatus.setBackgroundColor(Color.parseColor("#FFFDE7"));
        } else if (status.equalsIgnoreCase("Out of Stock")) {
            holder.tvStatus.setTextColor(Color.parseColor("#DC3545"));
            holder.tvStatus.setBackgroundColor(Color.parseColor("#FFEBEE"));
        } else {
            holder.tvStatus.setTextColor(Color.parseColor("#198754"));
            holder.tvStatus.setBackgroundColor(Color.parseColor("#E8F5E9"));
        }
    }

    @Override
    public int getItemCount() {
        return filteredList.size();
    }

    static class InventoryViewHolder extends RecyclerView.ViewHolder {
        TextView tvProductName, tvSku, tvReorder, tvQuantity, tvStatus;

        public InventoryViewHolder(@NonNull View itemView) {
            super(itemView);
            tvProductName = itemView.findViewById(R.id.tv_inv_product_name);
            tvSku = itemView.findViewById(R.id.tv_inv_sku);
            tvReorder = itemView.findViewById(R.id.tv_inv_reorder);
            tvQuantity = itemView.findViewById(R.id.tv_inv_quantity);
            tvStatus = itemView.findViewById(R.id.tv_inv_status);
        }
    }
}
