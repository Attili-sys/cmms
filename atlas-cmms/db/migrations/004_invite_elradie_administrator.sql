-- Give Elradie an Administrator account on the next application start.
-- The startup invitation handler creates the user and sends the welcome email.
INSERT INTO user_invitation (created_at, updated_at, email, role_id)
SELECT CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'elradie@aljazeera.net', role.id
FROM role
WHERE lower(role.name) = 'administrator'
  AND NOT EXISTS (
      SELECT 1 FROM own_user WHERE lower(email) = 'elradie@aljazeera.net'
  )
  AND NOT EXISTS (
      SELECT 1 FROM user_invitation WHERE lower(email) = 'elradie@aljazeera.net'
  )
ORDER BY role.id
LIMIT 1;
