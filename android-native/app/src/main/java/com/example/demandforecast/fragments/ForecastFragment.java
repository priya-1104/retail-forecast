package com.example.demandforecast.fragments;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.example.demandforecast.R;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentForecastBinding;
import com.example.demandforecast.models.ForecastModel;
import com.example.demandforecast.models.ProductModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.SessionManager;
import com.github.philjay.charting.data.BarData;
import com.github.philjay.charting.data.BarDataSet;
import com.github.philjay.charting.data.BarEntry;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ForecastFragment extends Fragment {

    private FragmentForecastBinding binding;
    private SessionManager sessionManager;
    private List<ProductModel> productList;
    private ArrayAdapter<String> spinnerAdapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentForecastBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());
        productList = new ArrayList<>();

        // Load Products for Spinner
        loadProducts();

        binding.btnRunForecast.setOnClickListener(v -> {
            int selectedPos = binding.spinnerProducts.getSelectedItemPosition();
            if (selectedPos >= 0 && selectedPos < productList.size()) {
                ProductModel product = productList.get(selectedPos);
                generateForecast(product);
            } else {
                Toast.makeText(getContext(), "Please select a valid product", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void loadProducts() {
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();
        
        ApiClient.getApiService().getProducts(token).enqueue(new Callback<List<ProductModel>>() {
            @Override
            public void onResponse(Call<List<ProductModel>> call, Response<List<ProductModel>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    productList = response.body();
                    List<String> productNames = new ArrayList<>();
                    for (ProductModel p : productList) {
                        productNames.add(p.getName() + " (ID: #" + p.getId() + ")");
                    }
                    
                    spinnerAdapter = new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_item, productNames);
                    spinnerAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                    binding.spinnerProducts.setAdapter(spinnerAdapter);
                } else {
                    Toast.makeText(getContext(), "Failed to load product catalog", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<ProductModel>> call, Throwable t) {
                Toast.makeText(getContext(), "Connection failed: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void generateForecast(ProductModel product) {
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();
        
        ApiClient.getApiService().getForecast(token, product.getId()).enqueue(new Callback<List<ForecastModel>>() {
            @Override
            public void onResponse(Call<List<ForecastModel>> call, Response<List<ForecastModel>> response) {
                if (response.isSuccessful() && response.body() != null && !response.body().isEmpty()) {
                    List<ForecastModel> list = response.body();
                    ForecastModel data = list.get(0); // Take first forecast record
                    
                    // Show scroll container and hide placeholder
                    binding.scrollResults.setVisibility(View.VISIBLE);
                    binding.tvForecastPlaceholder.setVisibility(View.GONE);
                    
                    // Set Data Values
                    binding.tvResProductName.setText(product.getName());
                    binding.tvResPredicted.setText(String.format("Predicted Demand: %.1f units", data.getPredictedQuantity()));
                    
                    String date = data.getForecastDate();
                    if (date != null && date.length() > 10) {
                        date = date.substring(0, 10);
                    }
                    binding.tvResDate.setText("Target Date: " + date);
                    binding.tvResModel.setText("Model Used: " + data.getModelUsed());
                    binding.tvResHorizon.setText("Forecast Horizon: " + data.getHorizonDays() + " days");
                    
                    // Draw Bar Chart
                    setupBarChart(list);
                } else {
                    Toast.makeText(getContext(), "No forecast predictions found for this product.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<ForecastModel>> call, Throwable t) {
                Toast.makeText(getContext(), "Forecast generation error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setupBarChart(List<ForecastModel> list) {
        List<BarEntry> entries = new ArrayList<>();
        for (int i = 0; i < list.size(); i++) {
            entries.add(new BarEntry(i, (float) list.get(i).getPredictedQuantity()));
        }

        BarDataSet dataSet = new BarDataSet(entries, "Predicted Units");
        dataSet.setColor(Color.parseColor("#0d6efd"));
        dataSet.setValueTextColor(Color.parseColor("#64748b"));
        dataSet.setValueTextSize(10f);

        BarData barData = new BarData(dataSet);
        binding.forecastBarChart.setData(barData);
        binding.forecastBarChart.getDescription().setEnabled(false);
        binding.forecastBarChart.getXAxis().setDrawGridLines(false);
        binding.forecastBarChart.getAxisRight().setEnabled(false);
        binding.forecastBarChart.invalidate(); // Refresh
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
