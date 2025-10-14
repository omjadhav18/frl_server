from django.contrib import admin
from .models import *

admin.site.register(QTable)
admin.site.register(GlobalQTable)
admin.site.register(ClientEventLog)
admin.site.register(TestResult)
admin.site.register(FederatedRun)
admin.site.register(ClientQTable)