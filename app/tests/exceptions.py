class FixtureFactoryError(Exception):
    """Exception raised for errors when building test setup."""

    def __init__(self, class_name: str, original_exception: Exception):
        self.class_name = class_name
        self.exception = original_exception
        self.message = f"Unable to setup fixture in class: {class_name}"
        super().__init__(self.message)


def fixture_factory_error_wrapper(cls):
    class WrappedClass:
        def __init__(self, *args, **kwargs):
            self.wrapped_instance = cls(*args, **kwargs)

        def __getattribute__(self, name):
            wrapped_instance = object.__getattribute__(self, "wrapped_instance")
            attr = object.__getattribute__(wrapped_instance, name)
            if not callable(attr):
                return attr

            def wrapped(*args, **kwargs):
                try:
                    return attr(*args, **kwargs)
                except Exception as e:
                    raise FixtureFactoryError(wrapped_instance.__class__.__name__, e) from e

            if name == "__name__":
                return wrapped_instance.__name__

            return wrapped

    return WrappedClass
