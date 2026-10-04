#!/usr/bin/env python3
"""环境检查：manim + manim-handdraw ≥0.1.1 + 本技能包依赖的新 API。"""
import sys


def main() -> int:
    ok = True
    try:
        import manim
        print(f"manim: {manim.__version__}")
    except Exception as e:
        print(f"manim MISSING: {e}")
        return 1
    try:
        import manim_handdraw as hd
        from manim_handdraw import StrokeSet
        print(f"manim_handdraw: {getattr(hd, '__version__', 'unknown')}")
        for api in ("cut_out_rectangles", "adaptive_widths"):
            has = hasattr(StrokeSet, api)
            print(f"  StrokeSet.{api}: {'OK' if has else 'MISSING'}")
            ok &= has
        import numpy, scipy, PIL  # noqa: F401
        print("numpy/scipy/PIL: OK")
    except Exception as e:
        print(f"manim_handdraw 问题: {e}")
        print("→ 修复: pip install 'manim-handdraw>=0.1.1'")
        return 1
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
