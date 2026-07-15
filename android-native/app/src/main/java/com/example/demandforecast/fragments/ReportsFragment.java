package com.example.demandforecast.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.example.demandforecast.adapter.ReportAdapter;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentReportsBinding;
import com.example.demandforecast.models.ReportModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.PDFExporter;
import com.example.demandforecast.utils.SessionManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ReportsFragment extends Fragment {

    private FragmentReportsBinding binding;
    private SessionManager sessionManager;
    private List<ReportModel> reportList;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentReportsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());
        reportList = new ArrayList<>();

        // Recycler View layout manager
        binding.rvReports.setLayoutManager(new LinearLayoutManager(getContext()));

        // Fetch reports list
        loadReports();

        // Export PDF Button click
        binding.btnExportPdf.setOnClickListener(v -> {
            if (!reportList.isEmpty()) {
                PDFExporter.exportReportsToPDF(requireContext(), reportList);
            } else {
                Toast.makeText(getContext(), "No report entries available to export", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void loadReports() {
        binding.progressReports.setVisibility(View.VISIBLE);
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();

        ApiClient.getApiService().getReports(token).enqueue(new Callback<List<ReportModel>>() {
            @Override
            public void onResponse(Call<List<ReportModel>> call, Response<List<ReportModel>> response) {
                binding.progressReports.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    reportList = response.body();
                    binding.rvReports.setAdapter(new ReportAdapter(reportList));
                } else {
                    Toast.makeText(getContext(), "Failed to load reports catalog", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<ReportModel>> call, Throwable t) {
                binding.progressReports.setVisibility(View.GONE);
                Toast.makeText(getContext(), "Error connecting: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
