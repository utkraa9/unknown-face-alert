# Unknown Face Detection & Alert System

An AI-powered surveillance MVP: a webcam feed is scanned in real time for faces.
Known faces (added by you) are recognized by name; any unrecognized face triggers
an automated alert (Telegram + Email + Google Sheets log) via n8n.

## Architecture

```
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
cd unknown-face-alert
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note on `face_recognition` / `dlib` install issues (common on Windows):**
> - Easiest path: `conda install -c conda-forge dlib` then `pip install face_recognition`
> - Or install a prebuilt dlib wheel matching your Python version before `pip install face_recognition`
> - On Linux/Mac, `pip install dlib` usually works directly (needs `cmake` + a C++ compiler).
> If you're really stuck under time pressure, an alternative is swapping `face_recognition`
> for `mediapipe` or `insightface`, but the code above is the fastest path for a hackathon demo.

## 2. Add known faces

Create one subfolder per known person, with 2-3 clear photos each:

```
known_faces/
    Alice/
        img1.jpg
        img2.jpg
    Bob/
        img1.jpg
```

Then build the encodings database:

```bash
python encode_faces.py
```

This creates `encodings.pickle`.

## 3. Configure the webhook

```bash
cp .env.example .env
# edit .env and set N8N_WEBHOOK_URL to your n8n webhook (see step 4)
```

## 4. Set up n8n

1. Run n8n (cloud, Docker, or `npx n8n`).
2. In n8n, go to **Workflows → Import from File** and import `n8n_workflow.json`.
3. Open the **Webhook** node → copy the **Production URL** (or Test URL while building)
   and paste it into your `.env` as `N8N_WEBHOOK_URL`. The path is `/webhook/unknown-face`.
4. Add your credentials on the Telegram / Email / Google Sheets nodes (or just delete
   the ones you don't need — even a single Telegram or Email node is enough for the MVP).
5. Activate the workflow (toggle top-right).

**Fastest alert option for a demo:** just keep the Telegram node — create a bot via
[@BotFather](https://t.me/botfather), get your chat ID, and you'll get instant phone
alerts, which looks great live during judging.

## 5. Run detection

```bash
python detect_faces.py
```

- Green box + name = recognized person, no alert.
- Red box + "Unknown" = triggers a snapshot + webhook alert (rate-limited by
  `ALERT_COOLDOWN_SECONDS` in `.env` so it doesn't spam on every frame).
- Press `q` to quit the preview window.

## 6. Demo tips (for your video/pitch)

1. Show a known person walking into frame → green box, no alert.
2. Show an unrecognized person → red box, then cut to your phone/email getting
   the Telegram/Email alert with the snapshot attached within seconds.
3. Optionally show the Google Sheet log growing as a simple "audit trail" — this
   maps well to the Feasibility & Scalability judging criterion (real deployments
   need logs, not just pop-up alerts).

## 7. Ideas if you have extra time before the deadline

- Add a simple web dashboard (Flask/Streamlit) showing latest snapshots + recognized/unknown counts.
- Multi-camera support: pass a `camera_id` per script instance, already wired into the webhook payload.
- Swap Telegram for WhatsApp (via Twilio/WhatsApp Business node in n8n) if you want a different channel.
- Add a "cooldown per unique unknown face" instead of global cooldown, using rough face embedding clustering.

## Submission checklist (per hackathon brief)

- [ ] Functional Prototype (this repo, running end-to-end)
- [ ] Source code / GitHub repo link
- [ ] Documentation (this README + a short architecture diagram/screenshot)
- [ ] Demo video (2-3 min walkthrough as described in section 6)
