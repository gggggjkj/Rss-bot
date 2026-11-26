# 每日 RSSHub + AI 摘要

以 Python 收集科技與 AI RSS，透過 DeepSeek 產生繁體中文摘要，再推送到 Discord。GitHub Actions 每天台灣時間 14:00（UTC 06:00）執行，也支援手動執行。排程可能延遲。

## 設定

1. 將本專案放入自己的 GitHub repository，並在 repository 的 **Settings → Secrets and variables → Actions** 新增：
   - `DEEPSEEK_API_KEY`：DeepSeek API 金鑰。
   - `DISCORD_WEBHOOK_URL`：要接收摘要的 Discord 頻道 webhook 網址。
   - `RSSHUB_BASE_URL`：選填，現有 RSSHub 實例的基底網址；如果實例的存取憑證包含在網址中，也請放在此 Secret。
2. 編輯 `config.json` 的 `feeds`。內建三個科技與 AI 原生 RSS；RSSHub 來源可加入 `{"name": "來源名稱", "route": "/你的/RSSHub/路由"}`。也可以直接用 `url` 加入完整 RSS 或 Atom 網址。只有在不含憑證時才把網址寫入設定檔。
3. 在 GitHub 的 **Actions** 頁面選擇 **Daily RSS AI digest → Run workflow** 手動測試，確認 Discord 收到訊息。排程需要 workflow 位於 repository 的預設分支，且 Actions 已啟用。

請勿將金鑰或 webhook 提交到 repository，或張貼在公開位置。DeepSeek 使用量可能產生費用；請先確認供應商的帳戶與計費設定。

## 本機執行

需要 Python 3.10 以上，無第三方依賴。先預覽來源（不呼叫 DeepSeek 或 Discord）：

```bash
python3 digest.py --dry-run
```

要實際推送，請在終端機安全設定 `DEEPSEEK_API_KEY` 和 `DISCORD_WEBHOOK_URL` 環境變數，再執行 `python3 digest.py`。如使用 RSSHub 路由，也可設定 `RSSHUB_BASE_URL`。自訂設定檔可用 `--config path/to/config.json`。網路環境必須能連線到來源、DeepSeek 和 Discord。

執行測試：

```bash
python3 -m unittest discover -s tests -v
```

## 行為與限制

- 僅處理執行當下往前 24 小時且帶有可解析日期的文章；未提供日期、未來日期或不含 HTTP(S) 連結的項目會略過。依網址去重，按發布時間由新到舊取最多 20 篇；每篇內容最多 1,200 字，可在設定檔調整。
- 模型只收到標題、來源與 RSS 內文，不會抓取文章全文。摘要及原文連結會拆成多則 Discord 訊息，並停用自動提及。沒有新文章時會發送通知。
- 單一來源失敗不影響其他來源；全部來源失敗、DeepSeek 失敗或 Discord 發送失敗時工作會失敗。若多則訊息中途失敗，先前已發送的訊息不會回收。
- 不保存執行狀態。排程延遲、漏跑或手動重跑時，可能遺漏或重複文章；RSSHub 實例可用性及各網站 feed 內容可能變動。
