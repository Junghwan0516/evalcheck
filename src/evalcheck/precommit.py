"""Pre-commit entry point: inspect named files without executing them."""
import sys
from .code_scan import scan_path


def main(argv=None):
    paths=sys.argv[1:] if argv is None else argv
    failed=False
    try:
        for path in paths:
            result=scan_path(path)
            for f in result['findings']:
                where=f"cell {f['cell']}, line {f['line']}" if f['cell'] is not None else f"line {f['line']}"
                print(f"{path}: {where}: {f['rule']} {f['title']}")
                print(f"  {f['suggestion']}")
                failed=True
            if result['coverage']['notes']:
                print(f"{path}: {len(result['coverage']['notes'])} scope notes; no complete-program claim")
        return 1 if failed else 0
    except (OSError,ValueError) as error:
        print(f'evalcheck: {error}',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
