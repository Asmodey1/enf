from django import forms


class AddToCartForm(forms.Form):
    size_id = forms.IntegerField(required=False)
    quantity = forms.IntegerField(min_value=1, initial=1)



    def __init__(self, *args, product=None,**kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

        if product:
            sizes = product.product_sizes.filter(stock__gt=0)
            if sizes.exists():
                self.fields['size_id'] = forms.ChoiceField(
                    choices=[(ps.id, ps.size.name) for ps in sizes],
                              required=True,
                              initial = sizes.first().id
                )
