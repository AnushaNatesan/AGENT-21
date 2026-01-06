from django.contrib import admin
from django.urls import path
from . import query_executer
from App import views as app_views
from App.views_scenario import scenario_simulator
from App import views

urlpatterns = [
    path('market/survey/', app_views.market_survey, name='market_survey'),
    path('', app_views.dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('execute-sql/', query_executer.agent_intelligence_view, name='execute_sql'),
    # UI PAGE
    path(
        "business/insights/scenario/",
        views.boardroom_ui,
        name="boardroom_ui"
    ),

    # DRF API
    path(
        "api/boardroom/simulate/",
        scenario_simulator,
        name="scenario_simulator"
    ),
    # Customer Portal
    path('customer/login/', app_views.customer_login, name='customer_login'),
    path('customer/signup/', app_views.customer_signup, name='customer_signup'),
    path('customer/dashboard/', app_views.customer_dashboard, name='customer_dashboard'),
    
    # API Endpoints
    path('api/products/', app_views.get_customer_products, name='api_products'),
    path('api/products/<int:product_id>/similar/', app_views.get_similar_products, name='api_similar_products'),
    path('api/cart/add/', app_views.add_to_cart, name='api_cart_add'),
    path('api/cart/details/', app_views.get_cart_details, name='api_cart_details'),
    path('api/cart/remove/', app_views.remove_from_cart, name='api_cart_remove'),
    path('api/order/confirm/', app_views.confirm_order, name='api_order_confirm'),
    path('api/orders/history/', app_views.get_order_history, name='api_order_history'),
    path('api/orders/<int:order_id>/tracking/', app_views.get_order_tracking, name='api_order_tracking'),
    path('api/business/data/', app_views.get_business_data, name='api_business_data'),
    path('business/insights/', app_views.business_insights, name='business_insights'),

    # Wishlist & Settings APIs
    path('api/wishlist/', app_views.manage_wishlist, name='api_wishlist'),
    path('api/wishlist/details/', app_views.get_wishlist_details, name='api_wishlist_details'),
    path('api/settings/', app_views.manage_settings, name='api_settings'),
    
    # ========================================
    # ADVANCED FEATURES API ENDPOINTS
    # ========================================
    
    # Self-Healing SQL Re-Sensing
    path('api/advanced/sql/healing/', app_views.api_self_healing_sql, name='api_self_healing_sql'),
    
    # Agentic Boardroom (Multi-Agent Negotiation)
    path('api/advanced/boardroom/convene/', app_views.api_convene_boardroom, name='api_convene_boardroom'),
    path('api/advanced/boardroom/history/', app_views.api_boardroom_history, name='api_boardroom_history'),
    
    # Digital Twin (What-If Simulator)
    path('api/advanced/simulation/run/', app_views.api_run_simulation, name='api_run_simulation'),
    path('api/advanced/simulation/history/', app_views.api_simulation_history, name='api_simulation_history'),
    path('api/advanced/simulation/compare/', app_views.api_compare_scenarios, name='api_compare_scenarios'),
    
    # Immutable Audit Trail
    path('api/advanced/audit/verify/', app_views.api_verify_audit_integrity, name='api_verify_audit'),
    path('api/advanced/audit/cycles/', app_views.api_get_audit_cycles, name='api_get_audit_cycles'),
    path('api/advanced/audit/search/', app_views.api_search_audit_trail, name='api_search_audit'),
    path('api/advanced/audit/report/', app_views.api_generate_audit_report, name='api_audit_report'),
    path('api/advanced/audit/cycle/<str:cycle_id>/', app_views.api_get_cycle_details, name='api_cycle_details'),
]