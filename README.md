# social-edu-federation: An SAML authentication backend for python-social-auth dedicated to education federation (RENATER) 

[![CircleCI](https://circleci.com/gh/openfun/social-edu-federation/tree/main.svg?style=svg)](https://circleci.com/gh/openfun/social-edu-federation/tree/main)

## Overview

This library provides an authentication backend which can be used with
[Python Social Auth](https://github.com/python-social-auth/social-core)
and optionally 
[Python Social Auth - Django](https://github.com/python-social-auth/social-app-django)
to connect your application to an education SAML federation.

For now, it is only limited to the 
[RENATER](https://services.renater.fr/federation/en/documentation/generale/metadata/index)'s
"Féderation Éducation-Recherche" (FER) federation.


## Architecture

`social-edu-federation` is divided in two parts:
- The SAML backend and metadata parser, customized for the FER federation, 
  usable with Python Social Auth.
- The Django integration which provides: base views to provide metadata, list available 
  Identity Providers and testing material for local development.


## Setup

```shell
$ pip install social-edu-federation
```

If you also want the Django integration components you need to explicitly add the extra `django`:

```shell
$ pip install social-edu-federation[django]
```
