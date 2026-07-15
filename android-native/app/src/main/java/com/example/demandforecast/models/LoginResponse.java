package com.example.demandforecast.models;

import com.google.gson.annotations.SerializedName;

public class LoginResponse {
    @SerializedName("access_token")
    private String accessToken;
    
    @SerializedName("message")
    private String message;
    
    private UserModel user;

    public String getAccessToken() { return accessToken; }
    public void setAccessToken(String accessToken) { this.accessToken = accessToken; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public UserModel getUser() { return user; }
    public void setUser(UserModel user) { this.user = user; }
}
