#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure app is importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from app.evals.eval_runner import LLMEvalRunner


def parse_args():
    parser = argparse.ArgumentParser(description="Automated LLM Socratic Coaching Evaluation Pipeline")
    parser.add_argument(
        "--mode",
        choices=["offline", "live"],
        default="offline",
        help="Evaluation mode: 'offline' runs deterministic doubles (0 cost, safe for CI); 'live' runs live LangGraph + LLM-as-a-judge.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval_report.json"),
        help="Path where full JSON report is written.",
    )
    parser.add_argument(
        "--markdown-summary",
        type=Path,
        default=None,
        help="Path where GitHub Flavored Markdown summary is written (e.g. $GITHUB_STEP_SUMMARY).",
    )
    parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=0.90,
        help="Minimum required pass rate (0.0 to 1.0) before exiting with code 1.",
    )
    parser.add_argument(
        "--min-non-directive-score",
        type=float,
        default=0.95,
        help="Minimum required non-directiveness score (0.0 to 1.0) before exiting with code 1.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="*",
        help="Optional list of specific scenario IDs to evaluate.",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    print(f"\n🚀 Starting LLM Evaluation Pipeline (Mode: {args.mode.upper()})...")

    runner = LLMEvalRunner(mode=args.mode)
    report = await runner.run(scenario_filter=args.scenarios)

    # Write JSON report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
    print(f"📄 Full JSON report written to: {args.output.resolve()}")

    # Write Markdown summary
    md_content = LLMEvalRunner.format_markdown_summary(report)
    if args.markdown_summary:
        args.markdown_summary.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_summary.write_text(md_content, encoding="utf-8")
        print(f"📝 Markdown summary written to: {args.markdown_summary.resolve()}")

    # Print summary to console
    print("\n" + "=" * 60)
    print(f"📊 EVALUATION SUMMARY (Total Scenarios: {report.total_scenarios})")
    print(f"• Passed: {report.passed_scenarios}/{report.total_scenarios} ({report.pass_rate * 100:.1f}%)")
    print(f"• Avg Non-Directiveness Score: {report.avg_non_directiveness_score:.3f}")
    print(f"• Avg GROW Adherence Score:   {report.avg_grow_adherence_score:.3f}")
    print("=" * 60)

    # Assert thresholds
    passed_thresholds = (
        report.pass_rate >= args.min_pass_rate
        and report.avg_non_directiveness_score >= args.min_non_directive_score
    )

    if not passed_thresholds:
        print(f"\n❌ EVALUATION GATE FAILED:")
        if report.pass_rate < args.min_pass_rate:
            print(f"  - Pass rate {report.pass_rate:.3f} below minimum {args.min_pass_rate:.3f}")
        if report.avg_non_directiveness_score < args.min_non_directive_score:
            print(f"  - Non-directiveness {report.avg_non_directiveness_score:.3f} below minimum {args.min_non_directive_score:.3f}")
        sys.exit(1)

    print("\n✅ EVALUATION GATE PASSED! Quality thresholds satisfied.\n")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

