package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;
import java.lang.reflect.Field;
import java.util.ArrayList;

public class ServiceSelectorActivity extends Activity {

    private static final String PREFS   = "svc_sel";
    private static final String KEY_URL = "saved_url";

    private static final String[] NAMES = {
        "Papai",
        "Mel",
        "Ivan",
        "Custom..."
    };

    private static final String[] XC_URLS = {
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"AEGVXXZVZV\",\"p\":\"236267373\",\"o\":\"ts\"}",
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"Melli3B3llie@832\",\"p\":\"Fir3F@xed2020\",\"o\":\"ts\"}",
        "xc:{\"h\":\"http://ky-tv.cc:80\",\"u\":\"icastil@1997\",\"p\":\"TheFireF@x3733\",\"o\":\"ts\"}",
        null  // placeholder for Custom
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Always populate _portals so "Add playlist → Service" shows our options
        populatePortals();

        // If a playlist was already chosen before, skip selector and launch directly
        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String savedUrl = prefs.getString(KEY_URL, null);
        if (savedUrl != null) {
            launchWithUrl(savedUrl);
            return;
        }

        // First run — show selector
        showSelector();
    }

    private void populatePortals() {
        try {
            Class<?> portalClass  = Class.forName("com.andyhax.haxsplash.PortalModel");
            Class<?> andyHaxClass = Class.forName("com.andyhax.haxsplash.AndyHax");
            Field portalsField    = andyHaxClass.getField("_portals");
            Field idField         = portalClass.getField("id_bClNU2OajLbxJWVW");
            Field nameField       = portalClass.getField("name_doQhQ7J9PskxUJv5");
            Field urlField        = portalClass.getField("url_rH6MnarmmBvhjdPh");

            ArrayList<Object> list = new ArrayList<>();
            for (int i = 0; i < XC_URLS.length - 1; i++) {   // skip "Custom..."
                Object p = portalClass.newInstance();
                idField.set(p, i + 1);
                nameField.set(p, NAMES[i]);
                urlField.set(p, XC_URLS[i]);
                list.add(p);
            }
            portalsField.set(null, list);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void showSelector() {
        new AlertDialog.Builder(this)
            .setTitle("Select Service")
            .setItems(NAMES, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    if (which == NAMES.length - 1) {
                        showCustomDialog();
                    } else {
                        saveAndLaunch(XC_URLS[which]);
                    }
                }
            })
            .setCancelable(false)
            .show();
    }

    private void showCustomDialog() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(16 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, 0);

        final EditText etHost = new EditText(this);
        etHost.setHint("Host (e.g. http://server.com:8080)");
        etHost.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        layout.addView(etHost, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        final EditText etUser = new EditText(this);
        etUser.setHint("Username");
        layout.addView(etUser, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        final EditText etPass = new EditText(this);
        etPass.setHint("Password");
        etPass.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        layout.addView(etPass, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        new AlertDialog.Builder(this)
            .setTitle("Custom Xtream")
            .setView(layout)
            .setPositiveButton("Connect", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    String host = etHost.getText().toString().trim();
                    String user = etUser.getText().toString().trim();
                    String pass = etPass.getText().toString().trim();
                    if (host.isEmpty() || user.isEmpty() || pass.isEmpty()) {
                        Toast.makeText(ServiceSelectorActivity.this,
                            "All fields required", Toast.LENGTH_SHORT).show();
                        showCustomDialog();
                        return;
                    }
                    String url = "xc:{\"h\":\"" + host + "\",\"u\":\"" + user +
                                 "\",\"p\":\"" + pass + "\",\"o\":\"ts\"}";
                    saveAndLaunch(url);
                }
            })
            .setNegativeButton("Back", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    showSelector();
                }
            })
            .setCancelable(false)
            .show();
    }

    private void saveAndLaunch(String xcUrl) {
        getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KEY_URL, xcUrl).apply();
        launchWithUrl(xcUrl);
    }

    private void launchWithUrl(String xcUrl) {
        try {
            Class<?> hookApp    = Class.forName("com.andyhax.hook.HookApplication");
            java.lang.reflect.Method injectMethod =
                hookApp.getMethod("inject", String.class, String.class);
            // inject() is static native — pass null as instance
            injectMethod.invoke(null, xcUrl, xcUrl);
        } catch (Exception e) {
            e.printStackTrace();
        }

        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "ar.tvplayer.tv",
            "ar.tvplayer.tv.ui.MainActivity"
        ));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
