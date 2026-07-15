package com.example.demandforecast.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.demandforecast.R;
import com.example.demandforecast.models.ReportModel;

import java.util.List;

public class ReportAdapter extends RecyclerView.Adapter<ReportAdapter.ReportViewHolder> {

    private final List<ReportModel> reportList;

    public ReportAdapter(List<ReportModel> reportList) {
        this.reportList = reportList;
    }

    @NonNull
    @Override
    public ReportViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_report, parent, false);
        return new ReportViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ReportViewHolder holder, int position) {
        ReportModel model = reportList.get(position);
        holder.tvReportName.setText(model.getName());
        
        String dateStr = model.getCreatedAt();
        if (dateStr != null && dateStr.length() > 10) {
            dateStr = dateStr.substring(0, 10);
        }
        holder.tvReportDate.setText("Created Date: " + dateStr);
        holder.tvReportFormat.setText(model.getFormat().toUpperCase());
        
        // Show icon based on type
        if (model.getFormat().equalsIgnoreCase("pdf")) {
            holder.imgReportIcon.setImageResource(android.R.drawable.ic_menu_gallery);
        }
    }

    @Override
    public int getItemCount() {
        return reportList.size();
    }

    static class ReportViewHolder extends RecyclerView.ViewHolder {
        TextView tvReportName, tvReportDate, tvReportFormat;
        ImageView imgReportIcon;

        public ReportViewHolder(@NonNull View itemView) {
            super(itemView);
            tvReportName = itemView.findViewById(R.id.tv_report_name);
            tvReportDate = itemView.findViewById(R.id.tv_report_date);
            tvReportFormat = itemView.findViewById(R.id.tv_report_format);
            imgReportIcon = itemView.findViewById(R.id.img_report_icon);
        }
    }
}
