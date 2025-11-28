# J97 Packing - Qt UI (converted from TSX)

This folder contains a first-pass conversion of your React `App` layout into a Qt Designer `.ui` file and a simple preview loader using PySide6.

Files created:
- `app_mainwindow.ui` — Qt Designer UI representing the top-level layout (sidebar + main area with pages).
- `preview_loader.py` — small script to load and preview the `.ui` using PySide6.
- `requirements.txt` — minimal dependency spec for previewing.

Notes on conversion
- The React `App` you provided is an app shell (a `Sidebar` and a main area with multiple pages). I converted that into a `QMainWindow` with a left `QWidget` (sidebar) and a `QStackedWidget` for pages.
- Each React page (Dashboard, Search, MonthlyTicket, EntryExitHistory, Statistics, Settings) is represented as a separate page (QWidget) in the `QStackedWidget` with a placeholder `QLabel`.
- Navigation buttons are created in the sidebar (`QPushButton` for each page). These don't have signal wiring in the .ui; you can connect them in code to switch `stackedPages.setCurrentIndex(...)`.

Next steps / how I can help
- If you provide the `Sidebar` and each page's TSX files (the components), I will:
  - map layout and widgets in each page to proper Qt widgets,
  - transfer important styles to Qt stylesheets where possible,
  - wire navigation buttons to switch pages (generate a small Python app that connects them),
  - or implement a converter script to process multiple TSX files automatically.

Preview (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\preview_loader.py
```

Update: `preview_loader.py` now wires the sidebar buttons to switch pages, populates the Dashboard with sample stats and availability progress bars, and attempts to load camera images from public URLs (falls back to placeholders if network fails).
Update: `preview_loader.py` now loads separate `.ui` files from the `ui_pages/` folder, wires the sidebar buttons to switch pages, populates the Dashboard with sample stats and availability progress bars, and attempts to load camera images from public URLs (falls back to placeholders if network fails).

How navigation is wired
- Sidebar buttons in the main `.ui` are named: `btnDashboard`, `btnSearch`, `btnMonthly`, `btnHistory`, `btnStatistics`, `btnSettings`.
- `preview_loader.py` now loads the page `.ui` files from `ui_pages/` and adds them to the main `QStackedWidget` (`stackedPages`). The sidebar buttons are connected to these loaded pages at runtime.

Files added
- `ui_pages/dashboard.ui` — Dashboard page (stats, availability, camera placeholders, barrier buttons).
- `ui_pages/search.ui` — Search Vehicle page placeholder.
- `ui_pages/monthly.ui` — Monthly Ticket page placeholder.
- `ui_pages/history.ui` — Entry/Exit History page placeholder.
- `ui_pages/statistics.ui` — Statistics page placeholder.
- `ui_pages/settings.ui` — Settings page placeholder.

Notes & next steps
- Each page is now a separate `.ui` file so you can open them individually in Qt Designer and edit layout/widgets easily.
- To complete pixel-perfect conversion, paste TSX for `Sidebar` and each page; I will convert styled elements and add precise object names and styles into each page `.ui`.
- If you want I can also create a small `app.py` that loads the `.ui` files and exposes signals (barrier open/close) for integration with backend hardware/APIs.

Limitations
- This is a structural conversion only. Complex React components, custom hooks, or third-party UI components will need manual mapping.
- CSS-to-Qt stylesheet translation is partial; I can do a best-effort mapping if you supply relevant CSS classes or the generated CSS from your build.
