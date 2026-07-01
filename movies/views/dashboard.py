from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'admin/dashboard.html'
