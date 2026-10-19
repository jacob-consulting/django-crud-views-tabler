from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class NewUserForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "is_staff")
        labels = {"is_staff": "Staff (can open the admin site)"}
