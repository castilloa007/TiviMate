package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.os.Bundle;

public class ServiceSelectorActivity extends Activity {

    private static final String[] NAMES = {"Papai", "Mel", "Ivan"};
    private static final String[] HOST  = {
        "http://ky-tv.cc:80", "http://ky-tv.cc:80", "http://ky-tv.cc:80"};
    private static final String[] USER  = {
        "AEGVXXZVZV", "Melli3B3llie@832", "icastil@1997"};
    private static final String[] PASS  = {
        "236267373", "Fir3F@xed2020", "TheFireF@x3733"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showPicker();
    }

    private void showPicker() {
        new AlertDialog.Builder(this)
            .setTitle("Select Account")
            .setItems(NAMES, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    String url = xc(HOST[which], USER[which], PASS[which]);
                    AndyHax.m1616Go(url, ServiceSelectorActivity.this);
                    finish();
                }
            })
            .setCancelable(false)
            .show();
    }

    private static String xc(String h, String u, String p) {
        return "xc:{\"h\":\"" + h + "\",\"u\":\"" + u + "\",\"p\":\"" + p + "\",\"o\":\"ts\"}";
    }
}
