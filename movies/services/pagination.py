from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class PaginationService:
    @staticmethod
    def get_paginated_page(queryset, request, per_page=12):
        paginator = Paginator(queryset, per_page)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
            
        return page_obj
