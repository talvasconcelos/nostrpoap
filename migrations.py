async def m001_initial(db):
    """
    Initial issuers table.
    """
    await db.execute(
        """
        CREATE TABLE poap.issuers (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            meta TEXT NOT NULL DEFAULT '{}'
        );
        """
    )

    """
    Initial POAP badges table.
    """
    await db.execute(
        """
        CREATE TABLE poap.badges (
            id TEXT PRIMARY KEY,
            issuer_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            image TEXT NOT NULL,
            thumbs TEXT,
            event_id TEXT,
            event_created_at INT
        );
        """
    )

    """
    Initial awards table.
    """
    await db.execute(
        f"""
        CREATE TABLE poap.awards (
            id TEXT PRIMARY KEY,
            badge_id TEXT NOT NULL,
            issuer TEXT NOT NULL,
            claim_pubkey TEXT NOT NULL,
            event_id TEXT,
            event_created_at INT,
            FOREIGN KEY (badge_id) REFERENCES poaps (id),
            FOREIGN KEY (issuer) REFERENCES issuers (id)
        );
        """
    )
