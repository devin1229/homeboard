# Homeboard

A Raspberry Pi powered household dashboard built with Flask.

## Features

- 🌤️ Weather
- 📅 Calendar
- ✅ Tasks
- 🛒 Shopping List
- 🌙 Ambient Mode
- 🌅 Automatic Brightness
- 🖥️ Kiosk Display

## Tech Stack

- Python
- Flask
- Gunicorn
- SQLite
- JavaScript
- HTML/CSS
- Raspberry Pi 4

## Development

Run the development server:

```bash
flask --app app run --host=0.0.0.0 --debug
```

Production:

```bash
sudo systemctl restart homeboard
```