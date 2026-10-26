#!/usr/bin/env python3
"""Export Flask-Smorest generated OpenAPI specification to openapi.yaml."""

import os
import sys

# Ensure current module directory is in python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from app import create_app


def export_openapi_spec(output_path: str = "openapi.yaml"):
    app, api = create_app()
    with app.app_context():
        # api.spec is an apispec.APISpec instance
        spec_dict = api.spec.to_dict()
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(spec_dict, f, sort_keys=False, allow_unicode=True)
        print(f"Successfully exported OpenAPI specification to {output_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_yaml = os.path.join(current_dir, "openapi.yaml")
    export_openapi_spec(target_yaml)
