from django.core.management.base import BaseCommand
from inventory.models import Brand, Phone
import random

class Command(BaseCommand):
    help = 'Adds dummy brands and phone models'

    def handle(self, *args, **kwargs):
        # Clear existing brands to ensure a fresh start
        Brand.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all existing brands.'))

        brand_names = ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Huawei", "Sony", "LG", "Motorola", "Nokia", "Realme", "Oppo"]
        for name in brand_names:
            Brand.objects.get_or_create(name=name.title())
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated brands.'))

        brands = Brand.objects.all()
        for brand in brands:
            # Clear existing phones for the brand
            Phone.objects.filter(brand=brand).delete()
            for i in range(1, 21):
                phone_name = f'{brand.name} Model {i}'
                base_price = round(random.uniform(100, 1000), 2)
                condition = random.choice(['New', 'Good', 'Usable', 'Scrap'])
                stock = random.randint(0, 100)
                memory = random.choice([64, 128, 256, 512])
                camera_quality = random.choice(['12MP', '24MP', '48MP', '108MP'])
                color = random.choice(['Black', 'White', 'Silver', 'Gold', 'Blue', 'Red'])

                Phone.objects.create(
                    brand=brand,
                    name=phone_name,
                    base_price=base_price,
                    condition=condition,
                    stock=stock,
                    memory=memory,
                    camera_quality=camera_quality,
                    color=color
                )
            self.stdout.write(self.style.SUCCESS(f'Successfully added 20 dummy models for {brand.name}'))
