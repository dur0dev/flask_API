-- name: login_query
SELECT 
    COUNT(*) as count
FROM 
    nba.dim_users u
WHERE 
    u.email = :email
    and u.password_hash = :password_hash

-- name: get_user_info
SELECT 
    *
FROM 
    nba.dim_users u
WHERE 
    u.email = :email
    and u.password_hash = :password_hash