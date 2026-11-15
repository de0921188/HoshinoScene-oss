.class public final Lcom/omarea/vtools/AccessibilityAuthorization;
.super Ljava/lang/Object;

.method public static isAuthorized(Landroid/content/Context;)Z
    .locals 6
    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "accessibility_enabled"
    const/4 v2, 0x0
    invoke-static {v0, v1, v2}, Landroid/provider/Settings$Secure;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I
    move-result v1
    const/4 v2, 0x1
    if-ne v1, v2, :not_authorized
    const-string v1, "enabled_accessibility_services"
    invoke-static {v0, v1}, Landroid/provider/Settings$Secure;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :not_authorized
    const-string v1, ":"
    invoke-virtual {v0, v1}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0
    array-length v1, v0
    const/4 v2, 0x0
    :next_component
    if-ge v2, v1, :not_authorized
    aget-object v3, v0, v2
    invoke-static {v3}, Landroid/content/ComponentName;->unflattenFromString(Ljava/lang/String;)Landroid/content/ComponentName;
    move-result-object v3
    if-eqz v3, :advance
    invoke-virtual {v3}, Landroid/content/ComponentName;->getPackageName()Ljava/lang/String;
    move-result-object v4
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v5
    invoke-virtual {v4, v5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v4
    if-eqz v4, :advance
    invoke-virtual {v3}, Landroid/content/ComponentName;->getClassName()Ljava/lang/String;
    move-result-object v3
    const-string v4, "com.omarea.vtools.AccessibilitySceneMode"
    invoke-virtual {v4, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-nez v3, :authorized
    :advance
    add-int/lit8 v2, v2, 0x1
    goto :next_component
    :authorized
    const/4 v0, 0x1
    return v0
    :not_authorized
    const/4 v0, 0x0
    return v0
.end method
