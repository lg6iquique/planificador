from django.core.management.base import BaseCommand
from planning.db_init import seed_poc_data

class Command(BaseCommand):
    help = 'Inicializa las tablas mct_* en SQLite y puebla los datos industriales de prueba'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Inicializando tablas mct_* y datos de prueba...'))
        seed_poc_data()
        self.stdout.write(self.style.SUCCESS('¡Base de datos POC inicializada y poblada exitosamente!'))
