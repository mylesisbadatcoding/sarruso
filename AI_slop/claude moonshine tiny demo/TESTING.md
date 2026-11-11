# Testing the Moonshine Tiny demo on Linux

Follow these steps once, in order. The whole thing takes about 10 minutes, plus a download on the first run.

## 0. What you need

- A Linux laptop with a working microphone (built-in is fine)
- Python 3.10 or newer (`python3 --version`)
- Google Chrome or Firefox
- Internet access for the first run only (the model downloads from Hugging Face, about 100 MB)
- Optional, for MP3/M4A uploads: `ffmpeg`

Install the system pieces on Debian/Ubuntu/Mint:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg
```

Fedora: `sudo dnf install python3 ffmpeg`. Arch: `sudo pacman -S python ffmpeg`.

## 1. Get the files

Clone the repo (or pull, if you already have it) and go to this folder:

```bash
git clone https://github.com/mylesisbadatcoding/sarruso.git
cd sarruso/"AI_slop/claude moonshine tiny demo"
```

If you already have the repo: `git pull`, then `cd` into the same folder.

## 2. Check the layout first (no model download)

This runs a fake engine. It proves the server and page work before you download anything.

```bash
MOONSHINE_STUB=1 ./run.sh
```

You should see `Open http://127.0.0.1:8000 in your browser`. Leave it running and open that address.

Check that:

- [ ] The badge at the top right says `moonshine/tiny` or `stub`. It is **not** blank or stuck on `loading…`.
- [ ] The **Entries** table shows "No entries yet".
- [ ] Clicking **Start recording** asks for mic permission. Allow it.
- [ ] While you talk, the **Live** box fills with `stub stub stub…`. The status line shows seconds buffered.
- [ ] Clicking **Stop** adds a row to the Entries table with the audio length and metrics.

Stop the server with `Ctrl+C`.

## 3. Run the real model

```bash
./run.sh
```

The first run creates `.venv`, installs the packages, and downloads the Moonshine Tiny weights. It may pause for a minute with no output while downloading. Wait for the `Open http://...` line.

Open **http://127.0.0.1:8000** in Chrome or Firefox.

## 4. Test the live path

1. Click **● Start recording** and allow the microphone.
2. Say a sentence slowly, for example: *"The quick brown fox jumps over the lazy dog."*
3. Watch the **Live** box. Text should appear within about a second and get more complete as you talk.
4. Click **■ Stop**.
5. A new row appears in **Entries** with:
   - **Text** matching what you said (small mistakes are normal for Tiny)
   - **Audio** close to how long you spoke
   - **Inference**, **RTF**, **Tok/s**, **First text**, **Avg pass**
   - **Reference** box empty

If the text is blank or nonsense, see troubleshooting below.

## 5. Test WER

WER compares what the model heard against text you know is correct.

1. Before recording, type the exact sentence you will say into the **Reference text for WER** box at the top.
2. Record the same sentence, then stop.
3. The new entry shows a **WER** (lower is better; 0% is a perfect match).

To add a reference afterwards: type the correct text into the **Reference** box in that row and press Enter or click elsewhere. WER updates.

## 6. Test upload

1. Click **Upload audio** and pick a WAV, MP3, or M4A file (about 10–30 seconds of speech works well).
2. Optional: type its correct transcript in **Reference for uploaded file**.
3. An entry appears with `upload:<filename>` as its source.

## 7. Test the rest

- [ ] **Export CSV** downloads a file with one row per entry and all metrics.
- [ ] **✕** on a row deletes that entry.
- [ ] **Clear all** asks for confirmation, then empties the table.
- [ ] Reload the page. Your entries are still there (they're stored in `data/entries.db`).
- [ ] Speak for longer than 30 seconds without stopping. The first 30 seconds should be saved as an entry automatically, and the rest after you stop.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Microphone error: Permission denied` or no prompt | Click the lock icon in the address bar, set Microphone to *Allow*, reload. |
| No mic prompt at all | Open the page via `http://127.0.0.1:8000`, not an IP address. Browsers only allow mic access on localhost or HTTPS. |
| Mic works but nothing appears | Check the input device in your sound settings. Try a headset mic. Speak closer to it. |
| `WebSocket error. Is the server running?` | The server stopped or crashed. Check the terminal where `./run.sh` is running. |
| Download fails or hangs on the first run | Check your internet connection and try again. You need access to `huggingface.co`. |
| `Could not decode audio` on upload | Install `ffmpeg`, or convert the file to WAV (16 kHz mono is safest). |
| Port 8000 already in use | Run `PORT=8010 ./run.sh` and open `http://127.0.0.1:8010`. |
| Text is slow to appear | Normal on older laptops. Check the **Avg pass** and **RTF** columns: RTF below 1 means faster than real time. |

If something fails, copy the terminal output and the entry or error message from the page, and send them to me.
