async def m001_initial(db):
    """
    Initial issuers table.
    """
    await db.execute(
        """
        CREATE TABLE poap.issuers (
            id TEXT PRIMARY KEY,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            meta TEXT NOT NULL DEFAULT '{}'
        );
        """
    )

    """
    Initial POAPs table.
    """
    await db.execute(
        """
        CREATE TABLE poap.poaps (
            id TEXT PRIMARY KEY,
            issuer_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            image TEXT NOT NULL,
            thumbs TEXT NOT NULL DEFAULT '[]',
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
            poap_id TEXT NOT NULL,
            issuer TEXT NOT NULL,
            claim_pubkey TEXT NOT NULL,
            time TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            FOREIGN KEY (poap_id) REFERENCES poaps (id),
            FOREIGN KEY (issuer) REFERENCES issuers (id)
        );
        """
    )
