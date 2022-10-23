from io import StringIO
from textwrap import dedent

from log_set import *


def test_generate_log_set():
    variables = StringIO(
        dedent(
            """\
            # yaml-language-server: $schema=variables-schema.json
            - bt1-outdoor-temperature-40004
            - hot-water-comfort-mode-47041
            """
        )
    )

    log_set = StringIO()

    generate_log_set("f370_f470", variables, log_set)
    
    assert log_set.getvalue() == dedent(
        """\
        [NIBL;20220910;8310]
        Divisors		10	1
        Date	Time	BT1 Outdoor Temperature [°C]	Hot water comfort mode
        40004
        47041"""
    )
