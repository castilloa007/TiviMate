package com.andyhax.hook;

import android.app.Application;
import android.content.Context;

public class HookApplication extends Application {
    public static native String a(String str);
    public static native void inject(String name, String xcUrl);
    protected native void attachBaseContext(Context context);
}
