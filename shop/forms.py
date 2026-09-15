from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Customer, Address, Review


class EmailLoginForm(forms.Form):
    email = forms.CharField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'id_email',
            'autofocus': True,
            'required': 'required'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_password',
            'required': 'required'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email_val = cleaned_data.get('email', '').strip()
        password = cleaned_data.get('password')

        if email_val and password:
            user_obj = User.objects.filter(email__iexact=email_val).first()
            if not user_obj:
                # Fallback: check username
                user_obj = User.objects.filter(username__iexact=email_val).first()

            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
            else:
                user = authenticate(username=email_val, password=password)

            if user is None:
                raise forms.ValidationError("Invalid email address or password. Please try again.")
            elif not user.is_active:
                raise forms.ValidationError("This account is inactive.")

            self.user = user

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)


class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. +880 1712-345678'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError("Please provide a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please sign in.")
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if len(phone) < 6:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+880 1712-345678'})
    )
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'profile_image']
        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if not self.initial.get('first_name'):
                self.initial['first_name'] = self.instance.first_name or (self.instance.user.first_name if self.instance.user else '')
            if not self.initial.get('last_name'):
                self.initial['last_name'] = self.instance.last_name or (self.instance.user.last_name if self.instance.user else '')
            if not self.initial.get('email'):
                if self.instance.email:
                    self.initial['email'] = self.instance.email
                elif self.instance.user:
                    self.initial['email'] = self.instance.user.email


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_line', 'city', 'country', 'postal_code', 'is_default']
        widgets = {
            'address_line': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Road, House, Area'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CheckoutForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=[
            ('cod', 'Cash on Delivery'),
            ('stripe', 'Credit/Debit Card (Stripe)')
        ],
        widget=forms.RadioSelect,
        initial='cod'
    )
    saved_address_id = forms.CharField(required=False, widget=forms.HiddenInput())
    save_to_address_book = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_save_to_address_book'})
    )

    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'required': 'required',
                'id': 'checkout-name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. +880 1712-345678',
                'required': 'required',
                'id': 'checkout-phone'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'House/Road, Area, City, Postal Code',
                'rows': 3,
                'required': 'required',
                'id': 'checkout-address'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com (optional)',
                'id': 'checkout-email'
            }),
        }
        labels = {
            'name': 'Full Name',
            'phone': 'Phone Number',
            'address': 'Delivery Address',
            'email': 'Email Address (Optional)',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if len(phone) < 6:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(5, '⭐⭐⭐⭐⭐ 5 Stars'), (4, '⭐⭐⭐⭐ 4 Stars'), (3, '⭐⭐⭐ 3 Stars'), (2, '⭐⭐ 2 Stars'), (1, '⭐ 1 Star')],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your honest review about this smartphone...'
            })
        }
