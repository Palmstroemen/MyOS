#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry point for the perspective daemon.
Runs the daemon module.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from daemon.__main__ import main

if __name__ == "__main__":
    main()
