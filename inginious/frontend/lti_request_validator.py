# coding=utf-8
import datetime
from oauthlib.oauth1 import RequestValidator
from pymongo.errors import DuplicateKeyError


class LTIValidator(RequestValidator):  # pylint: disable=abstract-method
    enforce_ssl = True
    client_key_length = (1, 30)
    nonce_length = (20, 64)
    realms = [""]

    @property
    def dummy_client(self):
        return ""  # Not used: validation works for all

    @property
    def dummy_request_token(self):
        return ""  # Not used: validation works for all

    @property
    def dummy_access_token(self):
        return ""  # Not used: validation works for all

    def __init__(self, collection, keys, nonce_validity=datetime.timedelta(minutes=10), debug=False):
        """
        :param collection: Pymongo collection. The collection must have a unique index on ("timestamp","nonce") and a TTL expiration on ("expiration")
        :param keys: dictionnary of allowed client keys, and their associated secret
        :param nonce_validity: timedelta representing the time during which a nonce is considered as valid
        :param debug:
        """
        super().__init__()

        self.enforce_ssl = debug
        self._collection = collection
        self._nonce_validity = nonce_validity
        self._keys = keys

    def validate_client_key(self, client_key, request):
        return client_key in self._keys

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce, request, request_token=None, access_token=None):
        try:
            date = datetime.datetime.utcfromtimestamp(int(timestamp))
            self._collection.insert_one({"timestamp": date,
                                         "nonce": nonce,
                                         "expiration": date + self._nonce_validity})
            return True
        except ValueError: # invalid timestamp
            return False
        except DuplicateKeyError:
            return False

    def get_client_secret(self, client_key, request):
        return self._keys[client_key] if client_key in self._keys else None
