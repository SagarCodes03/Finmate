"""Train the governed FinMate Default-risk signal model.

This command produces a risk signal only. It does not approve or reject loans.
"""

from __future__ import annotations

import json

from app.ml.training import train_and_evaluate


if __name__ == "__main__":
    print(json.dumps(train_and_evaluate(), indent=2))
