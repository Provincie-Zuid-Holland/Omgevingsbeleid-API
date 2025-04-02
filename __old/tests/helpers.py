from contextlib import ExitStack, contextmanager


@contextmanager
def patch_multiple(*patches):
    """
    Helper method wrap multiple patches using contextmanager.
    prevents unreadable nesting mess.
    """
    with ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        yield
