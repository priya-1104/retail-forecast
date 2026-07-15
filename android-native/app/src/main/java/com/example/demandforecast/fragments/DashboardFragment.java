package com.example.demandforecast.fragments;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.navigation.Navigation;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.example.demandforecast.R;
import com.example.demandforecast.adapter.ForecastAdapter;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentDashboardBinding;
import com.example.demandforecast.models.DashboardModel;
import com.example.demandforecast.models.ForecastModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.SessionManager;
import com.github.philjay.charting.data.Entry;
import com.github.philjay.charting.data.LineData;
import com.github.philjay.charting.data.LineDataSet;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class DashboardFragment extends Fragment {

    private FragmentDashboardBinding binding;
    private SessionManager sessionManager;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentDashboardBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());

        // Setup Quick Actions
        binding.btnQuickForecast.setOnClickListener(v -> 
            Navigation.findNavController(view).navigate(R.id.navigation_forecast));

        binding.btnQuickInventory.setOnClickListener(v -> 
            Navigation.findNavController(view).navigate(R.id.navigation_inventory));

        binding.btnQuickReports.setOnClickListener(v -> 
            Navigation.findNavController(view).navigate(R.id.navigation_reports));

        // Fetch Data from Server
        loadDashboardSummary();
    }

    private void loadDashboardSummary() {
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();
        
        ApiClient.getApiService().getDashboardSummary(token).enqueue(new Callback<DashboardModel>() {
            @Override
            public void onResponse(Call<DashboardModel> call, Response<DashboardModel> response) {
                if (response.isSuccessful() && response.body() != null) {
                    DashboardModel data = response.body();
                    
                    // Set KPI Values
                    binding.tvTotalProducts.setText(String.valueOf(data.getTotalProducts()));
                    binding.tvTotalRevenue.setText(String.format("$%.2f", data.getTotalRevenue()));
                    binding.tvLowStock.setText(data.getLowStockCount() + " items");
                    
                    // Render Line Chart
                    setupLineChart(data.getRecentSalesTrend());
                    
                    // Fetch Forecasts (Recent list)
                    loadRecentForecasts();
                } else {
                    Toast.makeText(getContext(), "Failed to load summary stats", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<DashboardModel> call, Throwable t) {
                Toast.makeText(getContext(), "Error connecting to server: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void loadRecentForecasts() {
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();
        
        // Let's call forecast with product id 1 to show a sample on the dashboard
        ApiClient.getApiService().getForecast(token, 1).enqueue(new Callback<List<ForecastModel>>() {
            @Override
            public void onResponse(Call<List<ForecastModel>> call, Response<List<ForecastModel>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<ForecastModel> list = response.body();
                    
                    // Limit to 5
                    if (list.size() > 5) {
                        list = list.subList(0, 5);
                    }
                    
                    binding.rvRecentForecasts.setLayoutManager(new LinearLayoutManager(getContext()));
                    binding.rvRecentForecasts.setAdapter(new ForecastAdapter(list));
                }
            }

            @Override
            public void onFailure(Call<List<ForecastModel>> call, Throwable t) {
                // Fail silently on secondary content load
            }
        });
    }

    private void setupLineChart(List<DashboardModel.SalesTrendItem> trend) {
        if (trend == null || trend.isEmpty()) return;

        List<Entry> entries = new ArrayList<>();
        for (int i = 0; i < trend.size(); i++) {
            entries.add(new Entry(i, (float) trend.get(i).getRevenue()));
        }

        LineDataSet dataSet = new LineDataSet(entries, "Daily Revenue ($)");
        dataSet.setColor(Color.parseColor("#0d6efd"));
        dataSet.setCircleColor(Color.parseColor("#0d6efd"));
        dataSet.setLineWidth(2f);
        dataSet.setCircleRadius(4f);
        dataSet.setDrawCircleHoles(false);
        dataSet.setValueTextSize(10f);
        dataSet.setDrawValues(false);
        
        // Enable filled line gradient style
        dataSet.setDrawFilled(true);
        dataSet.setFillColor(Color.parseColor("#e7f1ff"));

        LineData lineData = new LineData(dataSet);
        binding.salesLineChart.setData(lineData);
        binding.salesLineChart.getDescription().setEnabled(false);
        binding.salesLineChart.getLegend().setEnabled(false);
        binding.salesLineChart.getXAxis().setDrawGridLines(false);
        binding.salesLineChart.getAxisRight().setEnabled(false);
        binding.salesLineChart.invalidate(); // Refresh
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
