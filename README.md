#  Invoice & Receipt Generator

A modern desktop app that generates professional PDF invoices and receipts.

---

## Setup (one-time)

1. Make sure Python 3.9+ is installed — check with:
   ```
   python --version
   ```

2. Open the `fat_generator` folder in VS Code.

3. Open the integrated terminal (`` Ctrl+` ``) and run:
   ```
   pip install -r requirements.txt
   ```

---

## Running the App

```
python app.py
```

---

## Adding Your Logo

Place a file named **`logo.png`** in the same folder as `app.py`.
Recommended size: **400 × 200 px**, transparent or white background.
The logo will be centred at the top of every PDF automatically.

If no logo file is found, the header renders without one.

---

## Output Files

PDFs are saved to the folder you choose in the app (default: `Documents`).
Files are named after the document number, e.g. `FT-060426-01.pdf`.

---

## Customising Fixed Data

All company details (name, address, bank info, VAT number etc.) are defined
at the top of `app.py` in the `COMPANY` dictionary. Edit those values if
anything changes.

---

## Notes

- `tkinter` is bundled with Python on Windows — no extra install needed.
- On some Linux distros you may need: `sudo apt install python3-tk`
- The app works on Windows, macOS, and Linux.
