package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.os.Bundle;
import android.widget.Toast;
import java.lang.reflect.Field;
import java.util.ArrayList;

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
                        // Build a PortalModel and add it to AndyHax._portals
                        Class<?> portalClass = Class.forName("com.andyhax.haxsplash.PortalModel");
                        Object portal = portalClass.newInstance();

                        Field idField   = portalClass.getField("id_bClNU2OajLbxJWVW");
                        Field nameField = portalClass.getField("name_doQhQ7J9PskxUJv5");
                        Field urlField  = portalClass.getField("url_rH6MnarmmBvhjdPh");

                        idField.set(portal, which + 1);
                        nameField.set(portal, NAMES[which]);
                        urlField.set(portal, XC_URLS[which]);

                        // Set AndyHax._portals to a fresh list with just this portal
                        Class<?> andyHaxClass = Class.forName("com.andyhax.haxsplash.AndyHax");
                        Field portalsField = andyHaxClass.getField("_portals");
                        ArrayList<Object> list = new ArrayList<>();
                        list.add(portal);
                        portalsField.set(null, list);

                        // Set current_id to match
                        Field currentIdField = andyHaxClass.getField("current_id");
                        currentIdField.set(null, which + 1);

                        // Call AndyHax.m1616Go() to navigate into the app
                        andyHaxClass.getMethod("m1616Go", String.class, android.content.Context.class)
                                    .invoke(null, XC_URLS[which], ServiceSelectorActivity.this);

                        finish();
                    } catch (Exception e) {
                        Toast.makeText(ServiceSelectorActivity.this,
                            "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                        e.printStackTrace();
                    }
                }
            })
            .setCancelable(false)
            .show();
    }
}
