# PythonAnywhere deployment

## Before uploading

1. Create a GitHub repository and push this project from `Final_Project`.
2. Rotate the Django, Gmail and Stripe keys that were previously present in local settings/docs. They must be treated as exposed.
3. Keep the real values only in PythonAnywhere environment variables or a server-only `.env` file.

## PythonAnywhere Bash console

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY/mysite
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Create `mysite/.env` from `.env.example` and fill in real values. Set the same values in the Web app's environment configuration if that feature is enabled.

## Web app settings

- Working directory: `/home/YOUR_USERNAME/YOUR_REPOSITORY/mysite`
- Virtualenv: `/home/YOUR_USERNAME/YOUR_REPOSITORY/mysite/venv`
- WSGI file: `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`
- WSGI application: `mysite.wsgi.application`
- Static URL: `/static/`, directory: `/home/YOUR_USERNAME/YOUR_REPOSITORY/mysite/static`
- Media URL: `/media/`, directory: `/home/YOUR_USERNAME/YOUR_REPOSITORY/mysite/media`

In the WSGI file, add the project directory to `sys.path` and set `DJANGO_SETTINGS_MODULE` to `mysite.settings` before importing the application. Reload the web app after every code or environment change.