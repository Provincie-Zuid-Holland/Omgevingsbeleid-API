
# from .fixtures import populate_users, populate_modules


class TestSearch:
    """
    integration test of search methods with database input / output
    """

    def test_request_endpoint_initial_state(self, local_tables):
        assert 1 == 1
