# Campus Event & Find Hub

A Flask-based web application for managing campus lost & found items and events.

## Features

- **Lost & Found System**: Post and search for lost/found items
- **Event Management**: Create and view campus events
- **User Authentication**: Register, login, and manage your posts
- **Image Upload**: Upload photos of lost/found items
- **Search Functionality**: Search items by title, location, or category
- **Event News Ticker**: Scrolling ticker showing upcoming events

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Project Structure

```
anshi project/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── events.html
│   ├── add_event.html
│   ├── login.html
│   ├── register.html
│   ├── add_item.html
│   └── item_detail.html
├── static/
│   ├── css/
│   │   └── style.css   # Styles
│   └── js/
│       └── main.js     # JavaScript
└── uploads/            # Uploaded images (created automatically)
```

## Usage

1. **Register**: Create a new account
2. **Login**: Sign in with your credentials
3. **Add Events**: Post campus events with date, venue, and description
4. **Post Items**: Add lost or found items with photos and details
5. **Search**: Find items by keywords, location, or category
6. **Contact**: Reach out to item owners through the contact feature

## Database

The application uses SQLite (`campus_hub.db`) with three main tables:
- `students`: User accounts
- `items`: Lost and found items
- `events`: Campus events

## Security Note

Remember to change the `app.secret_key` in `app.py` before deploying to production.

---

## Streamlit Quick Deploy (Recommended for a free demo)

You can run this project as a Streamlit app and deploy it on Streamlit Community Cloud for a quick public URL.

### Run locally (Streamlit)

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Deploy to Streamlit Community Cloud

1. Push this repository to GitHub (public repo recommended).
2. Go to https://streamlit.io/cloud and click "New app".
3. Select your repo/branch and set Main file to `streamlit_app.py`.
4. Deploy – you’ll get a public URL.

Notes:
- SQLite DB (`campus_hub.db`) and `uploads/` live on the app filesystem. On Streamlit Cloud this storage is ephemeral and may reset on restarts/redeploys. Use a managed DB and object storage for durability if needed.

## Azure App Service (Flask)

If you prefer deploying the original Flask app to Azure App Service, a GitHub Actions workflow is provided at `.github/workflows/azure-webapp.yml`.

High level steps:
- Create an App Service (Linux, Python 3.11) and obtain the Publish Profile XML.
- In your GitHub repo settings:
	- Secrets: add `AZURE_WEBAPP_PUBLISH_PROFILE` with the XML content.
	- Variables: add `AZURE_WEBAPP_NAME` with your Web App name.
- Push to `main` to trigger deployment.

Environment settings to consider:
- `SECRET_KEY` – set to a strong random string.
- `UPLOAD_FOLDER` – e.g. `/home/uploads` on Azure.
- `DATABASE_PATH` – e.g. `/home/data/campus_hub.db` for persistence.
