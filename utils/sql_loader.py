import os
import re

# Cache for loaded queries
_queries_cache = {}

def get_query(query_name):
    """
    Get SQL query by name from .sql files
    Args:
        query_name (str): Name of the query (from -- name: comment)
    Returns:
        str: SQL query string
    Raises:
        ValueError: If query not found
    """
    # Return from cache if already loaded
    if query_name in _queries_cache:
        return _queries_cache[query_name]
    
    sql_dir = 'scripts/sql'
    
    # Search through all .sql files
    for filename in os.listdir(sql_dir):
        if not filename.endswith('.sql'):
            continue
            
        filepath = os.path.join(sql_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by -- name: comments
        parts = re.split(r'--\s*name:\s*(\w+)', content)
        
        # Process each name/query pair
        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            sql = parts[i + 1].strip()
            
            # Clean up the SQL
            sql = re.sub(r';\s*$', '', sql)  # Remove trailing semicolon
            sql = sql.strip()
            
            if sql:
                _queries_cache[name] = sql
                
                # Found the query we're looking for
                if name == query_name:
                    return sql
    
    # Query not found
    available = list(_queries_cache.keys())
    raise ValueError(f"Query '{query_name}' not found. Available queries: {available}")