package com.example.demandforecast.api;

import com.example.demandforecast.models.LoginRequest;
import com.example.demandforecast.models.LoginResponse;
import com.example.demandforecast.models.DashboardModel;
import com.example.demandforecast.models.ForecastModel;
import com.example.demandforecast.models.InventoryModel;
import com.example.demandforecast.models.ProductModel;
import com.example.demandforecast.models.ReportModel;
import com.example.demandforecast.models.SalesModel;
import com.example.demandforecast.models.UserModel;

import java.util.List;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.POST;
import retrofit2.http.Path;
import retrofit2.http.Query;

public interface ApiService {

    @POST("auth/login")
    Call<LoginResponse> login(@Body LoginRequest loginRequest);

    @GET("auth/profile")
    Call<UserModel> getProfile(@Header("Authorization") String token);

    @GET("dashboard/summary")
    Call<DashboardModel> getDashboardSummary(@Header("Authorization") String token);

    @GET("products")
    Call<List<ProductModel>> getProducts(@Header("Authorization") String token);

    @GET("sales")
    Call<List<SalesModel>> getSales(@Header("Authorization") String token);

    @GET("forecast/{product_id}")
    Call<List<ForecastModel>> getForecast(
        @Header("Authorization") String token,
        @Path("product_id") int productId
    );

    @GET("inventory")
    Call<List<InventoryModel>> getInventory(@Header("Authorization") String token);

    @GET("reports")
    Call<List<ReportModel>> getReports(@Header("Authorization") String token);
}
