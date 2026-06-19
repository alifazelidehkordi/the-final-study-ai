#!/usr/bin/env python3
"""Visible ChatGPT login probe without cookie inspection."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


EXIT_READY = 0
EXIT_NEEDS_LOGIN = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe ChatGPT login state with a visible browser.")
    parser.add_argument("--profile-dir", type=Path, required=True)
    parser.add_argument("--mindmap-project", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project = (args.mindmap_project or Path.home() / "projects/chatgpt-mindmap-to-xmind").resolve()
    scripts_dir = project / "scripts"
    if not scripts_dir.is_dir():
        print(f"ERROR: mind-map project not found: {project}", file=sys.stderr)
        return EXIT_ERROR

    sys.path.insert(0, str(scripts_dir))
    os.environ["CHATGPT_CHROME_PROFILE_DIR"] = str(args.profile_dir.resolve())

    try:
        import run_chatgpt_temporary_test as core  # type: ignore[import-not-found]
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:
        print(f"ERROR: could not import mind-map automation modules: {exc}", file=sys.stderr)
        return EXIT_ERROR

    driver = None
    try:
        driver = core.build_driver(browser="chrome")
        driver.set_window_size(1280, 900)
        driver.get("https://chatgpt.com/")
        try:
            core.wait_until_logged_in(driver, timeout=args.timeout)
            print("READY: ChatGPT prompt editor is available.")
            return EXIT_READY
        except TimeoutException:
            wait = WebDriverWait(driver, 5)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='login-button']")))
                print("NEEDS_LOGIN: ChatGPT login controls are visible.")
                return EXIT_NEEDS_LOGIN
            except TimeoutException:
                print("NEEDS_LOGIN: No usable editor or known login controls were detected.")
                return EXIT_NEEDS_LOGIN
    except Exception as exc:
        print(f"ERROR: login probe failed: {exc}", file=sys.stderr)
        return EXIT_ERROR
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())