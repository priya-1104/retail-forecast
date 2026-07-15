package com.example.demandforecast.activities;

import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.navigation.NavController;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.AppBarConfiguration;
import androidx.navigation.ui.NavigationUI;

import com.example.demandforecast.R;
import com.example.demandforecast.databinding.ActivityMainBinding;

public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        // Setup custom top action bar/toolbar
        setSupportActionBar(binding.toolbar);

        // Bind NavController and BottomNavigationView together
        NavHostFragment navHostFragment = (NavHostFragment) getSupportFragmentManager()
                .findFragmentById(R.id.nav_host_fragment);
                
        if (navHostFragment != null) {
            NavController navController = navHostFragment.getNavController();
            
            // Configuration for top-level navigation items
            AppBarConfiguration appBarConfiguration = new AppBarConfiguration.Builder(
                    R.id.navigation_dashboard,
                    R.id.navigation_forecast,
                    R.id.navigation_inventory,
                    R.id.navigation_sales,
                    R.id.navigation_reports,
                    R.id.navigation_profile
            ).build();
            
            NavigationUI.setupActionBarWithNavController(this, navController, appBarConfiguration);
            NavigationUI.setupWithNavController(binding.bottomNavigation, navController);
        }
    }
}
