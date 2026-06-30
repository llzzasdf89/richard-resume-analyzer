import os

import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT,
            name TEXT,
            avatar_url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_identities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider TEXT NOT NULL,
            provider_user_id TEXT NOT NULL,
            auth_provider TEXT,
            raw_profile JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(provider, provider_user_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            original_filename TEXT NOT NULL,
            storage_key TEXT NOT NULL,
            file_size BIGINT NOT NULL,
            mime_type TEXT NOT NULL,
            parsed_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
            jd_text TEXT NOT NULL,
            job_title TEXT,
            company TEXT,
            status TEXT NOT NULL,
            score INT,
            progress INT NOT NULL DEFAULT 0,
            current_step TEXT,
            steps_json JSONB,
            result_json JSONB,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            format TEXT NOT NULL,
            content TEXT,
            storage_key TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            request_id TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id UUID,
            response_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(user_id, request_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jd_knowledge (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            embedding vector(1024)
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS jd_knowledge_embedding_idx
        ON jd_knowledge USING hnsw (embedding vector_cosine_ops)
        """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialization completed")
