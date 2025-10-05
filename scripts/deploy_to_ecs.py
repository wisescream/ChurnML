"""Register a new ECS task definition revision and trigger a service deployment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from string import Template
from typing import Dict, Iterable

import boto3
from botocore.exceptions import ClientError


def _parse_overrides(values: Iterable[str]) -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}'. Expected KEY=VALUE.")
        key, value = item.split("=", 1)
        overrides[key] = value
    return overrides


def render_task_definition(path: Path, overrides: Dict[str, str]) -> Dict[str, object]:
    template = Template(path.read_text(encoding="utf-8"))
    mapping = {**os.environ, **overrides}
    rendered = template.safe_substitute(mapping)
    return json.loads(rendered)


def update_container_image(definition: Dict[str, object], container_name: str, image: str) -> None:
    for container in definition.get("containerDefinitions", []):
        if container.get("name") == container_name:
            container["image"] = image
            return
    raise ValueError(f"Container '{container_name}' not found in task definition")


def register_and_deploy(
    definition: Dict[str, object],
    cluster: str,
    service: str,
    update_service: bool,
    force_new_deployment: bool,
) -> str:
    ecs = boto3.client("ecs")
    response = ecs.register_task_definition(**definition)
    task_definition_arn = response["taskDefinition"]["taskDefinitionArn"]

    if update_service:
        ecs.update_service(
            cluster=cluster,
            service=service,
            taskDefinition=task_definition_arn,
            forceNewDeployment=force_new_deployment,
        )
    return task_definition_arn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy FastAPI task definition to ECS")
    parser.add_argument(
        "--task-def",
        type=Path,
        default=Path("deployment/ecs/telecom-churn-api-task.json"),
        help="Path to the task definition JSON template",
    )
    parser.add_argument(
        "--cluster",
        default=os.getenv("ECS_CLUSTER"),
        required=False,
        help="ECS cluster name (defaults to ECS_CLUSTER env)",
    )
    parser.add_argument(
        "--service",
        default=os.getenv("ECS_API_SERVICE"),
        required=False,
        help="ECS service name (defaults to ECS_API_SERVICE env)",
    )
    parser.add_argument(
        "--container-name",
        default=os.getenv("ECS_API_CONTAINER", "telecom-churn-api"),
        help="Name of the container to update image for",
    )
    parser.add_argument(
        "--image",
        default=os.getenv("ECR_IMAGE"),
        help="Full container image URI to deploy (overrides template)",
    )
    parser.add_argument(
        "--set",
        dest="overrides",
        nargs="*",
        default=(),
        help="Extra template overrides in KEY=VALUE form",
    )
    parser.add_argument(
        "--no-update-service",
        action="store_true",
        help="Register the task definition but skip updating the service",
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Do not force a new deployment when updating the service",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.cluster:
        raise SystemExit("ECS cluster must be provided via --cluster or ECS_CLUSTER env")
    if not args.service and not args.no_update_service:
        raise SystemExit("ECS service must be provided via --service or ECS_API_SERVICE env")

    overrides = _parse_overrides(args.overrides)
    definition = render_task_definition(args.task_def, overrides)

    if args.image:
        update_container_image(definition, args.container_name, args.image)

    try:
        arn = register_and_deploy(
            definition,
            cluster=args.cluster,
            service=args.service or "",
            update_service=not args.no_update_service,
            force_new_deployment=not args.no_force,
        )
    except ClientError as exc:
        raise SystemExit(f"AWS error: {exc}") from exc

    print(f"Registered task definition: {arn}")
    if args.no_update_service:
        print("Service update skipped (--no-update-service)")
    else:
        print(f"Triggered deployment to {args.service} in cluster {args.cluster}")


if __name__ == "__main__":
    main()
