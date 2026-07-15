package com.example.demandforecast.activities;

import android.content.Intent;
import android.os.Bundle;
import android.util.Patterns;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.example.demandforecast.api.ApiClient;
import com.example.demandforecast.databinding.ActivityLoginBinding;
import com.example.demandforecast.models.LoginRequest;
import com.example.demandforecast.models.LoginResponse;
import com.example.demandforecast.models.UserModel;
import com.example.demandforecast.utils.SessionManager;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {

    private ActivityLoginBinding binding;
    private SessionManager sessionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        sessionManager = new SessionManager(this);

        // Auto-login if token already exists in session cache
        if (sessionManager.isLoggedIn()) {
            navigateToDashboard();
        }

        binding.btnLogin.setOnClickListener(v -> attemptLogin());
    }

    private void attemptLogin() {
        String email = binding.etEmail.getText().toString().trim();
        String password = binding.etPassword.getText().toString().trim();

        // Validate fields
        if (email.isEmpty()) {
            binding.tilEmail.setError("Email is required");
            return;
        } else if (!Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.setError("Please enter a valid email address");
            return;
        } else {
            binding.tilEmail.setError(null);
        }

        if (password.isEmpty()) {
            binding.tilPassword.setError("Password is required");
            return;
        } else {
            binding.tilPassword.setError(null);
        }

        // Show Loader Spinner
        binding.btnLogin.setEnabled(false);
        binding.progressLoading.setVisibility(View.VISIBLE);

        // Call Flask Login API
        ApiClient.getApiService().login(new LoginRequest(email, password)).enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                binding.btnLogin.setEnabled(true);
                binding.progressLoading.setVisibility(View.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    LoginResponse loginRes = response.body();
                    UserModel user = loginRes.getUser();
                    
                    // Cache session details
                    sessionManager.createSession(
                            loginRes.getAccessToken(),
                            user.getUsername(),
                            user.getEmail(),
                            user.getRole()
                    );

                    Toast.makeText(LoginActivity.this, "Login successful!", Toast.LENGTH_SHORT).show();
                    navigateToDashboard();
                } else {
                    Toast.makeText(LoginActivity.this, "Invalid credentials. Please try again.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                binding.btnLogin.setEnabled(true);
                binding.progressLoading.setVisibility(View.GONE);
                Toast.makeText(LoginActivity.this, "Error connecting to server. Please try again.", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void navigateToDashboard() {
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
        finish(); // Close LoginActivity
    }
}
