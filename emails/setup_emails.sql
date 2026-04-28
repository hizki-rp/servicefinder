-- SQL script to create email tables manually
-- Run this if migrations don't work

-- EmailTemplate table
CREATE TABLE IF NOT EXISTS emails_emailtemplate (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- EmailLog table
CREATE TABLE IF NOT EXISTS emails_emaillog (
    id BIGSERIAL PRIMARY KEY,
    recipient_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    template_id BIGINT REFERENCES emails_emailtemplate(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
);

-- BulkEmail table
CREATE TABLE IF NOT EXISTS emails_bulkemail (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    template_id BIGINT REFERENCES emails_emailtemplate(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sending', 'sent', 'failed')),
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

-- BulkEmail recipients many-to-many table
CREATE TABLE IF NOT EXISTS emails_bulkemail_recipients (
    id BIGSERIAL PRIMARY KEY,
    bulkemail_id BIGINT NOT NULL REFERENCES emails_bulkemail(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE(bulkemail_id, user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS emails_emaillog_recipient_idx ON emails_emaillog(recipient_id);
CREATE INDEX IF NOT EXISTS emails_emaillog_status_idx ON emails_emaillog(status);
CREATE INDEX IF NOT EXISTS emails_emaillog_created_at_idx ON emails_emaillog(created_at);
CREATE INDEX IF NOT EXISTS emails_bulkemail_created_at_idx ON emails_bulkemail(created_at);
CREATE INDEX IF NOT EXISTS emails_bulkemail_status_idx ON emails_bulkemail(status);

-- Insert default templates
INSERT INTO emails_emailtemplate (name, subject, body, is_active) VALUES
('welcome', 'Welcome to Mert Service!', 'Dear {user_name},

Welcome to Mert Service! We''re excited to have you join our community connecting service providers with clients across Ethiopia.

Your account has been successfully created and you can now:
- Browse trusted service providers in your area
- Contact providers directly and get instant quotes
- Read reviews from real customers
- Discover services near you with location-based search

Whether you need home services, professional help, or want to become a provider yourself, Mert Service makes it easy!

If you have any questions, feel free to contact our support team.

Best regards,
The Mert Service Team', TRUE),

('provider_welcome', 'Welcome to Mert Service - Start Growing Your Business', 'Dear {user_name},

Congratulations on becoming a Mert Service provider! You''re now part of a growing network of trusted service professionals across Ethiopia.

Next steps to get started:
- Complete your provider profile
- Upload verification documents (National ID)
- Add your services with detailed descriptions
- Set your pricing and availability

Once verified, your services will be visible to thousands of potential clients in your area!

Best regards,
The Mert Service Team', TRUE),

('verification_approved', 'Your Mert Service verification has been approved!', 'Dear {user_name},

Great news! Your verification documents have been approved and your provider account is now active.

Your services are now visible to clients and you can start receiving inquiries. Make sure to:
- Keep your profile updated
- Respond promptly to client inquiries
- Maintain high service quality
- Collect positive reviews

Welcome to the Mert Service provider community!

Best regards,
The Mert Service Team', TRUE),

('verification_rejected', 'Action Required: Mert Service verification needs attention', 'Dear {user_name},

We''ve reviewed your verification documents and unfortunately we need you to resubmit them.

Reason: {rejection_reason}

Please upload clear, valid documents to complete your verification. Once approved, you''ll be able to start offering your services to clients.

If you have questions, contact our support team.

Best regards,
The Mert Service Team', TRUE)
ON CONFLICT (name) DO NOTHING;




