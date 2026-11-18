from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from .models import SupportOrganization, ChatBotResponse, AnonymousStats

@admin.register(SupportOrganization)
class SupportOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'state', 'phone_number', 'is_verified', 'created_at')
    list_filter = ('category', 'state', 'is_verified')
    search_fields = ('name', 'phone_number', 'email', 'description', 'address')
    list_editable = ('is_verified',)
    date_hierarchy = 'created_at'


@admin.register(ChatBotResponse)
class ChatBotResponseAdmin(admin.ModelAdmin):
    list_display = ('intent', 'title', 'suggested_action', 'updated_at')
    search_fields = ('intent', 'title', 'keywords', 'response_text')
    list_filter = ('suggested_action',)


@admin.register(AnonymousStats)
class AnonymousStatsAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'detected_intent', 'state_filter_used', 'category_filter_used', 'action_taken')
    list_filter = ('detected_intent', 'state_filter_used', 'action_taken')
    date_hierarchy = 'timestamp'
    
    def changelist_view(self, request, extra_context=None):
        """
        Customizes the default changelist view to inject aggregated usage analytics.
        Calculates frequencies of intents, regions searched, and safety actions taken.
        """
        extra_context = extra_context or {}
        
        # 1. Total stats count
        total_interactions = AnonymousStats.objects.count()
        
        # 2. Most common detected intents (top 5)
        top_intents = (
            AnonymousStats.objects.filter(detected_intent__isnull=False)
            .exclude(detected_intent='')
            .values('detected_intent')
            .annotate(count=Count('detected_intent'))
            .order_by('-count')[:5]
        )
        
        # 3. Top states searched in directory (top 5)
        top_states = (
            AnonymousStats.objects.filter(state_filter_used__isnull=False)
            .exclude(state_filter_used='')
            .values('state_filter_used')
            .annotate(count=Count('state_filter_used'))
            .order_by('-count')[:5]
        )
        
        # 4. Action breakdown (Quick Exit vs Safety Plan Downloads)
        actions = (
            AnonymousStats.objects.filter(action_taken__isnull=False)
            .exclude(action_taken='')
            .values('action_taken')
            .annotate(count=Count('action_taken'))
            .order_by('-count')
        )
        actions_dict = {item['action_taken']: item['count'] for item in actions}
        
        # Inject stats into the template rendering context
        extra_context.update({
            'analytics': {
                'total_interactions': total_interactions,
                'top_intents': top_intents,
                'top_states': top_states,
                'actions': actions,
                'quick_exit_count': actions_dict.get('quick_exit', 0),
                'download_count': actions_dict.get('downloaded_safety_plan', 0)
            },
            'title': 'Anonymous Usage Analytics & Stats'
        })
        
        return super().changelist_view(request, extra_context=extra_context)
