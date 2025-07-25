# inventory/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Brand(models.Model):
    """
    Represents a phone brand.
    """
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)

    def __str__(self):
        return self.name

class Phone(models.Model):
    """
    Represents a refurbished phone in the inventory.
    """
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Good', 'Good'),
        ('Usable', 'Usable'),
        ('Scrap', 'Scrap'),
    ]

    name = models.CharField(max_length=100, help_text="Name of the phone model (e.g., 12, Galaxy S21)")
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Base cost of the phone before any platform fees."
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        help_text="Overall condition of the phone."
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity of this phone."
    )
    memory = models.IntegerField(
        default=128,
        help_text="Memory of the phone in GB."
    )
    camera_quality = models.CharField(max_length=50, blank=True, help_text="Camera quality (e.g., 12MP, 48MP)")
    color = models.CharField(max_length=50, blank=True, help_text="Color of the phone")
    image = models.ImageField(
        upload_to='phone_images/',
        blank=True,
        null=True,
        help_text="Image of the phone."
    )

    def __str__(self):
        return f"{self.name} ({self.condition})"

class Platform(models.Model):
    """
    Represents an e-commerce platform where phones can be sold.
    """
    name = models.CharField(max_length=50, unique=True, help_text="Name of the e-commerce platform (e.g., X, Y, Z)")
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage fee charged by the platform (e.g., 10.00 for 10%)"
    )
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Fixed fee charged by the platform (e.g., 2.00 for $2)"
    )

    def __str__(self):
        return self.name

class Listing(models.Model):
    """
    Represents a phone listed on a specific platform.
    """
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='listings')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='listings')
    platform_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Calculated selling price on this specific platform."
    )
    platform_condition_category = models.CharField(
        max_length=50,
        help_text="Platform-specific condition category for the phone."
    )
    is_listed = models.BooleanField(
        default=False,
        help_text="Indicates if the phone is currently listed on this platform."
    )

    class Meta:
        unique_together = ('phone', 'platform') # A phone can only be listed once per platform

    def __str__(self):
        return f"{self.phone.name} on {self.platform.name}"

    def calculate_platform_price(self):
        """
        Calculates the selling price on the specific platform based on fees.
        This is a simplified calculation for demonstration.
        """
        # Ensure base_price is not zero to avoid division by zero or nonsensical calculations
        if self.phone.base_price <= 0:
            return 0.00 # Or raise an error, depending on desired behavior

        # Calculate price considering percentage and fixed fees
        # We assume the base_price is the cost, and we want to set a selling price
        # that covers the cost + fees.
        # Let S = selling_price
        # S - (S * fee_percentage / 100) - fixed_fee = base_price (assuming we want to break even at base_price)
        # S * (1 - fee_percentage / 100) = base_price + fixed_fee
        # S = (base_price + fixed_fee) / (1 - fee_percentage / 100)

        fee_percentage_decimal = self.platform.fee_percentage / 100
        if fee_percentage_decimal >= 1: # Prevent division by zero or negative margin
            return self.phone.base_price # Cannot make profit, just return base price or mark as unprofitable

        selling_price = (self.phone.base_price + self.platform.fixed_fee) / (1 - fee_percentage_decimal)
        return round(selling_price, 2)

    def map_condition_to_platform(self):
        """
        Maps the general phone condition to a platform-specific category.
        """
        general_condition = self.phone.condition
        platform_name = self.platform.name

        mapping = {
            'X': {
                'New': 'New',
                'Good': 'Good',
                'Usable': 'Scrap', # Assuming Usable maps to Scrap on X
                'Scrap': 'Scrap',
            },
            'Y': {
                'New': '3 stars (Excellent)',
                'Good': '2 stars (Good)',
                'Usable': '1 star (Usable)',
                'Scrap': '1 star (Usable)', # Assuming Scrap maps to Usable on Y
            },
            'Z': {
                'New': 'New',
                'Good': 'As New', # Assuming Good maps to As New on Z
                'Usable': 'Good', # Assuming Usable maps to Good on Z
                'Scrap': 'Good', # Assuming Scrap maps to Good on Z
            }
        }
        return mapping.get(platform_name, {}).get(general_condition, 'Unknown') # Default to Unknown if not found

    def check_profitability(self):
        """
        Checks if listing the phone on this platform is profitable.
        A simple definition of profitable: selling price covers base price and fees.
        """
        calculated_selling_price = self.calculate_platform_price()
        # If the calculated selling price is less than or equal to the base price, it's not profitable
        # after accounting for fees.
        # A more robust check would involve a desired profit margin.
        return calculated_selling_price > self.phone.base_price

class Order(models.Model):
    """
    Represents a buy or sell order for a phone.
    """
    ORDER_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type} order for {self.quantity} x {self.phone.name} at {self.total_price}"

class Query(models.Model):
    """
    Represents a user query or complaint.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query from {self.name} at {self.created_at}"

class Review(models.Model):
    """
    Represents a customer review for a phone.
    """
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.phone.name}"

class Cart(models.Model):
    """
    Represents a shopping cart.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_price(self):
        return sum(item.phone.base_price * item.quantity for item in self.items.all())

class CartItem(models.Model):
    """
    Represents an item in a shopping cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.phone.name} in cart for {self.cart.user.username}"

class HomePageImage(models.Model):
    """
    Represents an image on the home page.
    """
    image = models.ImageField(upload_to='home_page_images/')
    title = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
