package com.andyhax.haxsplash;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

public class ServiceSelectorActivity extends Activity {

    private static final String[] NAMES = {
        "http://ky-tv.cc:80"
    };
    private static final String[] HOST  = {
        "http://ky-tv.cc:80"
    };
    private static final String[] USER  = {
        ""
    };
    private static final String[] PASS  = {
        ""
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "ar.tvplayer.tv", "ar.tvplayer.tv.ui.MainActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                      | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        AndyHax._portals.clear();
        for (int i = 0; i < NAMES.length; i++) {
            PortalModel pm = new PortalModel();
            pm.id_bClNU2OajLbxJWVW = i;
            pm.name_doQhQ7J9PskxUJv5 = NAMES[i];
            pm.url_rH6MnarmmBvhjdPh = xc(HOST[i], USER[i], PASS[i]);
            AndyHax._portals.add(pm);
        }
        startActivity(intent);
        finish();
    }

    private static String xc(String h, String u, String p) {
        return "xc:{\"h\":\"" + h + "\",\"u\":\"" + u
             + "\",\"p\":\"" + p + "\",\"o\":\"ts\"}";
    }
}
