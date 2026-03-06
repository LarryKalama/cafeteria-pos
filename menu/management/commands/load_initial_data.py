from django.core.management.base import BaseCommand
from django.db import transaction
from menu.models import Category, MenuItem
from inventory.models import Stock
from accounts.models import User

class Command(BaseCommand):
    help = 'Loads initial CAFETERIA POS menu data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading CAFETERIA  POS initial data...')
        
        with transaction.atomic():
            # Create Categories
            self.stdout.write('Creating categories...')
            hot_drinks = Category.objects.create(
                name='Hot Drinks',
                description='Hot beverages',
                order=1
            )
            cold_drinks = Category.objects.create(
                name='Cold Drinks',
                description='Cold beverages',
                order=2
            )
            snacks = Category.objects.create(
                name='Snacks',
                description='Light snacks and appetizers',
                order=3
            )
            main_dishes = Category.objects.create(
                name='Main Dishes',
                description='Main course dishes',
                order=4
            )
            
            # HOT DRINKS
            self.stdout.write('Loading hot drinks...')
            hot_items = [
                ('Mixed Tea', 50, True),
                ('Masala Tea', 50, True),
                ('Black Tea', 50, True),
                ('Coffee', 50, True),
            ]
            
            for name, price, track_inv in hot_items:
                item = MenuItem.objects.create(
                    category=hot_drinks,
                    name=name,
                    price=price,
                    track_inventory=track_inv,
                    is_available=True,
                    is_active=True
                )
                if track_inv:
                    Stock.objects.create(menu_item=item, quantity=100, unit='cups')
            
            # COLD DRINKS
            self.stdout.write('Loading cold drinks...')
            cold_items = [
                ('Fresh Juice', 100, True),
                ('Smoothie', 100, True),
                ('Milkshake', 100, True),
                ('Fresh Milk', 100, True),
                ('Mala', 100, True),
                ('Dawa', 100, True),
                ('Water', 50, True),
                ('Minute Maid', 50, True),
                ('Soda 300ml', 100, True),
                ('Soda 500ml', 150, True),
            ]
            
            for name, price, track_inv in cold_items:
                item = MenuItem.objects.create(
                    category=cold_drinks,
                    name=name,
                    price=price,
                    track_inventory=track_inv,
                    is_available=True,
                    is_active=True
                )
                if track_inv:
                    if 'Soda' in name:
                        Stock.objects.create(menu_item=item, quantity=24, unit='bottles')
                    else:
                        Stock.objects.create(menu_item=item, quantity=50, unit='servings')
            
            # SNACKS
            self.stdout.write('Loading snacks...')
            snack_items = [
                ('Beef Samosas', 50, True),
                ('Sausages', 100, True),
                ('Kebab', 150, True),
                ('Smokie', 100, True),
                ('Chapati', 40, True),
                ('Fried Eggs', 150, True),
                ('Spanish Omelette', 200, True),
            ]
            
            for name, price, track_inv in snack_items:
                item = MenuItem.objects.create(
                    category=snacks,
                    name=name,
                    price=price,
                    track_inventory=track_inv,
                    is_available=True,
                    is_active=True
                )
                if track_inv:
                    Stock.objects.create(menu_item=item, quantity=50, unit='pieces')
            
            # MAIN DISHES
            self.stdout.write('Loading main dishes...')
            main_items = [
                ('Ugali Fish', 450, True),
                ('Ugali Plain', 50, True),
                ('Ugali Managu', 150, True),
                ('Managu Plain', 100, True),
                ('Ugali Mboga', 150, True),
                ('Ugali Mboga Mix', 200, True),
                ('Kuku Full', 2000, True),
                ('Stew Plain', 300, True),
                ('Chips', 200, True),
                ('Liver Plain', 300, True),
                ('Liver 1kg', 1300, True),
                ('Matumbo 1kg', 1000, True),
                ('Matumbo 1/2 kg', 500, True),
                ('Tumbukiza', 1000, True),
                ('Mbuzi Choma 1/2 kg', 650, True),
                ('Mbuzi Choma 3/4 kg', 850, True),
                ('Mbuzi Choma 1 kg', 1300, True),
            ]
            
            for name, price, track_inv in main_items:
                item = MenuItem.objects.create(
                    category=main_dishes,
                    name=name,
                    price=price,
                    track_inventory=track_inv,
                    is_available=True,
                    is_active=True
                )
                if track_inv:
                    if '1kg' in name or 'Full' in name:
                        Stock.objects.create(menu_item=item, quantity=5, unit='servings', reorder_level=2)
                    else:
                        Stock.objects.create(menu_item=item, quantity=20, unit='servings')
            
            # Create default superadmin
            self.stdout.write('Creating default superadmin...')
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    password='admin123',
                    first_name='CAFETERIA',
                    last_name='POS',
                    email='larrykalama8@gmail.com',
                    role='SUPERADMIN'
                )
                self.stdout.write(self.style.SUCCESS('Created admin user (username: admin, password: admin123)'))
            
            # Create sample waiter
            self.stdout.write('Creating sample waiter...')
            if not User.objects.filter(username='waiter1').exists():
                User.objects.create_user(
                    username='waiter1',
                    password='waiter123',
                    first_name='Joy',
                    last_name='Waiter',
                    role='WAITER'
                )
                self.stdout.write(self.style.SUCCESS('Created waiter user (username: waiter1, password: waiter123)'))
        
        self.stdout.write(self.style.SUCCESS('✅ Initial data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS('📊 Summary:'))
        self.stdout.write(f'   - Categories: {Category.objects.count()}')
        self.stdout.write(f'   - Menu Items: {MenuItem.objects.count()}')
        self.stdout.write(f'   - Stock Items: {Stock.objects.count()}')
        self.stdout.write(f'   - Users: {User.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🔐 Login Credentials:'))
        self.stdout.write('   Superadmin: username=admin, password=admin123')
        self.stdout.write('   Waiter: username=waiter1, password=waiter123')