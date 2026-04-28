# 臺灣天氣儀表板開發日誌 (Development Chat Log)

本專案是由使用者與 Antigravity (AI) 結對編程共同開發的成果。以下為完整的開發歷程與對話重點摘要，記錄了從零開始到最終高質感應用程式的迭代過程。

---

## 第一階段：專案初始化與架構設計

**使用者需求**：
使用者提供了一個大學作業的需求，目標是使用 Python 開發一個完整的三部分專案，透過中央氣象署 (CWA) 的 API 取得全台灣 7 天的天氣預報，將其儲存於 SQLite 資料庫中，最後透過 Streamlit 與 Folium 打造互動式地圖儀表板。並提供了專屬的 CWA API Key。

**AI 實作與遇到的挑戰**：
1. **API 連線異常 (SSL Error)**：
   在實作 `task1_fetch_weather.py` 時，我們發現 CWA 的 API 伺服器存在憑證問題（缺少主體金鑰識別碼）。為了解決這個問題，AI 決定在 `requests` 中加入 `verify=False` 參數，並使用 `urllib3.disable_warnings()` 隱藏警告，成功取得資料。
2. **資料結構解析**：
   一開始假設資料存放於 `Value` 欄位，但查看實際回傳的 JSON 後，發現 `F-D0047-091` 端點是提供每 12 小時一筆的資料，且區分為 `MaxTemperature` 與 `MinTemperature`。AI 重新撰寫了解析邏輯，將 12 小時的區間資料完美聚合為「每日最低與最高氣溫」。

---

## 第二階段：資料庫儲存與 UI 雛形

**使用者需求**：
確保擷取到的資料能正確寫入 SQLite (`task2_store_db.py`)，並建立初步的 Streamlit 介面 (`task3_app.py`)。使用者要求地圖上必須使用不同顏色的標記來區分平均氣溫：
- 🔵 藍色：< 20°C
- 🟢 綠色：20–25°C
- 🟡 黃色：25–30°C
- 🔴 紅色：> 30°C

**AI 實作**：
- **資料庫**：成功建立 `TemperatureForecasts` 表格，並寫入驗證腳本以確保 6 個指定地區（包含新增的東南部地區）的 42 筆資料（7天）正確儲存。
- **Folium 標記客製化**：由於 Folium 內建的標記不支援任意 HEX 顏色（如黃色），AI 巧妙地採用了 `folium.DivIcon` 搭配純 CSS 來繪製自訂顏色的圓形天氣標記。

---

## 第三階段：全面中文化與在地化

**使用者需求**：
> 「北部、中部、南部、東北部、東部及東南部地區，要有這些地區... 幫我把 UI 改成中文」

**AI 實作**：
- 更新 `task1_fetch_weather.py` 將原本的英文地區標籤替換為正體中文。
- 更新 `task2_store_db.py` 的驗證查詢語句。
- 全面翻譯 `task3_app.py` 中的頁面標題、副標題、圖例、圖表欄位、資料表表頭與工具提示 (Tooltip)，並將座標映射字典 (`REGION_COORDS`) 的鍵值同步為中文。

---

## 第四階段：質感大升級 (Premium UI Overhaul)

**使用者需求**：
> 「把UI做的有質感一點... 圖表用白色的不好看」

**AI 實作**：
為了徹底提升儀表板的質感，AI 進行了全面的前端視覺重構：
1. **解決白底圖表問題**：
   放棄了原本 Streamlit 預設的 `st.line_chart`，改為匯入 **Altair** (`alt.Chart`) 進行底層圖表客製化。強制關閉圖表背景 (`background='transparent'`)，並將網格與字體調整為深色系（如 `#94a3b8`），徹底解決突兀的白色區塊。
2. **全域深色主題強制套用**：
   動態生成了 `.streamlit/config.toml` 設定檔，從根源覆蓋 Streamlit 的預設亮色主題，確保資料表（DataFrame）與背景完美融合。
3. **Glassmorphism (毛玻璃) 與動畫設計**：
   在 `task3_app.py` 中寫入了大量 Premium CSS，包含：
   - 帶有發光效果的流體漸層標題（Animated hero header）。
   - 頂部的 6 個地區專屬 KPI 總覽卡片（包含漸層背景、陰影懸浮效果與專屬 Emoji）。
   - 指定使用高質感的 `Noto Sans TC` 與 `Inter` 無襯線字體。

---

## 第五階段：專案文件完善

**使用者需求**：
> 「改寫readme包含各個功能並附上截圖」

**AI 實作**：
- AI 使用瀏覽器代理（Browser Subagent）擷取了最終升級版的 Premium UI 畫面，並將其複製到專案資料夾命名為 `screenshot.png`。
- 重新撰寫了 `README.md`，詳細說明了三個腳本的功能特色、安裝與執行流程、以及針對 SSL 與 API Key 的注意事項。

---
**總結**：
透過流暢的 AI 協作，專案從基礎的 API 請求與資料庫寫入，一路進化為具有商業級質感的互動式全端視覺化儀表板，完美達成了大學作業的所有要求甚至超越了期待！
