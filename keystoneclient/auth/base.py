# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc

import six
import stevedore

from keystoneclient import exceptions

PLUGIN_NAMESPACE = 'keystoneclient.auth.plugin'


def get_plugin_class(name):
    """Retrieve a plugin class by its entrypoint name.

    :param str name: The name of the object to get.

    :returns: An auth plugin class.

    :raises exceptions.NoMatchingPlugin: if a plugin cannot be created.
    """
    try:
        mgr = stevedore.DriverManager(namespace=PLUGIN_NAMESPACE,
                                      name=name,
                                      invoke_on_load=False)
    except RuntimeError:
        msg = 'The plugin %s could not be found' % name
        raise exceptions.NoMatchingPlugin(msg)

    return mgr.driver


@six.add_metaclass(abc.ABCMeta)
class BaseAuthPlugin(object):
    """The basic structure of an authentication plugin."""

    @abc.abstractmethod
    def get_token(self, session, **kwargs):
        """Obtain a token.

        How the token is obtained is up to the plugin. If it is still valid
        it may be re-used, retrieved from cache or invoke an authentication
        request against a server.

        There are no required kwargs. They are passed directly to the auth
        plugin and they are implementation specific.

        Returning None will indicate that no token was able to be retrieved.

        :param session: A session object so the plugin can make HTTP calls.
        :return string: A token to use.
        """

    def get_endpoint(self, session, **kwargs):
        """Return an endpoint for the client.

        There are no required keyword arguments to ``get_endpoint`` as a plugin
        implementation should use best effort with the information available to
        determine the endpoint. However there are certain standard options that
        will be generated by the clients and should be used by plugins:

        - ``service_type``: what sort of service is required.
        - ``service_name``: the name of the service in the catalog.
        - ``interface``: what visibility the endpoint should have.
        - ``region_name``: the region the endpoint exists in.

        :param Session session: The session object that the auth_plugin
                                belongs to.

        :returns string: The base URL that will be used to talk to the
                         required service or None if not available.
        """

    def invalidate(self):
        """Invalidate the current authentication data.

        This should result in fetching a new token on next call.

        A plugin may be invalidated if an Unauthorized HTTP response is
        returned to indicate that the token may have been revoked or is
        otherwise now invalid.

        :returns bool: True if there was something that the plugin did to
                       invalidate. This means that it makes sense to try again.
                       If nothing happens returns False to indicate give up.
        """
        return False

    @classmethod
    def get_options(cls):
        """Return the list of parameters associated with the auth plugin.

        This list may be used to generate CLI or config arguments.

        :returns list: A list of Param objects describing available plugin
                       parameters.
        """
        return []

    @classmethod
    def load_from_options(cls, **kwargs):
        """Create a plugin from the arguments retrieved from get_options.

        A client can override this function to do argument validation or to
        handle differences between the registered options and what is required
        to create the plugin.
        """
        return cls(**kwargs)
