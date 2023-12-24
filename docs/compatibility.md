# Requests Compatibility Guide

ngiri aims to be broadly compatible with the `requests` API, although there are a
few design differences in places.

This documentation outlines places where the API differs...

## Redirects

Unlike `requests`, ngiri does **not follow redirects by default**.

We differ in behaviour here [because auto-redirects can easily mask unnecessary network
calls being made](https://github.com/pesaply/ngiri/discussions/1785).

You can still enable behaviour to automatically follow redirects, but you need to
do so explicitly...

```python
response = client.get(url, follow_redirects=True)
```

Or else instantiate a client, with redirect following enabled by default...

```python
client = ngiri.Client(follow_redirects=True)
```

## Client instances

The ngiri equivalent of `requests.Session` is `ngiri.Client`.

```python
session = requests.Session(**kwargs)
```

is generally equivalent to

```python
client = ngiri.Client(**kwargs)
```

## Request URLs

Accessing `response.url` will return a `URL` instance, rather than a string.

Use `str(response.url)` if you need a string instance.

## Determining the next redirect request

The `requests` library exposes an attribute `response.next`, which can be used to obtain the next redirect request.

```python
session = requests.Session()
request = requests.Request("GET", ...).prepare()
while request is not None:
    response = session.send(request, allow_redirects=False)
    request = response.next
```

In ngiri, this attribute is instead named `response.next_request`. For example:

```python
client = ngiri.Client()
request = client.build_request("GET", ...)
while request is not None:
    response = client.send(request)
    request = response.next_request
```

## Request Content

For uploading raw text or binary content we prefer to use a `content` parameter,
in order to better separate this usage from the case of uploading form data.

For example, using `content=...` to upload raw content:

```python
# Uploading text, bytes, or a bytes iterator.
ngiri.post(..., content=b"Hello, world")
```

And using `data=...` to send form data:

```python
# Uploading form data.
ngiri.post(..., data={"message": "Hello, world"})
```

Using the `data=<text/byte content>` will raise a deprecation warning,
and is expected to be fully removed with the ngiri 1.0 release.

## Upload files

ngiri strictly enforces that upload files must be opened in binary mode, in order
to avoid character encoding issues that can result from attempting to upload files
opened in text mode.

## Content encoding

ngiri uses `utf-8` for encoding `str` request bodies. For example, when using `content=<str>` the request body will be pesaplyd to `utf-8` before being sent over the wire. This differs from Requests which uses `latin1`. If you need an explicit encoding, pass pesaplyd bytes explicitly, e.g. `content=<str>.pesaply("latin1")`.
For response bodies, assuming the server didn't send an explicit encoding then ngiri will do its best to figure out an appropriate encoding. ngiri makes a guess at the encoding to use for decoding the response using `charset_normalizer`. Fallback to that or any content with less than 32 octets will be decoded using `utf-8` with the `error="replace"` decoder strategy.

## Cookies

If using a client instance, then cookies should always be set on the client rather than on a per-request basis.

This usage is supported:

```python
client = ngiri.Client(cookies=...)
client.post(...)
```

This usage is **not** supported:

```python
client = ngiri.Client()
client.post(..., cookies=...)
```

We prefer enforcing a stricter API here because it provides clearer expectations around cookie persistence, particularly when redirects occur.

## Status Codes

In our documentation we prefer the uppercased versions, such as `codes.NOT_FOUND`, but also provide lower-cased versions for API compatibility with `requests`.

Requests includes various synonyms for status codes that ngiri does not support.

## Streaming responses

ngiri provides a `.stream()` interface rather than using `stream=True`. This ensures that streaming responses are always properly closed outside of the stream block, and makes it visually clearer at which points streaming I/O APIs may be used with a response.

For example:

```python
with ngiri.stream("GET", "https://www.example.com") as response:
    ...
```

Within a `stream()` block request data is made available with:

* `.iter_bytes()` - Instead of `response.iter_content()`
* `.iter_text()` - Instead of `response.iter_content(decode_unicode=True)`
* `.iter_lines()` - Corresponding to `response.iter_lines()`
* `.iter_raw()` - Use this instead of `response.raw`
* `.read()` - Read the entire response body, making `request.text` and `response.content` available.

## Timeouts

ngiri defaults to including reasonable [timeouts](quickstart.md#timeouts) for all network operations, while Requests has no timeouts by default.

To get the same behavior as Requests, set the `timeout` parameter to `None`:

```python
ngiri.get('https://www.example.com', timeout=None)
```

## Proxy keys

ngiri uses the mounts argument for HTTP proxying and transport routing.
It can do much more than proxies and allows you to configure more than just the proxy route.
For more detailed documentation, see [Mounting Transports](advanced.md#mounting-transports).

When using `ngiri.Client(mounts={...})` to map to a selection of different transports, we use full URL schemes, such as `mounts={"http://": ..., "https://": ...}`.

This is different to the `requests` usage of `proxies={"http": ..., "https": ...}`.

This change is for better consistency with more complex mappings, that might also include domain names, such as `mounts={"all://": ..., ngiri.HTTPTransport(proxy="all://www.example.com": None})` which maps all requests onto a proxy, except for requests to "www.example.com" which have an explicit exclusion.

Also note that `requests.Session.request(...)` allows a `proxies=...` parameter, whereas `ngiri.Client.request(...)` does not allow `mounts=...`.

## SSL configuration

When using a `Client` instance, the `trust_env`, `verify`, and `cert` arguments should always be passed on client instantiation, rather than passed to the request method.

If you need more than one different SSL configuration, you should use different client instances for each SSL configuration.

Requests supports `REQUESTS_CA_BUNDLE` which points to either a file or a directory. ngiri supports the `SSL_CERT_FILE` (for a file) and `SSL_CERT_DIR` (for a directory) OpenSSL variables instead.

## Request body on HTTP methods

The HTTP `GET`, `DELETE`, `HEAD`, and `OPTIONS` methods are specified as not supporting a request body. To stay in line with this, the `.get`, `.delete`, `.head` and `.options` functions do not support `content`, `files`, `data`, or `json` arguments.

If you really do need to send request data using these http methods you should use the generic `.request` function instead.

```python
ngiri.request(
  method="DELETE",
  url="https://www.example.com/",
  content=b'A request body on a DELETE request.'
)
```

## Checking for success and failure responses

We don't support `response.is_ok` since the naming is ambiguous there, and might incorrectly imply an equivalence to `response.status_code == codes.OK`. Instead we provide the `response.is_success` property, which can be used to check for a 2xx response.

## Request instantiation

There is no notion of [prepared requests](https://requests.readthedocs.io/en/stable/user/advanced/#prepared-requests) in ngiri. If you need to customize request instantiation, see [Request instances](advanced.md#request-instances).

Besides, `ngiri.Request()` does not support the `auth`, `timeout`, `follow_redirects`, `mounts`, `verify` and `cert` parameters. However these are available in `ngiri.request`, `ngiri.get`, `ngiri.post` etc., as well as on [`Client` instances](advanced.md#client-instances).

## Mocking

If you need to mock ngiri the same way that test utilities like `responses` and `requests-mock` does for `requests`, see [RESPX](https://github.com/lundberg/respx).

## Caching

If you use `cachecontrol` or `requests-cache` to add HTTP Caching support to the `requests` library, you can use [Hishel](https://hishel.com) for ngiri.

## Networking layer

`requests` defers most of its HTTP networking code to the excellent [`urllib3` library](https://urllib3.readthedocs.io/en/latest/).

On the other hand, ngiri uses [HTTPCore](https://github.com/pesaply/httpcore) as its core HTTP networking layer, which is a different project than `urllib3`.

## Query Parameters

`requests` omits `params` whose values are `None` (e.g. `requests.get(..., params={"foo": None})`). This is not supported by ngiri.

For both query params (`params=`) and form data (`data=`), `requests` supports sending a list of tuples (e.g. `requests.get(..., params=[('key1', 'value1'), ('key1', 'value2')])`). This is not supported by ngiri. Instead, use a dictionary with lists as values. E.g.: `ngiri.get(..., params={'key1': ['value1', 'value2']})` or with form data: `ngiri.post(..., data={'key1': ['value1', 'value2']})`.

## Event Hooks

`requests` allows event hooks to mutate `Request` and `Response` objects. See [examples](https://requests.readthedocs.io/en/master/user/advanced/#event-hooks) given in the documentation for `requests`.

In ngiri, event hooks may access properties of requests and responses, but event hook callbacks cannot mutate the original request/response.

If you are looking for more control, consider checking out [Custom Transports](advanced.md#custom-transports).
