package com.omarea.vtools;

/** Check the exact granted component when the framework's service list is stale. */
public final class AccessibilityAuthorization {
    private AccessibilityAuthorization() {}

    public static boolean isAuthorized(android.content.Context context) {
        android.content.ContentResolver resolver = context.getContentResolver();
        if (android.provider.Settings.Secure.getInt(resolver, "accessibility_enabled", 0) != 1) {
            return false;
        }
        String enabled = android.provider.Settings.Secure.getString(resolver, "enabled_accessibility_services");
        if (enabled == null) return false;
        for (String value : enabled.split(":")) {
            android.content.ComponentName component = android.content.ComponentName.unflattenFromString(value);
            if (component != null && context.getPackageName().equals(component.getPackageName())
                    && "com.omarea.vtools.AccessibilitySceneMode".equals(component.getClassName())) {
                return true;
            }
        }
        return false;
    }
}
