package com.andyhax.haxsplash;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

public class ServiceSelectorActivity extends Activity {

    private static final String[] PRESET_NAMES = {"Papai", "Mel", "Ivan"};
    private static final String[] PRESET_HOST  = {
        "http://ky-tv.cc:80", "http://ky-tv.cc:80", "http://ky-tv.cc:80"};
    private static final String[] PRESET_USER  = {
        "AEGVXXZVZV", "Melli3B3llie@832", "icastil@1997"};
    private static final String[] PRESET_PASS  = {
        "236267373", "Fir3F@xed2020", "TheFireF@x3733"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        populatePortals();
        launchMain();
    }

    private static void populatePortals() {
        AndyHax._portals.clear();
        for (int i = 0; i < PRESET_NAMES.length; i++) {
            PortalModel pm = new PortalModel();
            pm.id_bClNU2OajLbxJWVW   = i + 1;
            pm.name_doQhQ7J9PskxUJv5 = PRESET_NAMES[i];
            pm.url_rH6MnarmmBvhjdPh  = buildXcUrl(PRESET_HOST[i], PRESET_USER[i], PRESET_PASS[i]);
            AndyHax._portals.add(pm);
        }
        // Empty-URL "Custom" entry so TiviMate falls through to its manual form.
        PortalModel custom = new PortalModel();
        custom.id_bClNU2OajLbxJWVW   = PRESET_NAMES.length + 1;
        custom.name_doQhQ7J9PskxUJv5 = "Custom...";
        custom.url_rH6MnarmmBvhjdPh  = "";
        AndyHax._portals.add(custom);
    }

    private static String buildXcUrl(String host, String user, String pass) {
        return "xc:{\"h\":\"" + host + "\",\"u\":\"" + user
             + "\",\"p\":\"" + pass + "\",\"o\":\"ts\"}";
    }

    private void launchMain() {
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "ar.tvplayer.tv", "ar.tvplayer.tv.ui.MainActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                      | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
