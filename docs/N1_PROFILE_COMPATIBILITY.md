# N1 性能配置相容性修正

## 原因與修正

Alpha14 Lite 的 `a.b11.d()` 僅接受 manifest 的作者名稱 `SCENE9`。
實機下載的 HP、EP、LP 配置使用 `SCENE N1`，因此即使配置下載完整，
仍無法啟用性能調節，浮動面板也無法切換模式。

修正接受 `SCENE9` 與 `SCENE N1`，保留原有的配置來源、profile.json
存在性檢查及外部模組處理。不修改 CPU、GPU、溫控或調節參數。

只改手機 manifest 的作者欄位是暫時處理；再次下載或切換配置會覆寫它。
應使用修正後的程式，讓新下載的原始配置直接通過檢查。

## 還原 APK 的修補方式

此專案的部分反編譯 Java 仍有未還原方法，測試包可保留原 APK 的資源、
Manifest、原生程式庫與 assets，只重新組譯修正的 Smali。

```powershell
java -jar tools/apktool.jar d -r -f <原始APK> -o build/profile-fix
python tools/patch_performance_profile.py build/profile-fix
python tools/patch_accessibility_state.py build/profile-fix
python tools/patch_accessibility_authorization.py build/profile-fix
python tools/localize_ui_overrides.py build/profile-fix
java -jar tools/apktool.jar b build/profile-fix -o build/profile-fix-unsigned.apk
```

產物仍需 zipalign 與 apksigner 簽署。安裝前核對原版與修復版的簽章；
若不同，不能直接覆蓋。更換前須備份設定，取得同意後才卸載，
還原時使用新 UID 修正資料擁有者與 SELinux 標籤，並重新授予 Root。

## 已執行的檢查

- 實機確認線上配置來源為 `SOURCE_SCENE_ONLINE`，下載的作者為 `SCENE N1`。
- 核對已安裝 Alpha14 Lite 的 Smali 也有舊名稱限制。
- 修補工具的冪等性、不相容輸入拒絕與修改範圍檢查通過。
- Apktool 組譯成功，修復 APK 的 v2、v3 簽章驗證通過。
- 最終版本的 Manifest、resources.arsc、原生程式庫與 assets 均與原版相同，
  因此資源 ID、調節核心與配置腳本沒有變更。四個版面 XML 的字串池已繁體化，
  並以 aapt2 逐一解析驗證；DEX 重新組譯後通過 APK 簽章驗證。
- 設定與配置已備份，重新安裝後核對 manifest、profile、global 與 powercfg
  設定還原內容相同。
- HP、EP、LP 均重新下載原始作者 `SCENE N1` 的配置，並於實機驗證可啟用，
  這輪逐項驗證沒有出現要求激活無障礙的提示。最後保留 EP。
- 模擬測試、能耗測試及自訂監視器已實機核對顯示；未啟動壓力測試。

## 無障礙反覆提示

實機曾出現系統顯示服務已啟用且已綁定，但 App 顯示尚未激活的狀況。
先前僅加入連線旗標的版本仍收到使用者回報，因此最終版本同時核對：
框架服務清單、服務連線回呼，以及系統已授權的確切元件名稱。
系統授權核對支援完整及簡寫 ComponentName，只讀設定，不自動授權。
授權與服務是否持續健康運作是不同狀態，仍須注意實機後續回報。

重新安裝時 Root 管理器曾快取舊 UID，實機日誌核對並刷新至新 UID 後恢復。
無障礙設定中相同元件的簡寫／完整名稱重複登記已備份並正規化。

## 繁體顯示

功能選單的「模擬測試／能耗測試」、能耗 FAQ、監視器入口與自訂版面
包含未走語系字串的硬編碼文字。修補指定 XML 的字串池與指定活動的顯示常數，
保留 XML 節點、索引、屬性資源 ID 與 resources.arsc。
監視器的「刷新間隔／縮放」前綴另外依精確文字修補。

最終安裝包保存於 `release/星野SCENE-N1-繁體修正版.apk`。
EP 自身會建議切換配置後重新啟動手機；本次未替使用者重開機，
未驗證重開機後的狀態，也未量測各配置完整的性能與功耗效果。

本機修復包及資料備份位於忽略的 `build/performance-fix/`，不應提交私人設定備份。
