package com.andyhax.haxsplash;

import android.content.Context;
import android.graphics.drawable.Drawable;
import java.util.ArrayList;

public class AndyHax {
    public static ArrayList<PortalModel> _portals = new ArrayList<>();
    public static int current_id;
    public static Drawable logo_drawable;
    public static native String Get(String str);
    public static native PortalModel GetById(int i);
    public static native void m1616Go(String str, Context context);
}
