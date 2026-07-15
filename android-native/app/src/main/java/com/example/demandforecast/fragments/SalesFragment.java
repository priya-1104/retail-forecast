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
import androidx.recyclerview.widget.LinearLayoutManager;

import com.example.demandforecast.adapter.SalesAdapter;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentSalesBinding;
import com.example.demandforecast.models.SalesModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.SessionManager;
import com.github.philjay.charting.data.PieData;
import com.github.philjay.charting.data.PieDataSet;
import com.github.philjay.charting.data.PieEntry;
import com.github.philjay.charting.utils.ColorTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class SalesFragment extends Fragment {

    private FragmentSalesBinding binding;
    private SessionManager sessionManager;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentSalesBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());

        // Recycler layout manager
        binding.rvSales.setLayoutManager(new LinearLayoutManager(getContext()));

        // Fetch transaction list
        loadSales();
    }

    private void loadSales() {
        binding.progressSales.setVisibility(View.VISIBLE);
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();

        ApiClient.getApiService().getSales(token).enqueue(new Callback<List<SalesModel>>() {
            @Override
            public void onResponse(Call<List<SalesModel>> call, Response<List<SalesModel>> response) {
                binding.progressSales.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<SalesModel> list = response.body();
                    
                    // Bind to recycler list
                    binding.rvSales.setAdapter(new SalesAdapter(list));
                    
                    // Group and render Pie Chart
                    setupPieChart(list);
                } else {
                    Toast.makeText(getContext(), "Failed to load transactions", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<SalesModel>> call, Throwable t) {
                binding.progressSales.setVisibility(View.GONE);
                Toast.makeText(getContext(), "Error connecting: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setupPieChart(List<SalesModel> list) {
        if (list == null || list.isEmpty()) return;

        // Group sales revenues by product names (acting as mock categories or items)
        Map<String, Float> grouped = new HashMap<>();
        for (SalesModel sale : list) {
            String name = sale.getProductName() != null ? sale.getProductName() : "Product #" + sale.getProductId();
            float rev = (float) sale.getRevenue();
            if (grouped.containsKey(name)) {
                grouped.put(name, grouped.get(name) + rev);
            } else {
                grouped.put(name, rev);
            }
        }

        // Limit entries to top 5
        List<PieEntry> entries = new ArrayList<>();
        int count = 0;
        for (Map.Entry<String, Float> item : grouped.entrySet()) {
            entries.add(new PieEntry(item.getValue(), item.getKey()));
            count++;
            if (count >= 5) break;
        }

        PieDataSet dataSet = new PieDataSet(entries, "");
        dataSet.setColors(ColorTemplate.MATERIAL_COLORS);
        dataSet.setValueTextColor(Color.WHITE);
        dataSet.setValueTextSize(12f);

        PieData pieData = new PieData(dataSet);
        binding.salesPieChart.setData(pieData);
        binding.salesPieChart.getDescription().setEnabled(false);
        binding.salesPieChart.setUsePercentValues(true);
        binding.salesPieChart.setEntryLabelColor(Color.BLACK);
        binding.salesPieChart.invalidate(); // Refresh
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
