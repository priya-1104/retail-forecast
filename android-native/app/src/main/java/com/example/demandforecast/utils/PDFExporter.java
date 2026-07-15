package com.example.demandforecast.utils;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.os.Environment;
import android.widget.Toast;

import com.example.demandforecast.models.ReportModel;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;

public class PDFExporter {

    public static void exportReportsToPDF(Context context, List<ReportModel> reports) {
        PdfDocument document = new PdfDocument();
        
        // Page width 595, height 842 (A4 Dimensions)
        PdfDocument.PageInfo pageInfo = new PdfDocument.PageInfo.Builder(595, 842, 1).create();
        PdfDocument.Page page = document.startPage(pageInfo);
        
        Canvas canvas = page.getCanvas();
        Paint paint = new Paint();
        
        // Title Design
        paint.setColor(Color.parseColor("#0d6efd"));
        paint.setTextSize(20);
        paint.setFakeBoldText(true);
        canvas.drawText("Demand Forecasting Reports Log", 50, 50, paint);
        
        // Horizontal Line
        paint.setColor(Color.GRAY);
        paint.setStrokeWidth(1);
        canvas.drawLine(50, 70, 545, 70, paint);
        
        // Table Headers
        paint.setColor(Color.BLACK);
        paint.setTextSize(12);
        paint.setFakeBoldText(true);
        canvas.drawText("ID", 50, 100, paint);
        canvas.drawText("Report Name", 100, 100, paint);
        canvas.drawText("Type", 320, 100, paint);
        canvas.drawText("Format", 430, 100, paint);
        canvas.drawText("Date", 490, 100, paint);
        
        canvas.drawLine(50, 110, 545, 110, paint);
        
        // Draw rows
        paint.setFakeBoldText(false);
        int yPosition = 130;
        for (ReportModel report : reports) {
            canvas.drawText(String.valueOf(report.getId()), 50, yPosition, paint);
            
            // Truncate name if too long
            String name = report.getName();
            if (name.length() > 25) {
                name = name.substring(0, 22) + "...";
            }
            canvas.drawText(name, 100, yPosition, paint);
            canvas.drawText(report.getType(), 320, yPosition, paint);
            canvas.drawText(report.getFormat(), 430, yPosition, paint);
            
            String date = report.getCreatedAt();
            if (date.length() > 10) {
                date = date.substring(0, 10);
            }
            canvas.drawText(date, 490, yPosition, paint);
            
            yPosition += 25;
            if (yPosition > 800) {
                break; // Limit to single page for simplicity
            }
        }
        
        document.finishPage(page);
        
        // Write PDF file
        File pdfDir = context.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
        File pdfFile = new File(pdfDir, "ReportsLog.pdf");
        
        try {
            document.writeTo(new FileOutputStream(pdfFile));
            Toast.makeText(context, "PDF saved to: " + pdfFile.getAbsolutePath(), Toast.LENGTH_LONG).show();
        } catch (IOException e) {
            e.printStackTrace();
            Toast.makeText(context, "Error generating PDF: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        } finally {
            document.close();
        }
    }
}
