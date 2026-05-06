package com.andyhax.haxsplash;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;

public class LaunchActivity extends Activity {
    @Override protected native void onCreate(Bundle bundle);
    @Override protected native void attachBaseContext(Context context);
}
