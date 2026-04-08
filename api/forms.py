from django import forms

from api.models import PartnerCompany, Tour, TourSession


BASE_INPUT_CLASS = (
    'w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm '
    'text-slate-900 shadow-sm outline-none transition focus:border-slate-800 focus:ring-2 focus:ring-slate-200'
)
BASE_CHECKBOX_CLASS = 'h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900'


class StyledFormMixin:
    def apply_widget_classes(self):
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get('class', '')

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = f'{existing} {BASE_CHECKBOX_CLASS}'.strip()
                continue

            if isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs['class'] = f'{existing} space-y-2'.strip()
                continue

            widget.attrs['class'] = f'{existing} {BASE_INPUT_CLASS}'.strip()


class PartnerLoginForm(StyledFormMixin, forms.Form):
    username = forms.EmailField(label='Kullanici adi (email)')
    password = forms.CharField(label='Sifre', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_classes()


class PartnerCompanyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PartnerCompany
        fields = ['company_name', 'tax_number']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Sirket adi'}),
            'tax_number': forms.TextInput(attrs={'placeholder': 'Vergi numarasi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_classes()


class PartnerTourForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Tour
        fields = [
            'destination',
            'title',
            'description',
            'location_link',
            'lat',
            'lng',
            'price_adult',
            'price_child',
            'currency',
            'family_friendly',
            'includes_free_food_drinks',
            'includes_hotel_pickup_dropoff',
            'categories',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'categories': forms.CheckboxSelectMultiple(),
            'location_link': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_classes()
        self.fields['lat'].required = False
        self.fields['lng'].required = False

    def clean_lat(self):
        value = self.cleaned_data.get('lat')
        return 0 if value in (None, '') else value

    def clean_lng(self):
        value = self.cleaned_data.get('lng')
        return 0 if value in (None, '') else value


class TourSessionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TourSession
        fields = ['date', 'start_time', 'end_time', 'capacity', 'is_active']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_classes()


class RecurringTourSessionForm(StyledFormMixin, forms.Form):
    WEEKDAY_CHOICES = [
        ('0', 'Pazartesi'),
        ('1', 'Sali'),
        ('2', 'Carsamba'),
        ('3', 'Persembe'),
        ('4', 'Cuma'),
        ('5', 'Cumartesi'),
        ('6', 'Pazar'),
    ]

    start_date = forms.DateField(label='Baslangic tarihi', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='Bitis tarihi', widget=forms.DateInput(attrs={'type': 'date'}))
    weekdays = forms.MultipleChoiceField(
        label='Hangi gunlerde?',
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=['0', '1', '2', '3', '4'],
    )
    start_time = forms.TimeField(label='Baslangic saati', widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(label='Bitis saati', widget=forms.TimeInput(attrs={'type': 'time'}))
    capacity = forms.IntegerField(label='Kapasite', min_value=1, initial=20)
    is_active = forms.BooleanField(label='Aktif', required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_classes()

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Bitis tarihi, baslangic tarihinden once olamaz.')

        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', 'Bitis saati, baslangic saatinden sonra olmali.')

        return cleaned
