""" Selects the variables that are logged.

The logged variables are also published on the MODBUS40 interface every 2 seconds,
even after the logging has ended.

Generates a LOG.SET with sample contents:

> [NIBL;20220910;8310]
> Divisors		10	1
> Date	Time	BT1 Outdoor Temperature [°C]	Hot water comfort mode
> 40004
> 47041

The input variables are according to a schema which is generated with the sub-command generate-schema.

"""
__version__ = "1.0.0"


from argparse import ArgumentParser, FileType
import json
from logging import basicConfig, debug
from typing import Mapping, TextIO

import yaml
from jsonschema import validate
from nibe.heatpump import Model


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nibe-model",
        default="f370_f470",
        choices=[m.value for m in Model.__members__.values()],
        help="default=%(default)s",
    )
    operation = parser.add_subparsers(required=True, dest="operation")

    op_sche = operation.add_parser("generate-schema")
    op_sche.add_argument(
        "--schema",
        type=FileType("wt", encoding="utf_8"),
        default="variables-schema.json",
    )

    op_gen = operation.add_parser("generate-log-set")
    op_gen.add_argument(
        "--variables",
        type=FileType("rt", encoding="utf_8"),
        default="variables.yaml",
    )
    op_gen.add_argument(
        "--log-set",
        type=FileType("wt", encoding="iso-8859-1"),
        default="LOG.SET",
    )

    args = parser.parse_args()
    basicConfig(level="DEBUG")
    debug(args)

    if args.operation == "generate-schema":
        generate_schema(args.nibe_model, args.schema)
    elif args.operation == "generate-log-set":
        args.log_set.reconfigure(newline="\r\n")
        generate_log_set(args.nibe_model, args.variables, args.log_set)


def generate_schema(model: str, schema: TextIO) -> None:
    json.dump(get_schema(model), schema, indent=4, sort_keys=False)


def generate_log_set(model: str, variables: TextIO, log_set: TextIO) -> None:
    names = yaml.safe_load(variables)
    validate(names, get_schema(model))

    coils = Model(model).get_coil_data()
    addr = {c["name"]: k for k, c in coils.items()}

    divisors = ["Divisors", ""] + [str(coils[addr[k]]["factor"]) for k in names]
    heading = ["Date", "Time"]
    for k in names:
        c = coils[addr[k]]
        heading += [c["title"] + (f" [{c['unit']}]" if "unit" in c else "")]

    log_set.write("[NIBL;20220910;8310]\n")

    log_set.write("\t".join(divisors))
    log_set.write("\n")

    log_set.write("\t".join(heading))
    log_set.write("\n")

    log_set.write("\n".join(addr[k] for k in names))


def get_schema(model: str) -> Mapping:
    coils = Model(model).get_coil_data()

    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "array",
        "maxItems": 23,
        "uniqueItems": True,
        "additionalItems": False,
        "items": {
            "oneOf": [
            {
                "type": "string",
                "const": c["name"],
                "description": c.get("info", c["title"])

            } for c in coils.values()]
        },
    }


if __name__ == "__main__":
    main()
