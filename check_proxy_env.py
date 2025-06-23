#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

print("🔍 Verificando variables de entorno de proxy...\n")

proxy_vars = [k for k in os.environ.keys() if 'proxy' in k.lower()]

if proxy_vars:
    print("📋 Variables de proxy encontradas:")
    for var in proxy_vars:
        value = os.environ[var]
        print(f"  {var}: {value}")
else:
    print("✅ No se encontraron variables de proxy en el entorno")

print("\n🔍 Verificando variables HTTP específicas...")
http_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']

for var in http_vars:
    value = os.environ.get(var)
    if value:
        print(f"  {var}: {value}")
    else:
        print(f"  {var}: No configurada")

print("\n🔍 Verificando configuración de requests...")
try:
    import requests
    session = requests.Session()
    print(f"  Proxies en requests: {session.proxies}")
except ImportError:
    print("  requests no disponible")

print("\n🔍 Verificando configuración de urllib...")
try:
    import urllib.request
    proxy_handler = urllib.request.getproxies()
    print(f"  Proxies en urllib: {proxy_handler}")
except Exception as e:
    print(f"  Error verificando urllib: {e}")