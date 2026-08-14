class ResourceNotFoundError(Exception):
    """A missing or inaccessible resource.

    Ownership failures intentionally use the same error as missing records to avoid
    disclosing another customer's resources.
    """
