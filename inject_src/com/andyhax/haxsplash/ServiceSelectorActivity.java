package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import java.lang.reflect.Method;

public class ServiceSelectorActivity extends Activity {

    private static final String[] NAMES = {
        "Papai",
        "Mel",
        "Ivan"
    };

    private static final String[] XC_URLS = {
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"AEGVXXZVZV\",\"p\":\"236267373\",\"o\":\"ts\"}",
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"Melli3B3llie@832\",\"p\":\"Fir3F@xed2020\",\"o\":\"ts\"}",
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"icastil@1997\",\"p\":\"TheFireF@x3733\",\"o\":\"ts\"}"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        new AlertDialog.Builder(this)
            .setTitle("Select Service")
            .setItems(NAMES, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    try {
                        // Call the real HookApplication.inject() via reflection
                        // so we don't conflict with our stub class
                        Class<?> hookApp = Class.forName("com.andyhax.hook.HookApplication");
                        Method injectMethod = hookApp.getMethod("inject", String.class, String.class);
                        injectMethod.invoke(null, NAMES[which], XC_URLS[which]);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                    // Start the real MainActivity by component name
                    Intent intent = new Intent();
                    intent.setComponent(new ComponentName(
                        "ar.tvplayer.tv",
                        "ar.tvplayer.tv.ui.MainActivity"
                    ));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                    startActivity(intent);
                    finish();
                }
            })
            .setCancelable(false)
            .show();
    }
}
