# Unknown Face Detection & Alert System

An AI-powered surveillance MVP: a webcam feed is scanned in real time for faces. Known faces are recognized by name; any unrecognized face triggers an automated alert (Email / Telegram / Google Sheets log) via n8n.

## Architecture

```text
[Webcam] --> [Python: OpenCV + face_recognition]
                  |
                  |  known face  -> label + green box (no alert)
                  |  unknown face-> label + red box + save snapshot
                  v
        [POST image + metadata] --> [n8n Webhook]
                                          |
                                +---------+---------+
                                |         |         |
                          [Telegram] [Email]  [Google Sheets log]
```

## 1. Setup (Python side)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** If you experience issues installing `face_recognition` or `dlib` on Windows, install a prebuilt `dlib` wheel matching your Python version before running `pip install face_recognition`.

## 2. Add Known Faces

Create one subfolder per known person, with 2-3 clear photos each:

```text
known_faces/
    Utkarsh/
        img1.jpg
        img2.jpg
```

Then build the encodings database:

```bash
python encode_faces.py
```

## 3. Configure the Webhook

Create a `.env` file in the root directory and add your webhook URL:

```env
N8N_WEBHOOK_URL=https://your-workspace.n8n.cloud/webhook/unknown-face
CAMERA_INDEX=1
TOLERANCE=0.6
ALERT_COOLDOWN_SECONDS=30
```

## 4. Set up n8n

1. Run n8n (Cloud or local).
2. Go to **Workflows → Import from File** and import `n8n_workflow.json`.
3. Open the **Webhook** node, copy the **Production URL**, and paste it into your `.env` file.
4. Add your credentials to the alerting nodes (Email, Telegram, etc.).
5. Activate the workflow (toggle top-right).

## 5. Run Detection

```bash
python detect_faces.py
```

- **Green box + name:** Recognized person, no alert.
- **Red box + "Unknown":** Triggers a snapshot + webhook alert (rate-limited by `ALERT_COOLDOWN_SECONDS` in `.env` to prevent spam).
- Press `q` to quit the preview window.
