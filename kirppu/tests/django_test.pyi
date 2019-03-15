import typing

import django.core.handlers.wsgi
import django.http.request
import django.test.client
import django.template
import django.template.context
import django.urls.resolvers


# Documentation copied and shortened from Django documentation, topics/testing/tools.html#django.test.Response
class DjangoResponse(object):

    # The test client that was used to make the request that resulted in the response.
    client: django.test.client.Client

    # The body of the response, as a bytestring. This is the final page content as rendered by the view, or any error message.
    content: bytes

    # The template Context instance that was used to render the template that produced the response content.
    #
    # If the rendered page used multiple templates, then context will be a list of Context objects, in the order in which they were rendered.
    #
    # Regardless of the number of templates used during rendering, you can retrieve context values using the [] operator. For example, the context variable name could be retrieved using:
    context: django.template.context.Context

    def json(self, **kwargs) -> typing.Optional[typing.Any]:
        """The body of the response, parsed as JSON. Extra keyword arguments are passed to json.loads()."""
        pass

    # The request data that stimulated the response.
    request: django.http.request.HttpRequest

    # The WSGIRequest instance generated by the test handler that generated the response.
    wsgi_request: django.core.handlers.wsgi.WSGIRequest

    # The HTTP status of the response, as an integer. For a full list of defined codes, see the IANA status code registry.
    status_code: int

    # A list of Template instances used to render the final content, in the order they were rendered. For each template in the list, use template.name to get the template’s file name, if the template was loaded from a file. (The name is a string such as 'admin/index.html'.)
    templates: typing.List[django.template.Template]

    # An instance of ResolverMatch for the response.
    resolver_match: django.urls.resolvers.ResolverMatch