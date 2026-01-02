UPDATE users 
SET password_hash = '$pbkdf2-sha256$29000$uRfiXKtVylkrpbSWkrJWKg$NQRlGkGLBkjoKtNurYCT2aH0H55RQFujDLA/8BSIxEc' 
WHERE username = 'admin';
