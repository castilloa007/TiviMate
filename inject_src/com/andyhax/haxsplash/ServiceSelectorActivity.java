package com.andyhax.haxsplash;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class ServiceSelectorActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Forward to the original LaunchActivity so all native
        // initialization in libhax.so runs as intended.
        Intent intent = new Intent(this, LaunchActivity.class);
        startActivity(intent);
        finish();
    }
}
