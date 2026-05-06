package com.andyhax.haxsplash;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

public class ServiceSelectorActivity extends Activity {

    private static final String[] NAMES = {
        "Papai", "Mel", "Ivan", "http://ky-tv.cc:80"
    };
    private static final String[] HOST  = {
        "http://ky-tv.cc:80", "http://ky-tv.cc:80", "http://ky-tv.cc:80", "http://ky-tv.cc:80"
    };
    private static final String[] USER  = {
        "AEGVXXZVZV", "Melli3B3llie@832", "icastil@1997", ""
    };
    private static final String[] PASS  = {
        "236267373", "Fir3F@xed2020", "TheFireF@x3733", ""
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // MainActivity requires _portals to be non-empty to start correctly.
        // Populate with presets so the app launches without crashing.
        // Users can also add their own account via Add playlist -> Xtream Codes.
        AndyHax._portals.clear();
        for (int i = 0; i < NAMES.length; i++) {
            PortalModel pm = new PortalModel();
            pm.id_bClNU2OajLbxJWVW   = i + 1;
            pm.name_doQhQ7J9PskxUJv5 = NAMES[i];
            pm.url_rH6MnarmmBvhjdPh  = xc(HOST[i], USER[i], PASS[i]);
            AndyHax._portals.add(pm);
        }
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "ar.tvplayer.tv", "ar.tvplayer.tv.ui.MainActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                      | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private static String xc(String h, String u, String p) {
        return "xc:{\"h\":\"" + h + "\",\"u\":\"" + u
             + "\",\"p\":\"" + p + "\",\"o\":\"ts\"}";
    }
}
