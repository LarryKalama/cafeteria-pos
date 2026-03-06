from django.contrib.auth.decorators import user_passes_test


def is_superadmin(user):
    return user.is_authenticated and user.role == 'SUPERADMIN'


def is_staff(user):
    """Waiter or Cashier or Superadmin"""
    return user.is_authenticated and user.role in ('SUPERADMIN', 'WAITER', 'CASHIER')


def can_manage_menu(user):
    """Only superadmin"""
    return is_superadmin(user)


def can_adjust_inventory(user):
    """Superadmin + Cashier + Waiter"""
    return is_staff(user)


def can_record_expenses(user):
    """Superadmin + Cashier + Waiter"""
    return is_staff(user)


def can_view_reports(user):
    """Superadmin + Cashier + Waiter"""
    return is_staff(user)


def can_view_inventory(user):
    """Superadmin + Cashier + Waiter"""
    return is_staff(user)


def can_manage_stock(user):
    """Superadmin + Cashier + Waiter — full stock CRUD"""
    return user.is_authenticated and user.role in ('SUPERADMIN', 'CASHIER', 'WAITER')

def can_view_stock(user):
    """Same as above — for read-only views if you ever need them separately"""
    return can_manage_stock(user)
def can_manage_expenses(user):
    """Superadmin + Cashier + Waiter"""
    return user.is_authenticated and user.role in ('SUPERADMIN', 'CASHIER', 'WAITER')