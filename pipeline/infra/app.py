#!/usr/bin/env python3
"""CDK entry point.

    cdk synth      writes the template to cdk.out
    cdk deploy     not from this lane. HUMAN CHECKPOINT D comes first.

Settings come from context, so nothing about the account is baked into the
code::

    cdk synth -c calmframes:budgetEmail=you@example.com \\
              -c calmframes:githubRepo=owner/calm-frames
"""

from __future__ import annotations

import os
import sys

import aws_cdk as cdk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calm_frames_stack import CalmFramesStack, StackConfig  # noqa: E402


def build_app() -> cdk.App:
    app = cdk.App()
    config = StackConfig(
        budget_email=app.node.try_get_context("calmframes:budgetEmail") or "",
        github_repo=app.node.try_get_context("calmframes:githubRepo") or "",
        github_oidc_provider_arn=(
            app.node.try_get_context("calmframes:githubOidcProviderArn") or ""
        ),
        signing_public_key=app.node.try_get_context("calmframes:signingPublicKey") or "",
    )
    CalmFramesStack(
        app,
        "CalmFramesStack",
        config=config,
        description="Calm Frames ingest, delivery and catalog",
        env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
            region=os.environ.get("CDK_DEFAULT_REGION"),
        ),
    )
    return app


if __name__ == "__main__":
    build_app().synth()
