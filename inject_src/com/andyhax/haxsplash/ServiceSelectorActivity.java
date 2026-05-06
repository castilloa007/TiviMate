package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

public class ServiceSelectorActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showXtreamForm();
    }

    private void showXtreamForm() {
        int pad = (int) (16 * getResources().getDisplayMetrics().density);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(pad, pad, pad, 0);

        final EditText host = field("Server", "http://ky-tv.cc:80", InputType.TYPE_TEXT_VARIATION_URI);
        final EditText user = field("Username", "", InputType.TYPE_CLASS_TEXT);
        final EditText pass = field("Password", "", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);

        layout.addView(host);
        layout.addView(user);
        layout.addView(pass);

        new AlertDialog.Builder(this)
            .setTitle("Xtream Codes")
            .setView(layout)
            .setCancelable(false)
            .setPositiveButton("Connect", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    String h = host.getText().toString().trim();
                    String u = user.getText().toString().trim();
                    String p = pass.getText().toString().trim();
                    if (h.isEmpty() || u.isEmpty() || p.isEmpty()) {
                        Toast.makeText(ServiceSelectorActivity.this, "Fill all fields", Toast.LENGTH_SHORT).show();
                        showXtreamForm();
                        return;
                    }
                    try {
                        AndyHax.m1616Go(xc(h, u, p), ServiceSelectorActivity.this);
                    } catch (Throwable t) {
                        openMain();
                    }
                    finish();
                }
            })
            .setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    openMain();
                    finish();
                }
            })
            .show();
    }

    private EditText field(String hint, String value, int variation) {
        EditText et = new EditText(this);
        et.setHint(hint);
        et.setText(value);
        et.setInputType(InputType.TYPE_CLASS_TEXT | variation);
        et.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        ));
        return et;
    }

    private void openMain() {
        Intent intent = new Intent();
        intent.setComponent(new ComponentName("ar.tvplayer.tv", "ar.tvplayer.tv.ui.MainActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
    }

    private static String xc(String h, String u, String p) {
        return "xc:{\"h\":\"" + h + "\",\"u\":\"" + u
             + "\",\"p\":\"" + p + "\",\"o\":\"ts\"}";
    }
}
