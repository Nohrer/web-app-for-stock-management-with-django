# How To Run

## 1. Install Python
Use Python 3.11 or 3.12 if possible. Check your version with:

```bash
python3 --version
```

## 2. Create a virtual environment
From the project root:

```bash
python3 -m venv .venv
```

## 3. Activate the virtual environment
On Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies
With the virtual environment active:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Prepare the database
Run migrations:

```bash
python manage.py migrate
```

Populate demo data:

```bash
python manage.py seed_demo_data
```

## 6. Run the app
Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## 7. Optional Tailwind rebuild
If you need to rebuild the frontend CSS:

```bash
cd theme/static_src
npm install
npm run dev
```

## Demo accounts
The seed command creates sample users for the app flow:

* `admin_demo`
* `directeur_demo`
* `magasinier_demo`
* `employee_demo`

Password for each demo account: `Demo12345!`