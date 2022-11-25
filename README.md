# social-edu-federation: An SAML authentication backend for python-social-auth dedicated to education federation (RENATER)

[![Python version](https://img.shields.io/badge/Python-3.8%20|%203.9%20|%203.10-blue.svg)](https://www.python.org/)
[![Django version](https://img.shields.io/badge/Django-3.2%20|%204.0-green.svg)](https://www.djangoproject.com/)
[![CircleCI](https://circleci.com/gh/openfun/social-edu-federation/tree/main.svg?style=svg)](https://circleci.com/gh/openfun/social-edu-federation/tree/main)

## Overview

This library provides an authentication backend which can be used with
[Python Social Auth](https://github.com/python-social-auth/social-core)
and optionally
[Python Social Auth - Django](https://github.com/python-social-auth/social-app-django)
to connect your application to an education SAML federation.

Before beginning, you must read the above documentations.

For now, it is only limited to the
[RENATER](https://services.renater.fr/federation/en/documentation/generale/metadata/index)'s
"Féderation Éducation-Recherche" (FER) federation.


## Architecture

`social-edu-federation` is divided in two parts:
- The SAML backend and metadata parser, customized for the FER federation,
  usable with Python Social Auth.
- The Django integration which provides: base views to provide metadata, list available
  Identity Providers and testing material for local development.


### Authentication behavior

This library parses the metadata to extract base SAML authentication for each identity
provider in the federation metadata plus some extra information
(see below *Setup - Core* section)

The authentication process can be summarized in few steps:

- The federation metadata are parsed to fetch the identity providers list.
- User choose an identity provider in the list with which they have an account and want to login.
- The backend makes an SAML authentication request and redirects the user to the identity provider
  "single login" page.
- The user logs in on the identity provider website and is redirected to our (Service Provider) site.
- The SAML FER backend will extract authentication data it needs from the authentication response
  assertions.
  The used assertions are:
  - **urn:oid:2.5.4.4** (sn) aka (surname)
    This represents the user's first name.
  - **urn:oid:2.5.4.42** (givenName) aka (gn)
    This represents the user's last name.
  - **urn:oid:2.16.840.1.113730.3.1.241** (displayName)
    This represents the user's full name.
  - **urn:oid:0.9.2342.19200300.100.1.3** (mail)
    Provides us the user email, we use it as email address and username.
  - **urn:oid:1.3.6.1.4.1.5923.1.1.1.1** (eduPersonAffiliation)
    Provides us the user's role(s) list.
    This is not mandatory.

  Fields we do not use:
   - **urn:oid:1.3.6.1.4.1.7135.1.2.1.14** (supannEtablissement)

  All fields are documented on
  [Renater supann](https://services.renater.fr/documentation/supann/supann2021/recommandations/attributs/liste_des_attributs).
- The authentication response passes through the "Social auth" pipeline.
  `social-edu-federation` provides one extra step to replace the
  `social_core.pipeline.user.create_user` original one. This step allows to have a fallback
  on the user's *full name* if one of the *first name* or *last name* is not available.

## Setup

### Core

You may install only the library core which will provide you with:
- The FER metadata parser (see `social_edu_federation.parser.FederationMetadataParser`)
  which is an extension of the original `python3-saml`'s `OneLogin_Saml2_IdPMetadataParser`
  and provides extra features as:
  - Extract all the identity providers at once
  - Extract extra information from each identity provider metadata (
    the identity provider's display name,
    the identity provider's organization name,
    the identity provider's organization display name)
- A basic "metadata store" which is not really helpful but organizes the process of fetching
  the metadata and convert it to a Python Social Auth like object, usable by the authentication
  backend.
- The SAML authentication backend which is preconfigured to be used with the FER federation.

```shell
$ pip install social-edu-federation
```

### Django integration

If you also want to add this library into a Django project you may explicitly add the `django` extra while installing the library:

```shell
$ pip install social-edu-federation[django]
```

It is also recommended to add `social_edu_federation.django.apps.PythonSocialEduFedAuthConfig`
to your `INSTALLED_APPS` to get the following features:

- A Django check which asserts the default "metadata store" is overridden.
- The `prefetch_saml_fer_metadata` management command (see *Cache management* below).
- The static files and Django views default templates (see *Using the default views* below).

#### Cache management

When using the Django integration, it is highly recommended to define a Django setting to
tell `social_edu_federation` to use the "metadata store with cache". This will avoid fetching
the whole federation metadata everytime we need an information about one identity
provider.

```python
# settings.py
SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = "social_edu_federation.django.metadata_store.CachedMetadataStore"
```

This "metadata store" will use the Django `default` cache which can be easily replaced by
the cache backend of your choice:

```python
# settings.py
SOCIAL_AUTH_SAML_FER_DJANGO_CACHE = "redis"

assert SOCIAL_AUTH_SAML_FER_DJANGO_CACHE in CACHES, "cache backend name is not in settings.CACHES"
```

If you installed the `social_edu_federation` Django application, you will be able to
fill the cache asynchronously using the `prefetch_saml_fer_metadata` management
command, by defining a cron job which will call
`django-admin prefetch_saml_fer_metadata saml_fer` to refresh the FER cache.
Using this make sure that no actual user has to wait for the full federation metadata to load
loading time.

#### Project setup

For a basic use of the FER backend for authentication you will need to define:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "social_django.apps.PythonSocialAuthConfig",  # see python-social-auth
    "social_edu_federation.django.apps.PythonSocialEduFedAuthConfig",
]
MIDDLEWARE = [
    # ...
    "social_django.middleware.SocialAuthExceptionMiddleware",  # At the end
]

AUTHENTICATION_BACKENDS = [
    "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    "django.contrib.auth.backends.ModelBackend",  # only if you keep Django basic auth
]

# Python social auth
SOCIAL_AUTH_JSONFIELD_ENABLED = True

SOCIAL_AUTH_SAML_FER_SECURITY_CONFIG = {
    "authnRequestsSigned": True,
    "signMetadata": True,
    "wantAssertionsSigned": True,
    "rejectDeprecatedAlgorithm": True,
}

# Specific social_edu_federation
SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = "social_edu_federation.django.metadata_store.CachedMetadataStore"

# SOCIAL_AUTH_SAML_FER_SP_ENTITY_ID should be a URL that includes a domain name you own
SOCIAL_AUTH_SAML_FER_SP_ENTITY_ID = "https://you-site.example/saml/metadata/"
# SOCIAL_AUTH_SAML_FER_SP_PUBLIC_CERT X.509 certificate for the key pair that
# your app will use
SOCIAL_AUTH_SAML_FER_SP_PUBLIC_CERT = "MII..."
# SOCIAL_AUTH_SAML_FER_SP_PRIVATE_KEY The private key to be used by your app
SOCIAL_AUTH_SAML_FER_SP_PRIVATE_KEY = "MII..."

# Next certificate management, keep empty when next certificate is still not known
SOCIAL_AUTH_SAML_FER_SP_NEXT_PUBLIC_CERT = None
SOCIAL_AUTH_SAML_FER_SP_EXTRA = (
    {
        "x509certNew": SOCIAL_AUTH_SAML_FER_SP_NEXT_PUBLIC_CERT,
    }
    if SOCIAL_AUTH_SAML_FER_SP_NEXT_PUBLIC_CERT
    else {}
)

SOCIAL_AUTH_SAML_FER_ORG_INFO = {  # specify values for English at a minimum
    "en-US": {
        "name": "Organization name",
        "displayname": "Organization display name",
        "url": "https://you-site.example",
    }
}
# SOCIAL_AUTH_SAML_FER_TECHNICAL_CONTACT technical contact responsible for your app
SOCIAL_AUTH_SAML_FER_TECHNICAL_CONTACT = {
    "givenName": "Dev team",
    "emailAddress": "dev@example.com",
}
# SOCIAL_AUTH_SAML_FER_SUPPORT_CONTACT support contact for your app
SOCIAL_AUTH_SAML_FER_SUPPORT_CONTACT = {
    "givenName": "Dev team",
    "emailAddress": "dev@example.com",
}
# SOCIAL_AUTH_SAML_FER_ENABLED_IDPS is not required since the
# SAML FER backend is overridden to allow dynamic IdPs.
# see social_edu_federation.backends.saml_fer.FERSAMLAuth.get_idp(idp_name)

# Custom parameter to define the FER Federation Metadata
SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
    "https://metadata.federation.renater.fr/renater/main/main-idps-renater-metadata.xml"
)

# Use (or not) the default pipeline with the first/last name cleanup step
from social_edu_federation.pipeline import DEFAULT_EDU_FED_AUTH_PIPELINE
SOCIAL_AUTH_SAML_FER_PIPELINE = DEFAULT_EDU_FED_AUTH_PIPELINE
```

#### Using the default views

To make your Service Provider metadata publicly available, you will need to add
the following URL:

```python
# some_module/urls.py
from django.urls import path

from social_edu_federation.django.views import EduFedMetadataView


urlpatterns = [
    # ...
    path(
        "saml/metadata/",
        EduFedMetadataView.as_view(backend_name="saml_fer"),
        name="saml_fer_metadata",
    ),
]
```

You may also want to have a look at the provided `EduFedIdpChoiceView` which serves
the list of identity providers in the federation. It includes a cookie mechanism for the
user to easily find the last used identity providers.

An easy way to use it:

```python
# some_module/views.py
from social_edu_federation.django.views import EduFedIdpChoiceView


class CustomizedEduFederationIdpChoiceView(EduFedIdpChoiceView):
    """Display the list of all available Identity providers using our own template."""

    template_extends = "my_site/base.html"


# some_module/urls.py
from django.urls import path

from . import views

urlpatterns = [
    # ...
    path(
        "saml/renater_fer_idp_choice/",
        views.CustomizedEduFederationIdpChoiceView.as_view(backend_name="saml_fer"),
        name="saml_fer_idp_choice",
    ),
]
```

#### Testing views

`social-edu-federation` comes along with testing views to ease the development process.
Those testing views are to be used when you want to test the whole authentication loop on
your local computer.

How to plug the testing views in your project is not detailed here, but you can
try them (or see how they are plugged) by running the `social-edu-federation` tests suite.

Fetch the project:

```shell
git clone git@github.com:openfun/social-edu-federation.git
```

Create a virtual environment and install requirements:

```shell
cd social-edu-federation
pip install .[dev,django]
```

Run the standalone Django project:

```shell
make run_django
```

Open it in your browser.

##### Docker

In case you want to plug the testing views in your own project which is run in a Docker container
you will probably need to define the port used in the generated metadata. By default,
it will use the Django application port (let's say 8000) but if your mapping to the container
uses another port you have to define `SOCIAL_AUTH_SAML_FER_IDP_FAKER_DOCKER_PORT` setting
to provide the proper port.

E.g.:
 - Without override: metadata will be for `http://testserver:8000/saml/idp/sso/`
 - With `SOCIAL_AUTH_SAML_FER_IDP_FAKER_DOCKER_PORT=11000`,
   metadata will be for `http://testserver:11000/saml/idp/sso/`.


## Contributing

This project is intended to be community-driven, so please, do not hesitate to get in touch if you
have any question related to our implementation or design decisions.

We try to raise our code quality standards and expect contributors to follow the recommandations
from our [handbook](https://openfun.gitbooks.io/handbook/content).


## Versioning

This project follows [Semantic Versioning 2.0.0](http://semver.org/spec/v2.0.0.html).


## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
