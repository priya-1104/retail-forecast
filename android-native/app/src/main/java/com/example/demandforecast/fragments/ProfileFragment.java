package com.example.demandforecast.fragments;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.example.demandforecast.activities.LoginActivity;
import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.FragmentProfileBinding;
import com.example.demandforecast.models.UserModel;
import com.example.demandforecast.utils.Constants;
import com.example.demandforecast.utils.SessionManager;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ProfileFragment extends Fragment {

    private FragmentProfileBinding binding;
    private SessionManager sessionManager;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentProfileBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        sessionManager = new SessionManager(requireContext());

        // Set Cached SharedPreferences details first
        binding.tvProfileName.setText(sessionManager.getUsername());
        binding.tvProfileEmail.setText(sessionManager.getEmail());
        binding.tvProfileRole.setText(sessionManager.getRole().toUpperCase());

        // Fetch Fresh details from API
        loadUserProfile();

        // Logout listener
        binding.btnLogout.setOnClickListener(v -> {
            sessionManager.logout();
            
            // Redirect back to LoginActivity and close MainActivity
            Intent intent = new Intent(requireActivity(), LoginActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            requireActivity().finish();
            
            Toast.makeText(getContext(), "Session ended successfully.", Toast.LENGTH_SHORT).show();
        });
    }

    private void loadUserProfile() {
        String token = Constants.TOKEN_PREFIX + sessionManager.getToken();

        ApiClient.getApiService().getProfile(token).enqueue(new Callback<UserModel>() {
            @Override
            public void onResponse(Call<UserModel> call, Response<UserModel> response) {
                if (response.isSuccessful() && response.body() != null) {
                    UserModel user = response.body();
                    binding.tvProfileName.setText(user.getUsername());
                    binding.tvProfileEmail.setText(user.getEmail());
                    binding.tvProfileRole.setText(user.getRole().toUpperCase());
                }
            }

            @Override
            public void onFailure(Call<UserModel> call, Throwable t) {
                // Fail silently and retain local cached profile labels
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
