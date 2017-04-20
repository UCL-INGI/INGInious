# -*- coding: utf-8 -*-
"""
Copyright (c) 2014, Massachusetts Institute of Technology
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Python 3-compatible version of PyLTI. To be dropped once they accept our PR.
source: https://github.com/mitodl/pylti
"""

from __future__ import absolute_import

import logging

import oauth2
from xml.etree import ElementTree as etree

from oauth2 import STRING_TYPES
from six.moves.urllib.parse import urlparse, urlencode

log = logging.getLogger('pylti.common')  # pylint: disable=invalid-name

LTI_PROPERTY_LIST = [
    'oauth_consumer_key',
    'launch_presentation_return_url',
    'user_id',
    'oauth_nonce',
    'context_label',
    'context_id',
    'resource_link_title',
    'resource_link_id',
    'lis_person_contact_email_primary',
    'lis_person_contact_emailprimary',
    'lis_person_name_full',
    'lis_person_name_family',
    'lis_person_name_given',
    'lis_result_sourcedid',
    'lis_person_sourcedid',
    'launch_type',
    'lti_message',
    'lti_version',
    'roles',
    'lis_outcome_service_url'
]

LTI_ROLES = {
    u'staff': [u'Administrator', u'Instructor', ],
    u'instructor': [u'Instructor', ],
    u'administrator': [u'Administrator', ],
    u'student': [u'Student', u'Learner', ]
    # There is also a special role u'any' that ignores role check
}

LTI_SESSION_KEY = u'lti_authenticated'

LTI_REQUEST_TYPE = [u'any', u'initial', u'session']


class LTIOAuthServer(oauth2.Server):
    """
    Largely taken from reference implementation
    for app engine at https://code.google.com/p/ims-dev/
    """

    def __init__(self, consumers, signature_methods=None):
        """
        Create OAuth server
        """
        super(LTIOAuthServer, self).__init__(signature_methods)
        self.consumers = consumers

    def lookup_consumer(self, key):
        """
        Search through keys
        """
        if not self.consumers:
            log.critical(("No consumers defined in settings."
                          "Have you created a configuration file?"))
            return None

        consumer = self.consumers.get(key)
        if not consumer:
            log.info("Did not find consumer, using key: %s ", key)
            return None

        secret = consumer.get('secret', None)
        if not secret:
            log.critical(('Consumer %s, is missing secret'
                          'in settings file, and needs correction.'), key)
            return None
        return oauth2.Consumer(key, secret)

    def lookup_cert(self, key):
        """
        Search through keys
        """
        if not self.consumers:
            log.critical(("No consumers defined in settings."
                          "Have you created a configuration file?"))
            return None

        consumer = self.consumers.get(key)
        if not consumer:
            log.info("Did not find consumer, using key: %s ", key)
            return None

        cert = consumer.get('cert', None)
        return cert


class LTIException(Exception):
    """
    Custom LTI exception for proper handling
    of LTI specific errors
    """
    pass


class LTINotInSessionException(LTIException):
    """
    Custom LTI exception for proper handling
    of LTI specific errors
    """
    pass


class LTIRoleException(LTIException):
    """
    Exception class for when LTI user doesn't have the
    right role.
    """
    pass


class LTIPostMessageException(LTIException):
    """
    Exception class for when LTI user doesn't have the
    right role.
    """
    pass


def _post_patched_request(consumers, lti_key, body,
                          url, method, content_type):
    """
    Authorization header needs to be capitalized for some LTI clients
    this function ensures that header is capitalized

    :param body: body of the call
    :param client: OAuth Client
    :param url: outcome url
    :return: response
    """
    # pylint: disable=too-many-locals, too-many-arguments
    oauth_server = LTIOAuthServer(consumers)
    oauth_server.add_signature_method(SignatureMethod_HMAC_SHA1_Unicode())
    lti_consumer = oauth_server.lookup_consumer(lti_key)
    lti_cert = oauth_server.lookup_cert(lti_key)

    secret = lti_consumer.secret

    consumer = oauth2.Consumer(key=lti_key, secret=secret)
    client = oauth2.Client(consumer)

    if lti_cert:
        client.add_certificate(key=lti_cert, cert=lti_cert, domain='')
        log.debug("cert %s", lti_cert)

    import httplib2

    http = httplib2.Http
    # pylint: disable=protected-access
    normalize = http._normalize_headers

    def my_normalize(self, headers):
        """ This function patches Authorization header """
        ret = normalize(self, headers)
        if 'authorization' in ret:
            ret['Authorization'] = ret.pop('authorization')
        log.debug("headers")
        log.debug(headers)
        return ret

    http._normalize_headers = my_normalize
    monkey_patch_function = normalize
    response, content = client.request(
        url,
        method,
        body=body.encode('utf-8'),
        headers={'Content-Type': content_type})

    http = httplib2.Http
    # pylint: disable=protected-access
    http._normalize_headers = monkey_patch_function

    log.debug("key %s", lti_key)
    log.debug("secret %s", secret)
    log.debug("url %s", url)
    log.debug("response %s", response)
    log.debug("content %s", format(content))

    return response, content


def post_message(consumers, lti_key, url, body):
    """
        Posts a signed message to LTI consumer

    :param consumers: consumers from config
    :param lti_key: key to find appropriate consumer
    :param url: post url
    :param body: xml body
    :return: success
    """
    content_type = 'application/xml'
    method = 'POST'
    (_, content) = _post_patched_request(
        consumers,
        lti_key,
        body,
        url,
        method,
        content_type,
    )

    is_success = b"<imsx_codeMajor>success</imsx_codeMajor>" in content
    log.debug("is success %s", is_success)
    return is_success


def post_message2(consumers, lti_key, url, body,
                  method='POST', content_type='application/xml'):
    """
        Posts a signed message to LTI consumer using LTI 2.0 format

    :param: consumers: consumers from config
    :param: lti_key: key to find appropriate consumer
    :param: url: post url
    :param: body: xml body
    :return: success
    """
    # pylint: disable=too-many-arguments
    (response, _) = _post_patched_request(
        consumers,
        lti_key,
        body,
        url,
        method,
        content_type,
    )

    is_success = response.status == 200
    log.debug("is success %s", is_success)

    return is_success


def verify_request_common(consumers, url, method, headers, params):
    """
    Verifies that request is valid

    :param consumers: consumers from config file
    :param url: request url
    :param method: request method
    :param headers: request headers
    :param params: request params
    :return: is request valid
    """

    log.debug("consumers %s", consumers)
    log.debug("url %s", url)
    log.debug("method %s", method)
    log.debug("headers %s", headers)
    log.debug("params %s", params)

    oauth_server = LTIOAuthServer(consumers)
    oauth_server.add_signature_method(
        SignatureMethod_PLAINTEXT_Unicode())
    oauth_server.add_signature_method(
        SignatureMethod_HMAC_SHA1_Unicode())

    # Check header for SSL before selecting the url
    if headers.get('X-Forwarded-Proto', 'http') == 'https':
        url = url.replace('http:', 'https:', 1)

    oauth_request = Request_Fix_Duplicate.from_request(  # pylint: disable=no-member
        method,
        url,
        headers=dict(headers),
        parameters=params
    )

    if not oauth_request:
        log.info('Received non oauth request on oauth protected page')
        raise LTIException('This page requires a valid oauth session '
                           'or request')
    try:
        # pylint: disable=protected-access
        oauth_consumer_key = oauth_request.get_parameter('oauth_consumer_key')
        consumer = oauth_server.lookup_consumer(oauth_consumer_key)
        if not consumer:
            raise oauth2.Error('Invalid consumer.')
        oauth_server.verify_request(oauth_request, consumer, None)
    except oauth2.Error:
        # Rethrow our own for nice error handling (don't print
        # error message as it will contain the key
        raise LTIException("OAuth error: Please check your key and secret")

    return True


def generate_request_xml(message_identifier_id, operation,
                         lis_result_sourcedid, score):
    # pylint: disable=too-many-locals
    """
    Generates LTI 1.1 XML for posting result to LTI consumer.

    :param message_identifier_id:
    :param operation:
    :param lis_result_sourcedid:
    :param score:
    :return: XML string
    """
    root = etree.Element(u'imsx_POXEnvelopeRequest',
                         xmlns=u'http://www.imsglobal.org/services/'
                               u'ltiv1p1/xsd/imsoms_v1p0')

    header = etree.SubElement(root, 'imsx_POXHeader')
    header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
    version = etree.SubElement(header_info, 'imsx_version')
    version.text = 'V1.0'
    message_identifier = etree.SubElement(header_info,
                                          'imsx_messageIdentifier')
    message_identifier.text = message_identifier_id
    body = etree.SubElement(root, 'imsx_POXBody')
    xml_request = etree.SubElement(body, '%s%s' % (operation, 'Request'))
    record = etree.SubElement(xml_request, 'resultRecord')

    guid = etree.SubElement(record, 'sourcedGUID')

    sourcedid = etree.SubElement(guid, 'sourcedId')
    sourcedid.text = lis_result_sourcedid
    if score is not None:
        result = etree.SubElement(record, 'result')
        result_score = etree.SubElement(result, 'resultScore')
        language = etree.SubElement(result_score, 'language')
        language.text = 'en'
        text_string = etree.SubElement(result_score, 'textString')
        text_string.text = score.__str__()
    ret = "<?xml version='1.0' encoding='utf-8'?>\n{}".format(
        etree.tostring(root, encoding='utf-8').decode('utf-8'))

    log.debug("XML Response: \n%s", ret)
    return ret


class SignatureMethod_HMAC_SHA1_Unicode(oauth2.SignatureMethod_HMAC_SHA1):
    """
    Temporary workaround for
    https://github.com/joestump/python-oauth2/issues/207

    Original code is Copyright (c) 2007 Leah Culver, MIT license.
    """

    def check(self, request, consumer, token, signature):
        """
        Returns whether the given signature is the correct signature for
        the given consumer and token signing the given request.
        """
        built = self.sign(request, consumer, token)
        if isinstance(signature, STRING_TYPES):
            signature = signature.encode("utf8")
        return built == signature


class SignatureMethod_PLAINTEXT_Unicode(oauth2.SignatureMethod_PLAINTEXT):
    """
    Temporary workaround for
    https://github.com/joestump/python-oauth2/issues/207

    Original code is Copyright (c) 2007 Leah Culver, MIT license.
    """

    def check(self, request, consumer, token, signature):
        """
        Returns whether the given signature is the correct signature for
        the given consumer and token signing the given request.
        """
        built = self.sign(request, consumer, token)
        if isinstance(signature, STRING_TYPES):
            signature = signature.encode("utf8")
        return built == signature


class Request_Fix_Duplicate(oauth2.Request):
    """
    Temporary workaround for
    https://github.com/joestump/python-oauth2/pull/197

    Original code is Copyright (c) 2007 Leah Culver, MIT license.
    """

    def get_normalized_parameters(self):
        """
        Return a string that contains the parameters that must be signed.
        """
        items = []
        for key, value in self.items():
            if key == 'oauth_signature':
                continue
            # 1.0a/9.1.1 states that kvp must be sorted by key, then by value,
            # so we unpack sequence values into multiple items for sorting.
            if isinstance(value, STRING_TYPES):
                items.append(
                    (oauth2.to_utf8_if_string(key), oauth2.to_utf8(value))
                )
            else:
                try:
                    value = list(value)
                except TypeError as e:
                    assert 'is not iterable' in str(e)
                    items.append(
                        (oauth2.to_utf8_if_string(key),
                         oauth2.to_utf8_if_string(value))
                    )
                else:
                    items.extend(
                        (oauth2.to_utf8_if_string(key),
                         oauth2.to_utf8_if_string(item))
                        for item in value
                    )

        # Include any query string parameters from the provided URL
        query = urlparse(self.url)[4]
        url_items = self._split_url_string(query).items()
        url_items = [
            (oauth2.to_utf8(k), oauth2.to_utf8_optional_iterator(v))
            for k, v in url_items if k != 'oauth_signature'
            ]

        # Merge together URL and POST parameters.
        # Eliminates parameters duplicated between URL and POST.
        items_dict = {}
        for k, v in items:
            items_dict.setdefault(k, []).append(v)
        for k, v in url_items:
            if not (k in items_dict and v in items_dict[k]):
                items.append((k, v))

        items.sort()

        encoded_str = urlencode(items, True)
        # Encode signature parameters per Oauth Core 1.0 protocol
        # spec draft 7, section 3.6
        # (http://tools.ietf.org/html/draft-hammer-oauth-07#section-3.6)
        # Spaces must be encoded with "%20" instead of "+"
        return encoded_str.replace('+', '%20').replace('%7E', '~')
