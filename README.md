# Commands

1. Run Server CMD
```bash
python manage.py runserver
```

2. Create a superuser account
```bash
python manage.py createsuperuser
```

3. Migrate
```bash
python manage.py makemigrations
python manage.py migrate
```

## Git Commands

1. Pull changes
```bash
git pull
```

2. Push changes
```bash
git push
```

# Test User Creds
To truncate a table row with EmpID as a key :
> Use python manage.py shell
```bash
from django.contrib.auth import get_user_model
User = get_user_model()
deleted_count, _ = User.objects.filter(username="1040663").delete()
print(f"Successfully deleted {deleted_count} user row(s).")
```
### Quick Links
<a href="http://127.0.0.1:8080/">Employee Login</a>

<a href="http://127.0.0.1:8080/admin/portal/login/">Admin Login</a>
> `admin` is the super user. Access admin page at : 127.0.0.1:8000/admin/portal/login

| Emp ID / Username | Email | Password |
| :--- | :--- | :--- |
| admin | admin@infinite.com  | Admin@123  |
| 1040666  | chaitanyakumars@infinite.com  | chaitu123 |
| 1040669 | charithasree@infinite.com | charitha123 |
|1040585 | poojithap@infinite.com | poojitha123 |
