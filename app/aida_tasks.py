"""Alias-модуль: переадресует celery на настоящий код."""

from importlib import import_module

_real = import_module("aida_tasks")  # название ниже – любое уникальное

globals().update(_real.__dict__)  # экспортируем всё наружу
