# 影片素材網 Design Resources Site

> 一個自訂API、瀏覽器面向的web server

## 原理
收到瀏覽器發出的HTTP request後，根據自訂的API來抓取資料庫、渲染前端頁面和讀取串流影片，並回傳瀏覽器。

## 功能

- 每樣素材下方有留言區能夠做評論
- 要登入後才能留言
- 透過影片串流來預覽影片素材
- 使用Multithread來同時處理多個request

## 環境設定

- Python 3.8 以上
- 所需 python package:
    - opencv-python==4.6.0.66
    - numpy==1.23.5

## 執行方式

1. 執行 server.py （`python server.py`）
2. 使用瀏覽器（推薦使用 Chrome or Edge）瀏覽 http://localhost:12345 ，便可開始瀏覽。

## 主要功能之實作方式

- 留言板功能
    - 使用 Python 內建之 SQLite 作為資料庫來管理留言
    - 透過處理 HTTP POST method 來新增留言
    - 在留言輸入框自動帶入已登入的使用者名稱
    - 在頁面被 request 前先 render HTML 中的留言區
- 註冊登入登出功能
    - 使用 Python 內建之 SQLite 作為資料庫來管理使用者資訊
    - 透過處理 HTTP POST method 來實現登入或註冊功能
    - 透過 Header 中的 Set-Cookie 欄位來記錄目前登入session與實作登出功能
- Multithread
    - 使用 Python 的 Thread 套件，在建立TCP連線同時為其新增執行緒
    - 當執行緒結束執行便經由 Python 的 Garbage Collection 機制回收記憶體
- 影片串流
    - 使用 HTTP 中 Content-type: multipart/x-mixed-replace 的機制來實作
    - 透過 OpenCV 套件來實時讀取影片中的影像幀
    - 將影像幀透過 HTTP 傳送至 Browser，使用新的影像幀來替換舊的幀，達成影片串流的功能
    - 按下 Replay 按鈕，便重新由第一幀開始讀取及傳送。

## DEMO影片

請見 DEMO.mp4

## 素材來源

- Video 1 (Walking Dog)
    
    [https://www.videvo.net/video/young-couple-walking-dog-at-sunset/457886/](https://www.videvo.net/video/young-couple-walking-dog-at-sunset/457886/)
    
- Video 2 (Golden Liquid)
    
    [https://www.videvo.net/video/golden-liquid-poured-into-bowl/457881/](https://www.videvo.net/video/golden-liquid-poured-into-bowl/457881/)
