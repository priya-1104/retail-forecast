package com.example.demandforecast.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.demandforecast.R;
import com.example.demandforecast.models.ForecastModel;

import java.util.List;

public class ForecastAdapter extends RecyclerView.Adapter<ForecastAdapter.ForecastViewHolder> {

    private final List<ForecastModel> forecastList;

    public ForecastAdapter(List<ForecastModel> forecastList) {
        this.forecastList = forecastList;
    }

    @NonNull
    @Override
    public ForecastViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_forecast, parent, false);
        return new ForecastViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ForecastViewHolder holder, int position) {
        ForecastModel model = forecastList.get(position);
        holder.tvProductName.setText(model.getProductName() != null ? model.getProductName() : "Product #" + model.getProductId());
        
        String dateStr = model.getForecastDate();
        if (dateStr != null && dateStr.length() > 10) {
            dateStr = dateStr.substring(0, 10);
        }
        holder.tvForecastDate.setText("Target Date: " + dateStr);
        holder.tvForecastModel.setText("Model: " + model.getModelUsed());
        
        holder.tvPredictedQty.setText(String.format("%.1f units", model.getPredictedQuantity()));
        holder.tvHorizon.setText(model.getHorizonDays() + "d Horizon");
    }

    @Override
    public int getItemCount() {
        return forecastList.size();
    }

    static class ForecastViewHolder extends RecyclerView.ViewHolder {
        TextView tvProductName, tvForecastDate, tvForecastModel, tvPredictedQty, tvHorizon;

        public ForecastViewHolder(@NonNull View itemView) {
            super(itemView);
            tvProductName = itemView.findViewById(R.id.tv_item_product_name);
            tvForecastDate = itemView.findViewById(R.id.tv_item_forecast_date);
            tvForecastModel = itemView.findViewById(R.id.tv_item_forecast_model);
            tvPredictedQty = itemView.findViewById(R.id.tv_item_predicted_qty);
            tvHorizon = itemView.findViewById(R.id.tv_item_horizon);
        }
    }
}
