from django.contrib import admin
from django.urls import path
from . import query_executor
from . import supabase_redis_api 
from .security.intent_api import classify_intent
from .apis.insert_agent_log import insert_agent_log
from .apis.market_survey import market_survey
from .apis.insert_suggestions import insert_suggestion
from .apis.reasoning_gate import reasoning_gate_api
from .apis.insert_products import insert_products
from .apis.translate_request import translate_to_english
from .apis.translate_response import translate_response
from .voice.voice import voice_webhook
from .voice.voice import agent_response
urlpatterns = [
    path('admin/', admin.site.urls),
    path('execute-sql/', query_executor.execute_sql_query, name='execute_sql'),
    path('api/query/', supabase_redis_api.execute_sql_query, name='sql_query'),
    path('api/cache/stats/', supabase_redis_api.cache_stats, name='cache_stats'),
    path('api/cache/clear/', supabase_redis_api.clear_cache, name='clear_cache'),
    path('api/cache/test/', supabase_redis_api.test_redis, name='test_redis'),

    path('api/intent/classify/', classify_intent, name='classify_intent'),

    path('api/agent/log/', insert_agent_log, name='insert_agent_log'),
    path('api/market/survey/', market_survey, name='market_survey_api'),

    path('api/suggestions/insert/', insert_suggestion, name='insert_suggestion'),
    path('api/reasoning_gate/', reasoning_gate_api, name='reasoning_gate_api'),
    path('api/products/insert/', insert_products, name='insert_products'),
    path('api/translate/request/', translate_to_english, name='translate_to_english'),
    path('api/translate/response/', translate_response, name='translate_response'),
    # path('twilio/voice/', voice_webhook, name='voice_webhook'),
    # path('twilio/agent-response/', agent_response, name='agent_response'),
]
