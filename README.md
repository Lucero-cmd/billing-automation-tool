#  Invoice & Receipt Generator

A modern desktop app that generates professional PDF invoices and receipts,
tracks which invoices have been paid, and exports history for Excel.
Built with Python, CustomTkinter and ReportLab.

---

## Setup (one-time)

1. Make sure Python 3.9+ is installed. Check with:
   ```
   python --version
   ```

2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```

---

## Running the App

```
python app.py
```

---

## Features

- **Modern interface** with a sidebar, a New document page with a live
  summary panel, and a History dashboard. The layout adapts to the window
  size, so it still works when snapped to half the screen.
- **Invoices and receipts** with automatic numbering (`FT-DDMMYY-NN` for
  invoices, `FAT-DDMMYY-NN` for receipts).
- **Course library** with saved prices (inclusive of VAT) that fill in the
  amount and VAT rate automatically. Manage it from the course picker.
- **History dashboard** of up to 5,000 records, with totals for outstanding
  invoices and payments received this month. Search, filter by Outstanding,
  Paid or Receipts, and double-click a record to reload it into the form.
- **Mark Paid → Receipt.** Select an invoice in the history (or right-click it)
  to mark it as paid. The app creates a receipt dated today with its own
  receipt number and links the two records together.
- **Export CSV by date range.** Pick From and To dates, or use the quick
  buttons (this month, last month, this or last UK tax year). Optionally export
  only the records matching the current search and filter. Exporting never
  removes anything from your history.
- **Daily backups** of the history file, keeping the last 30 days.

---

## Adding Your Logo

Place a file named **`logo.png`** in the same folder as `app.py`.
Recommended size: **400 × 200 px**, transparent or white background.
The logo will be centred at the top of every PDF automatically.

If no logo file is found, the header renders without one.

---

## Output Files

PDFs are saved to the folder you choose in the app (default: `Documents`).
Each file name includes the document number and client, for example
`invoice_FT-301026-01_Jane_Smith.pdf`, so earlier PDFs are never overwritten.

---

## Where Data Is Stored

| What | Location |
|---|---|
| Counters, history, course library, last save folder | `~/fat_generator_settings.json` |
| Daily backups (last 30 days) | `~/fat_generator_backups/` |

`~` is your user folder, for example `C:\Users\<you>` on Windows.
Updating or replacing `app.py` does not affect your history.

---

## Customising Fixed Data

All company details (name, address, bank info, VAT number etc.) are defined
at the top of `app.py` in the `COMPANY` dictionary. Edit those values if
anything changes. The default course list is in `DEFAULT_COURSES`.

---

## Notes

- `tkinter` is bundled with Python on Windows, so no extra install is needed.
- On some Linux distros you may need: `sudo apt install python3-tk`
- The app works on Windows, macOS, and Linux.
- To build a Windows `.exe`: `pip install pyinstaller`, then
  `pyinstaller --onefile --windowed --add-data "logo.png;." --collect-data customtkinter app.py`
