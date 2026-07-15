package com.example.demandforecast.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.widget.SearchView;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.example.demandforecast.adapter.InventoryAdapter;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentInventoryBinding;
import com.example.demandforecast.models.InventoryModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.SessionManager;

import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class InventoryFragment extends Fragment {

    private FragmentInventoryBinding binding;
    private SessionManager sessionManager;
    private InventoryAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentInventoryBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());

        // Setup Recycler View
        binding.rvInventory.setLayoutManager(new LinearLayoutManager(getContext()));

        // Setup Search filtering
        binding.searchViewInventory.setOnQueryTextListener(new SearchView.OnQueryTextListener() {
            @Override
            public boolean onQueryTextSubmit(String query) {
                if (adapter != null) {
                    adapter.filter(query);
                }
                return false;
            }

            @Override
            public boolean onQueryTextChange(String newText) {
                if (adapter != null) {
                    adapter.filter(newText);
                }
                return false;
            }
        });

        // Load Data
        loadInventory();
    }

    private void loadInventory() {
        binding.progressInventory.setVisibility(View.VISIBLE);
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();

        ApiClient.getApiService().getInventory(token).enqueue(new Callback<List<InventoryModel>>() {
            @Override
            public void onResponse(Call<List<InventoryModel>> call, Response<List<InventoryModel>> response) {
                binding.progressInventory.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<InventoryModel> list = response.body();
                    adapter = new InventoryAdapter(list);
                    binding.rvInventory.setAdapter(adapter);
                } else {
                    Toast.makeText(getContext(), "Failed to fetch inventory logs", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<InventoryModel>> call, Throwable t) {
                binding.progressInventory.setVisibility(View.GONE);
                Toast.makeText(getContext(), "Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
