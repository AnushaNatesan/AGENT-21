from django.urls import path
from .views import LLM_Planner_chat,Reasoning_chat,dataset_api,Rag_chat,Reasoning_fast_chat,SQL_QUERY_GENERATOR

urlpatterns = [
    path("planner/", LLM_Planner_chat),
    path("reasoning/", Reasoning_chat),
    path("reasoning_fast/",Reasoning_fast_chat),
    path("rag/", Rag_chat),
    path("dataset/",dataset_api),
    path("sql_generator/",SQL_QUERY_GENERATOR)
]
