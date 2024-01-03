# The migration file is like a blockchain, never edit only add!

async def m001_initial(db):
    """
    Initial poaplates table.
    """
    await db.execute(
        """
        CREATE TABLE poapextension.poap (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            name TEXT NOT NULL,
            total INTEGER DEFAULT 0,
            lnurlpayamount INTEGER DEFAULT 0
        );
    """
    )

# Here we are adding an extra field to the database

async def m002_addtip_wallet(db):
    """
    Add total to poaplates table
    """
    await db.execute(
        """
        ALTER TABLE poapextension.poap ADD lnurlwithdrawamount INTEGER DEFAULT 0;
    """
    )

# Here we add another field to the database, always add never edit!

async def m004_addtip_wallet(db):
    """
    Add total to poaplates table
    """
    await db.execute(
        """
        ALTER TABLE poapextension.poap ADD lnurlwithdraw TEXT;
    """
    )

# Here we add another field to the database

async def m005_addtip_wallet(db):
    """
    Add total to poaplates table
    """
    await db.execute(
        """
        ALTER TABLE poapextension.poap ADD lnurlpay TEXT;
    """
    )