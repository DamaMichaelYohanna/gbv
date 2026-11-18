import json
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from .models import SupportOrganization, ChatBotResponse, AnonymousStats
from .nlp_engine import match_intent

@ensure_csrf_cookie
def home(request):
    """
    Renders the institutional Landing Page inspired by Nasarawa State University, Keffi (NSUK).
    Includes university branding, zero-tolerance policy, types of GBV, campus support helplines,
    and clear entry points to the separate Chat Interface and Safety Planner.
    """
    states = SupportOrganization.NIGERIAN_STATES
    categories = SupportOrganization.CATEGORY_CHOICES
    nasarawa_orgs = SupportOrganization.objects.filter(state='Nasarawa', is_verified=True)
    orgs_preview = SupportOrganization.objects.filter(is_verified=True)[:8]
    
    context = {
        'states': states,
        'categories': categories,
        'nasarawa_orgs': nasarawa_orgs,
        'orgs_preview': orgs_preview,
        'total_orgs_count': SupportOrganization.objects.filter(is_verified=True).count(),
    }
    return render(request, 'advisor/landing.html', context)


@ensure_csrf_cookie
def chat_page(request):
    """
    Renders the dedicated, standalone Chat Interface page.
    A secure, confidential space with Endy the Advisory Bot, side resource tools,
    campus directory, and interactive safety planner.
    """
    states = SupportOrganization.NIGERIAN_STATES
    categories = SupportOrganization.CATEGORY_CHOICES
    
    context = {
        'states': states,
        'categories': categories,
    }
    return render(request, 'advisor/chat_page.html', context)


@staff_member_required(login_url='/admin/login/')
def dashboard(request):
    """Render the lightweight staff dashboard separately from Django admin."""
    action_counts = {
        item['action_taken']: item['count']
        for item in AnonymousStats.objects.filter(
            action_taken__isnull=False
        ).exclude(action_taken='').values('action_taken').annotate(
            count=Count('action_taken')
        )
    }
    top_intents = (
        AnonymousStats.objects.filter(detected_intent__isnull=False)
        .exclude(detected_intent='')
        .values('detected_intent')
        .annotate(count=Count('detected_intent'))
        .order_by('-count')[:5]
    )

    context = {
        'organization_count': SupportOrganization.objects.count(),
        'verified_organization_count': SupportOrganization.objects.filter(
            is_verified=True
        ).count(),
        'knowledge_count': ChatBotResponse.objects.count(),
        'interaction_count': AnonymousStats.objects.count(),
        'quick_exit_count': action_counts.get('quick_exit', 0),
        'safety_plan_count': action_counts.get('downloaded_safety_plan', 0),
        'top_intents': top_intents,
        'recent_organizations': SupportOrganization.objects.order_by(
            '-created_at'
        )[:5],
        'recent_knowledge': ChatBotResponse.objects.order_by('-updated_at')[:5],
    }
    return render(request, 'advisor/dashboard.html', context)


# Alias for backward compatibility
chat_home = home


@require_http_methods(["POST"])
def chat_api(request):
    """
    AJAX endpoint for chatbot interaction. Receives user message, runs the NLP engine,
    saves an anonymous usage stat (intent detected), and returns the chatbot's response.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Match using NLP Engine
        matched_response, score = match_intent(user_message)
        
        # Log this event anonymously (only save the detected intent)
        try:
            AnonymousStats.objects.create(
                detected_intent=matched_response.intent
            )
        except Exception:
            pass
        
        return JsonResponse({
            'response': matched_response.response_text,
            'intent': matched_response.intent,
            'suggested_action': matched_response.suggested_action,
            'title': matched_response.title
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def directory_api(request):
    """
    AJAX endpoint for searching support organizations and referrals.
    Filters by optional state, category, and keyword search (q).
    If no filters are provided, returns all verified referral organizations.
    Logs anonymous search stats.
    """
    state = request.GET.get('state', '').strip()
    category = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()
    
    # Query database for verified organizations
    orgs = SupportOrganization.objects.filter(is_verified=True)
    
    if state:
        orgs = orgs.filter(state__iexact=state)
    if category:
        orgs = orgs.filter(category__iexact=category)
    if query:
        orgs = orgs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    # Log the search event anonymously
    try:
        AnonymousStats.objects.create(
            state_filter_used=state or None,
            category_filter_used=category or None,
            action_taken='directory_search'
        )
    except Exception:
        pass
    
    # Serialize results
    results = []
    for org in orgs:
        results.append({
            'name': org.name,
            'category': org.get_category_display(),
            'category_code': org.category,
            'state': org.state,
            'phone_number': org.phone_number,
            'alt_phone_number': org.alt_phone_number or '',
            'email': org.email or '',
            'address': org.address,
            'website': org.website or '',
            'description': org.description,
        })
        
    return JsonResponse({'results': results, 'count': len(results)})


@require_http_methods(["GET"])
def knowledge_base_api(request):
    """
    Knowledge Base Module API endpoint.
    Retrieves stored knowledge on types of GBV, legal guidance, and advisories.
    Supports filtering by ?intent= or ?type= (e.g. types_of_gbv).
    """
    intent = request.GET.get('intent') or request.GET.get('type')
    
    responses = ChatBotResponse.objects.all()
    if intent:
        responses = responses.filter(intent=intent)
        
    results = [
        {
            'id': item.id,
            'intent': item.intent,
            'title': item.title,
            'keywords': item.keywords,
            'response_text': item.response_text,
            'suggested_action': item.suggested_action,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in responses
    ]
    return JsonResponse({'knowledge_base': results, 'count': len(results)})


@require_http_methods(["POST", "PUT"])
def admin_update_knowledge_api(request):
    """
    Administrative Module API endpoint for updating knowledge-base information.
    Requires an authorized administrator (authenticated staff or superuser).
    Rejects unauthorized access with HTTP 403 Forbidden.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse(
            {'error': 'Unauthorized: Administrator privileges required to update knowledge-base information'}, 
            status=403
        )
    
    try:
        data = json.loads(request.body)
        intent = data.get('intent', '').strip()
        response_text = data.get('response_text', '').strip()
        title = data.get('title', '').strip()
        keywords = data.get('keywords', '').strip()
        suggested_action = data.get('suggested_action')
        
        if not intent:
            return JsonResponse({'error': 'Intent is required'}, status=400)
            
        record, created = ChatBotResponse.objects.get_or_create(intent=intent)
        if response_text:
            record.response_text = response_text
        if title:
            record.title = title
        if keywords:
            record.keywords = keywords
        if suggested_action:
            record.suggested_action = suggested_action
            
        record.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Knowledge-base record updated successfully',
            'created': created,
            'data': {
                'id': record.id,
                'intent': record.intent,
                'title': record.title,
                'keywords': record.keywords,
                'response_text': record.response_text,
                'suggested_action': record.suggested_action,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def log_stat_api(request):
    """
    AJAX endpoint to log anonymous actions, e.g., downloading a safety plan,
    visiting resources, or executing a quick exit.
    """
    try:
        data = json.loads(request.body)
        action = data.get('action', '')
        
        if action:
            try:
                AnonymousStats.objects.create(
                    action_taken=action
                )
            except Exception:
                pass
            return JsonResponse({'status': 'logged'})
        return JsonResponse({'error': 'Action missing'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
