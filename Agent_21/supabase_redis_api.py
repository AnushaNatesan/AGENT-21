"""
supabase_redis_api.py
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import time
import hashlib
import redis
from supabase import create_client

SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TIMEOUT = 300  # 5 minutes (300 seconds)

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    redis_client.ping()
    REDIS_ENABLED = True
    print("✅ Redis cache ENABLED")
except Exception as e:
    REDIS_ENABLED = False
    print(f"⚠️  Redis cache DISABLED: {str(e)}")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_cache_key(sql_query):
    """Generate unique cache key from SQL query"""
    query_hash = hashlib.md5(sql_query.encode('utf-8')).hexdigest()
    return f"sql_cache:{query_hash}"

def get_cached_result(cache_key):
    """Get result from Redis cache if available"""
    if not REDIS_ENABLED:
        return None
    
    try:
        start_time = time.time()
        cached_data = redis_client.get(cache_key)
        retrieval_time = round((time.time() - start_time) * 1000, 2)
        
        if cached_data:
            result = json.loads(cached_data.decode('utf-8'))
            result['cache_info']['hit'] = True
            result['cache_info']['source'] = 'redis_cache'
            result['cache_info']['retrieval_time_ms'] = retrieval_time
            print(f"Cache retrieval time: {retrieval_time}ms")
            return result
            
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None

def set_cached_result(cache_key, data, timeout=CACHE_TIMEOUT):
    """Store result in Redis cache"""
    if not REDIS_ENABLED:
        return
    
    try:
        # Prepare cache info
        cache_info = {
            'hit': False,
            'source': 'supabase_fresh',
            'cached_at': time.time(),
            'timeout': timeout
        }
        data['cache_info'] = cache_info
        serialized = json.dumps(data)
        redis_client.setex(cache_key, timeout, serialized)
        
        print(f"Cached for {timeout} seconds")
        
    except Exception as e:
        print(f"Cache write error: {e}")


PII_KEYS = {"name", "email", "username", "password"}

def redact_pii(data):
    # Case 1: list of rows
    if isinstance(data, list):
        return [
            {
                k: ("REDACTED" if k.lower() in PII_KEYS else v)
                for k, v in row.items()
            }
            for row in data
        ]

    # Case 2: single row
    if isinstance(data, dict):
        return {
            k: ("REDACTED" if k.lower() in PII_KEYS else v)
            for k, v in data.items()
        }

    return data

def execute_supabase_query(sql_query):
    """Execute query directly on Supabase"""
    print("Querying Supabase...")
    start_time = time.time()
    
    try:
        response = supabase.rpc('execute_any_query', {'sql_text': sql_query}).execute()
        execution_time = round((time.time() - start_time) * 1000, 2)
        
        data = response.data
        safe_data = redact_pii(data)
        row_count = len(data) if isinstance(data, list) else 1
        
        print(f"  ✅ Supabase query successful")
        print(f"  ⏱️  Query time: {execution_time}ms")
        print(f"  📊 Rows returned: {row_count}")
        
        return {
            "success": True,
            "query": sql_query,
            "row_count": row_count,
            "data": safe_data,
            "execution_time_ms": execution_time
        }
        
    except Exception as e:
        execution_time = round((time.time() - start_time) * 1000, 2)
        error_msg = str(e)
        print(f"Supabase query failed: {error_msg}")
        
        return {
            "success": False,
            "query": sql_query,
            "error": error_msg,
            "execution_time_ms": execution_time,
            "cache_info": {
                "hit": False,
                "source": "error"
            }
        }

@csrf_exempt
@require_POST
def execute_sql_query(request):
    """
    Main API endpoint with Redis caching
    """
    
    print("\n" + "="*70)
    print("SQL QUERY API WITH REDIS CACHE")
    print("="*70)
    
    try:
        # Parse request
        data = json.loads(request.body)
        sql_query = data.get('query', '').strip()
        bust_cache = data.get('bust_cache', False)
        cache_timeout = data.get('cache_timeout', CACHE_TIMEOUT)
        print(data)
        query_display = sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
        print(f"Query: {query_display}")
        
        if not sql_query:
            return JsonResponse({
                "success": False,
                "error": "No SQL query provided"
            }, status=400)
        
        if not sql_query.lower().strip().startswith('select'):
            return JsonResponse({
                "success": False,
                "error": "Only SELECT queries are allowed"
            }, status=403)
        
        # Generate cache key
        cache_key = generate_cache_key(sql_query)
        print(f"🔑 Cache key: {cache_key}")
        
        if bust_cache and REDIS_ENABLED:
            print("Cache bust requested")
            try:
                redis_client.delete(cache_key)
            except:
                pass

        if not bust_cache:
            cached_result = get_cached_result(cache_key)
            if cached_result:
                print("✅ CACHE HIT")
                print(f"Total response: {cached_result['cache_info'].get('retrieval_time_ms', '?')}ms")
                
                # Show data sample
                if cached_result['success'] and cached_result.get('data'):
                    data_to_show = cached_result['data']
                    if isinstance(data_to_show, list) and len(data_to_show) > 0:
                        print(f"📄 Sample (cached): {json.dumps(data_to_show[0], default=str)[:80]}...")
                
                print("="*70)
                return JsonResponse(cached_result)
        
        print("❌ CACHE MISS")
        
        # execute query
        result = execute_supabase_query(sql_query)
        
        # Cache successful results
        if result['success'] and REDIS_ENABLED:
            set_cached_result(cache_key, result, timeout=cache_timeout)
        
        # Print results
        if result['success']:
            data_to_show = result.get('data', [])
            if isinstance(data_to_show, list) and len(data_to_show) > 0:
                print(f"📄 Results (first row):")
                row_str = json.dumps(data_to_show[0], default=str)
                print(f"   {row_str[:80]}...")
                
                if len(data_to_show) > 1:
                    print(f"   ... and {len(data_to_show) - 1} more rows")
        
        print(f"⏱️  Total response: {result.get('execution_time_ms', 0)}ms")
        print("="*70)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON")
        print("="*70)
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        }, status=400)
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        print("="*70)
        return JsonResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, status=500)
    
# additional endpoints for cache stats, clear, and test
@csrf_exempt
def cache_stats(request):
    """Get Redis cache statistics"""
    if not REDIS_ENABLED:
        return JsonResponse({
            "success": False,
            "error": "Redis cache is not enabled"
        })
    
    try:
        # Get basic info
        info = redis_client.info()
    
        cache_keys = redis_client.keys("sql_cache:*")
        
        stats = {
            "redis_status": "connected",
            "redis_version": info.get('redis_version', 'N/A'),
            "connected_clients": info.get('connected_clients', 0),
            "used_memory": f"{info.get('used_memory_human', 'N/A')}",
            "total_cache_keys": len(cache_keys),
            "hit_rate": f"{info.get('keyspace_hits', 0)} / {info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)}",
            "hit_percentage": f"{info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1) * 100:.2f}%",
            "uptime_days": info.get('uptime_in_days', 0)
        }
        
        if cache_keys:
            stats["sample_cache_keys"] = [k.decode('utf-8')[:50] + "..." for k in cache_keys[:5]]
        
        return JsonResponse({
            "success": True,
            "cache_stats": stats
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def clear_cache(request):
    """Clear all cached SQL queries"""
    if not REDIS_ENABLED:
        return JsonResponse({
            "success": False,
            "error": "Redis cache is not enabled"
        })
    
    try : 
        cache_keys = redis_client.keys("sql_cache:*")
        
        if cache_keys:
            deleted = redis_client.delete(*cache_keys)
            return JsonResponse({
                "success": True,
                "message": f"Cleared {deleted} cached queries",
                "keys_cleared": len(cache_keys)
            })
        else:
            return JsonResponse({
                "success": True,
                "message": "No cached queries found"
            })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def test_redis(request):
    """Test Redis connection"""
    try:
        redis_client.ping()
        # simple get 
        test_key = "test:connection"
        test_value = f"OK - {time.time()}"
        
        redis_client.setex(test_key, 10, test_value)
        retrieved = redis_client.get(test_key)
        
        return JsonResponse({
            "success": True,
            "redis": "connected",
            "test": "passed",
            "value_set": test_value,
            "value_retrieved": retrieved.decode('utf-8') if retrieved else None,
            "message": "Redis cache is working correctly!"
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "redis": "error",
            "error": str(e)
        })