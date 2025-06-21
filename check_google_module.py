#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

print("Python paths:")
for path in sys.path:
    print(f"  {path}")

print("\nBuscando módulos google:")
for path in sys.path:
    if os.path.isdir(path):
        google_path = os.path.join(path, 'google')
        if os.path.exists(google_path):
            print(f"  Encontrado google en: {google_path}")
            if os.path.isdir(google_path):
                contents = os.listdir(google_path)
                print(f"    Contenido: {contents}")
                if 'generativeai' in contents:
                    print(f"    ✅ generativeai encontrado!")
                else:
                    print(f"    ❌ generativeai NO encontrado")

print("\nIntentando importar google:")
try:
    import google
    print(f"✅ google importado desde: {google.__file__}")
    print(f"Contenido del módulo google: {dir(google)}")
except ImportError as e:
    print(f"❌ Error importando google: {e}")

print("\nIntentando importar google.generativeai:")
try:
    import google.generativeai
    print(f"✅ google.generativeai importado correctamente")
except ImportError as e:
    print(f"❌ Error importando google.generativeai: {e}")