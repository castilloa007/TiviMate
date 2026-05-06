package com.andyhax.haxsplash;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;

public class ServiceSelectorActivity extends Activity {

    private static final String PREFS   = "svc_sel";
    private static final String KEY_URL = "saved_url";

    // Preset accounts (name shown in list)
    private static final String[] PRESET_NAMES = { "Papai", "Mel", "Ivan" };
    private static final String[] PRESET_HOST  = {
        "http://ky-tv.cc:80", "http://ky-tv.cc:80", "http://ky-tv.cc:80" };
    private static final String[] PRESET_USER  = {
        "AEGVXXZVZV", "Melli3B3llie@832", "icastil@1997" };
    private static final String[] PRESET_PASS  = {
        "236267373",  "Fir3F@xed2020",    "TheFireF@x3733" };

    // Dialog list items
    private static final String[] MENU = {
        "Papai", "Mel", "Ivan", "Add custom account", "Change account"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String savedUrl = prefs.getString(KEY_URL, null);

        if (savedUrl != null) {
            // Already have a saved account — go straight in
            injectAndLaunch(savedUrl);
        } else {
            showMainMenu();
        }
    }

    private void showMainMenu() {
        new AlertDialog.Builder(this)
            .setTitle("Select Account")
            .setItems(MENU, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    switch (which) {
                        case 0: case 1: case 2:
                            // Papai / Mel / Ivan
                            String xcUrl = buildXcUrl(
                                PRESET_HOST[which], PRESET_USER[which], PRESET_PASS[which]);
                            saveAndLaunch(xcUrl);
                            break;
                        case 3:
                            showCustomForm(null);
                            break;
                        case 4:
                            // Clear saved account and show selector again
                            getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                                .edit().remove(KEY_URL).apply();
                            showMainMenu();
                            break;
                    }
                }
            })
            .setCancelable(false)
            .show();
    }

    private void showCustomForm(final String prefillXcUrl) {
        // Parse prefill if editing existing
        String[] prefill = prefillXcUrl != null
            ? parseXcUrl(prefillXcUrl)
            : new String[]{"", "", ""};

        int pad = (int)(16 * getResources().getDisplayMetrics().density);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(pad, pad, pad, 0);

        final EditText etHost = makeField("Server URL  (e.g. http://server.com:8080)", prefill[0]);
        final EditText etUser = makeField("Username", prefill[1]);
        final EditText etPass = makeField("Password", prefill[2]);
        etPass.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);

        layout.addView(label("Server URL"));
        layout.addView(etHost);
        layout.addView(label("Username"));
        layout.addView(etUser);
        layout.addView(label("Password"));
        layout.addView(etPass);

        new AlertDialog.Builder(this)
            .setTitle("Custom Account")
            .setView(layout)
            .setPositiveButton("Connect", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface d, int w) {
                    String host = etHost.getText().toString().trim();
                    String user = etUser.getText().toString().trim();
                    String pass = etPass.getText().toString().trim();
                    if (host.isEmpty() || user.isEmpty() || pass.isEmpty()) {
                        Toast.makeText(ServiceSelectorActivity.this,
                            "All fields are required", Toast.LENGTH_SHORT).show();
                        showCustomForm(prefillXcUrl);
                        return;
                    }
                    saveAndLaunch(buildXcUrl(host, user, pass));
                }
            })
            .setNegativeButton("Back", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface d, int w) { showMainMenu(); }
            })
            .setCancelable(false)
            .show();
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private static String buildXcUrl(String host, String user, String pass) {
        return "xc:{\"h\":\"" + host + "\",\"u\":\"" + user +
               "\",\"p\":\"" + pass + "\",\"o\":\"ts\"}";
    }

    /** Parse xc:{...} back to [host, user, pass] */
    private static String[] parseXcUrl(String xcUrl) {
        try {
            String json = xcUrl.substring(3); // strip "xc:"
            String h = extract(json, "\"h\":\"");
            String u = extract(json, "\"u\":\"");
            String p = extract(json, "\"p\":\"");
            return new String[]{h, u, p};
        } catch (Exception e) {
            return new String[]{"", "", ""};
        }
    }
    private static String extract(String json, String key) {
        int s = json.indexOf(key) + key.length();
        int e = json.indexOf('"', s);
        return json.substring(s, e);
    }

    private EditText makeField(String hint, String text) {
        EditText et = new EditText(this);
        et.setHint(hint);
        et.setText(text);
        et.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        et.setLayoutParams(new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return et;
    }

    private TextView label(String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        int pad = (int)(4 * getResources().getDisplayMetrics().density);
        tv.setPadding(0, pad, 0, 0);
        return tv;
    }

    private void saveAndLaunch(String xcUrl) {
        getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KEY_URL, xcUrl).apply();
        injectAndLaunch(xcUrl);
    }

    private void injectAndLaunch(String xcUrl) {
        // Write directly to TiviMate's SQLite DB so the playlist persists
        try {
            insertPlaylistToDb(xcUrl);
        } catch (Exception e) {
            e.printStackTrace();
        }

        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "ar.tvplayer.tv", "ar.tvplayer.tv.ui.MainActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    /**
     * Insert (or replace) a single Xtream Codes playlist entry into
     * TiviMate's Room database.
     * Table: playlists
     * We determine the exact column layout by inspecting the live schema at runtime.
     */
    private void insertPlaylistToDb(String xcUrl) throws Exception {
        String[] parts = parseXcUrl(xcUrl);
        String host = parts[0], user = parts[1], pass = parts[2];
        String name = resolveName(user);

        // DB lives at /data/data/ar.tvplayer.tv/databases/tvplayer_db
        File dbFile = new File(getApplicationInfo().dataDir, "databases/tvplayer_db");
        if (!dbFile.exists()) return;

        SQLiteDatabase db = SQLiteDatabase.openDatabase(
            dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READWRITE);

        // Inspect actual columns so we don't crash on schema mismatch
        android.database.Cursor pragma = db.rawQuery(
            "PRAGMA table_info(playlists)", null);
        StringBuilder cols = new StringBuilder();
        StringBuilder vals = new StringBuilder();
        java.util.Map<String, String> row = new java.util.LinkedHashMap<>();
        while (pragma.moveToNext()) {
            String col = pragma.getString(pragma.getColumnIndex("name"));
            String dflt = pragma.getString(pragma.getColumnIndex("dflt_value"));
            // Map known semantic column names → values
            String v = null;
            String cl = col.toLowerCase();
            if (cl.contains("name"))                      v = "'" + sqlEsc(name) + "'";
            else if (cl.contains("url") || cl.contains("xc") || cl.contains("src"))
                                                          v = "'" + sqlEsc(xcUrl) + "'";
            else if (cl.contains("host") || cl.equals("h")) v = "'" + sqlEsc(host) + "'";
            else if (cl.contains("user"))                 v = "'" + sqlEsc(user) + "'";
            else if (cl.contains("pass") || cl.contains("pwd")) v = "'" + sqlEsc(pass) + "'";
            else if (cl.contains("type") || cl.contains("kind")) v = "2"; // 2 = Xtream
            else if (cl.contains("enabled") || cl.contains("active")) v = "1";
            else if (cl.contains("sort") || cl.contains("order") || cl.contains("pos")) v = "0";
            else if (cl.contains("id") && !cl.contains("tvg")) v = null; // autoincrement
            else if (dflt != null)                        v = dflt;
            else                                          v = "''";

            if (v != null) {
                row.put(col, v);
            }
        }
        pragma.close();

        if (row.isEmpty()) { db.close(); return; }

        String colList = android.text.TextUtils.join(", ", row.keySet());
        String valList = android.text.TextUtils.join(", ", row.values());
        db.execSQL("INSERT OR REPLACE INTO playlists (" + colList + ") VALUES (" + valList + ")");
        db.close();

        Toast.makeText(this, "Playlist saved: " + name, Toast.LENGTH_SHORT).show();
    }

    private String resolveName(String user) {
        for (int i = 0; i < PRESET_USER.length; i++) {
            if (PRESET_USER[i].equals(user)) return PRESET_NAMES[i];
        }
        return user; // use username as name for custom accounts
    }

    private static String sqlEsc(String s) {
        return s.replace("'", "''");
    }
}
